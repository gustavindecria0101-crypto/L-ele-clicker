from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class Achievement(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    description: str
    requirement: int
    type: str  # clicks, points, upgrades, prestige
    unlocked: bool = False


class Upgrade(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    type: str  # click, persecond, autoclick
    base_cost: int
    cost_multiplier: float
    increment: float
    level: int = 0
    description: str


class GameState(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    points: float = 0
    total_clicks: int = 0
    points_per_click: float = 1
    points_per_second: float = 0
    autoclick_active: bool = False
    autoclick_speed: float = 0
    prestige_level: int = 0
    prestige_multiplier: float = 1
    total_points_earned: float = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GameStateResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    game_state: GameState
    upgrades: List[Upgrade]
    achievements: List[Achievement]


class ClickRequest(BaseModel):
    clicks: int = 1


class UpgradeRequest(BaseModel):
    upgrade_id: str


# Initialize default upgrades and achievements
DEFAULT_UPGRADES = [
    {"id": "click1", "name": "Caneta Extra", "type": "click", "base_cost": 10, "cost_multiplier": 1.15, "increment": 1, "level": 0, "description": "+1 ponto por clique"},
    {"id": "click2", "name": "Pacote de Canetas", "type": "click", "base_cost": 100, "cost_multiplier": 1.2, "increment": 5, "level": 0, "description": "+5 pontos por clique"},
    {"id": "click3", "name": "Caixa de Canetas", "type": "click", "base_cost": 1000, "cost_multiplier": 1.25, "increment": 25, "level": 0, "description": "+25 pontos por clique"},
    {"id": "click4", "name": "Fábrica de Canetas", "type": "click", "base_cost": 10000, "cost_multiplier": 1.3, "increment": 100, "level": 0, "description": "+100 pontos por clique"},
    
    {"id": "ps1", "name": "Ajudante Automático", "type": "persecond", "base_cost": 50, "cost_multiplier": 1.15, "increment": 0.5, "level": 0, "description": "+0.5 pontos por segundo"},
    {"id": "ps2", "name": "Máquina de Canetas", "type": "persecond", "base_cost": 500, "cost_multiplier": 1.2, "increment": 5, "level": 0, "description": "+5 pontos por segundo"},
    {"id": "ps3", "name": "Robô Produtor", "type": "persecond", "base_cost": 5000, "cost_multiplier": 1.25, "increment": 50, "level": 0, "description": "+50 pontos por segundo"},
    {"id": "ps4", "name": "Super Fábrica", "type": "persecond", "base_cost": 50000, "cost_multiplier": 1.3, "increment": 500, "level": 0, "description": "+500 pontos por segundo"},
    
    {"id": "auto1", "name": "Auto-Clicker Básico", "type": "autoclick", "base_cost": 1000, "cost_multiplier": 2, "increment": 1, "level": 0, "description": "1 clique automático por segundo"},
    {"id": "auto2", "name": "Auto-Clicker Rápido", "type": "autoclick", "base_cost": 10000, "cost_multiplier": 2.5, "increment": 3, "level": 0, "description": "+3 cliques automáticos por segundo"},
]

DEFAULT_ACHIEVEMENTS = [
    {"id": "ach1", "name": "Primeiro Lá Ele", "description": "Dê seu primeiro clique", "requirement": 1, "type": "clicks", "unlocked": False},
    {"id": "ach2", "name": "Começando a Jornada", "description": "Clique 10 vezes", "requirement": 10, "type": "clicks", "unlocked": False},
    {"id": "ach3", "name": "Caneta Azul Aprendiz", "description": "Clique 100 vezes", "requirement": 100, "type": "clicks", "unlocked": False},
    {"id": "ach4", "name": "Fã do Manoel", "description": "Clique 1.000 vezes", "requirement": 1000, "type": "clicks", "unlocked": False},
    {"id": "ach5", "name": "Lá Ele Points", "description": "Acumule 10.000 pontos", "requirement": 10000, "type": "points", "unlocked": False},
    {"id": "ach6", "name": "Colecionador de Canetas", "description": "Compre 10 upgrades", "requirement": 10, "type": "upgrades", "unlocked": False},
    {"id": "ach7", "name": "Upgrade Master", "description": "Compre 50 upgrades", "requirement": 50, "type": "upgrades", "unlocked": False},
    {"id": "ach8", "name": "Clicker Automático", "description": "Ative o auto-clicker", "requirement": 1, "type": "autoclick", "unlocked": False},
    {"id": "ach9", "name": "Multiplicador", "description": "Alcance 10 pontos por clique", "requirement": 10, "type": "per_click", "unlocked": False},
    {"id": "ach10", "name": "Produtor de Canetas", "description": "Acumule 100.000 pontos totais", "requirement": 100000, "type": "total_points", "unlocked": False},
    {"id": "ach11", "name": "Fábrica de Canetas", "description": "Acumule 1.000.000 pontos totais", "requirement": 1000000, "type": "total_points", "unlocked": False},
    {"id": "ach12", "name": "Império de Canetas", "description": "Acumule 10.000.000 pontos totais", "requirement": 10000000, "type": "total_points", "unlocked": False},
    {"id": "ach13", "name": "Speed Clicker", "description": "Clique 5.000 vezes", "requirement": 5000, "type": "clicks", "unlocked": False},
    {"id": "ach14", "name": "Maratonista", "description": "Clique 10.000 vezes", "requirement": 10000, "type": "clicks", "unlocked": False},
    {"id": "ach15", "name": "Lendário", "description": "Clique 100.000 vezes", "requirement": 100000, "type": "clicks", "unlocked": False},
    {"id": "ach16", "name": "Caneta de Ouro", "description": "Acumule 50.000.000 pontos totais", "requirement": 50000000, "type": "total_points", "unlocked": False},
    {"id": "ach17", "name": "Ascensão", "description": "Faça seu primeiro prestígio", "requirement": 1, "type": "prestige", "unlocked": False},
    {"id": "ach18", "name": "Mestre do Prestígio", "description": "Alcance nível 5 de prestígio", "requirement": 5, "type": "prestige", "unlocked": False},
    {"id": "ach19", "name": "Transcendência", "description": "Alcance nível 10 de prestígio", "requirement": 10, "type": "prestige", "unlocked": False},
    {"id": "ach20", "name": "O Verdadeiro Manoel Gomes", "description": "Alcance nível 20 de prestígio", "requirement": 20, "type": "prestige", "unlocked": False},
]


# Helper functions
def calculate_upgrade_cost(upgrade: Upgrade) -> int:
    return int(upgrade.base_cost * (upgrade.cost_multiplier ** upgrade.level))


def check_achievements(game_state: GameState, upgrades: List[Upgrade], achievements: List[Achievement]) -> List[Achievement]:
    total_upgrades_bought = sum(u.level for u in upgrades)
    
    for achievement in achievements:
        if achievement.unlocked:
            continue
            
        if achievement.type == "clicks" and game_state.total_clicks >= achievement.requirement:
            achievement.unlocked = True
        elif achievement.type == "points" and game_state.points >= achievement.requirement:
            achievement.unlocked = True
        elif achievement.type == "total_points" and game_state.total_points_earned >= achievement.requirement:
            achievement.unlocked = True
        elif achievement.type == "upgrades" and total_upgrades_bought >= achievement.requirement:
            achievement.unlocked = True
        elif achievement.type == "autoclick" and game_state.autoclick_active:
            achievement.unlocked = True
        elif achievement.type == "per_click" and game_state.points_per_click >= achievement.requirement:
            achievement.unlocked = True
        elif achievement.type == "prestige" and game_state.prestige_level >= achievement.requirement:
            achievement.unlocked = True
    
    return achievements


# Routes
@api_router.get("/")
async def root():
    return {"message": "Manoel Gomes Clicker Game API"}


@api_router.post("/game/start", response_model=GameStateResponse)
async def start_game():
    game_state = GameState()
    upgrades = [Upgrade(**u) for u in DEFAULT_UPGRADES]
    achievements = [Achievement(**a) for a in DEFAULT_ACHIEVEMENTS]
    
    game_doc = game_state.model_dump()
    game_doc['created_at'] = game_doc['created_at'].isoformat()
    game_doc['last_updated'] = game_doc['last_updated'].isoformat()
    
    await db.game_states.insert_one(game_doc)
    
    for upgrade in upgrades:
        upgrade_doc = upgrade.model_dump()
        upgrade_doc['game_id'] = game_state.id
        await db.upgrades.insert_one(upgrade_doc)
    
    for achievement in achievements:
        achievement_doc = achievement.model_dump()
        achievement_doc['game_id'] = game_state.id
        await db.achievements.insert_one(achievement_doc)
    
    return GameStateResponse(game_state=game_state, upgrades=upgrades, achievements=achievements)


@api_router.get("/game/{game_id}", response_model=GameStateResponse)
async def get_game(game_id: str):
    game_doc = await db.game_states.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if isinstance(game_doc['created_at'], str):
        game_doc['created_at'] = datetime.fromisoformat(game_doc['created_at'])
    if isinstance(game_doc['last_updated'], str):
        game_doc['last_updated'] = datetime.fromisoformat(game_doc['last_updated'])
    
    game_state = GameState(**game_doc)
    
    upgrades_docs = await db.upgrades.find({"game_id": game_id}, {"_id": 0}).to_list(100)
    upgrades = [Upgrade(**u) for u in upgrades_docs]
    
    achievements_docs = await db.achievements.find({"game_id": game_id}, {"_id": 0}).to_list(100)
    achievements = [Achievement(**a) for a in achievements_docs]
    
    return GameStateResponse(game_state=game_state, upgrades=upgrades, achievements=achievements)


@api_router.post("/game/{game_id}/click", response_model=GameStateResponse)
async def click(game_id: str, request: ClickRequest):
    game_doc = await db.game_states.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if isinstance(game_doc['created_at'], str):
        game_doc['created_at'] = datetime.fromisoformat(game_doc['created_at'])
    if isinstance(game_doc['last_updated'], str):
        game_doc['last_updated'] = datetime.fromisoformat(game_doc['last_updated'])
    
    game_state = GameState(**game_doc)
    
    points_earned = game_state.points_per_click * game_state.prestige_multiplier * request.clicks
    game_state.points += points_earned
    game_state.total_points_earned += points_earned
    game_state.total_clicks += request.clicks
    game_state.last_updated = datetime.now(timezone.utc)
    
    update_doc = game_state.model_dump()
    update_doc['created_at'] = update_doc['created_at'].isoformat()
    update_doc['last_updated'] = update_doc['last_updated'].isoformat()
    await db.game_states.update_one({"id": game_id}, {"$set": update_doc})
    
    upgrades_docs = await db.upgrades.find({"game_id": game_id}, {"_id": 0}).to_list(100)
    upgrades = [Upgrade(**u) for u in upgrades_docs]
    
    achievements_docs = await db.achievements.find({"game_id": game_id}, {"_id": 0}).to_list(100)
    achievements = [Achievement(**a) for a in achievements_docs]
    
    achievements = check_achievements(game_state, upgrades, achievements)
    
    for achievement in achievements:
        await db.achievements.update_one(
            {"game_id": game_id, "id": achievement.id},
            {"$set": {"unlocked": achievement.unlocked}}
        )
    
    return GameStateResponse(game_state=game_state, upgrades=upgrades, achievements=achievements)


@api_router.post("/game/{game_id}/upgrade", response_model=GameStateResponse)
async def buy_upgrade(game_id: str, request: UpgradeRequest):
    game_doc = await db.game_states.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if isinstance(game_doc['created_at'], str):
        game_doc['created_at'] = datetime.fromisoformat(game_doc['created_at'])
    if isinstance(game_doc['last_updated'], str):
        game_doc['last_updated'] = datetime.fromisoformat(game_doc['last_updated'])
    
    game_state = GameState(**game_doc)
    
    upgrade_doc = await db.upgrades.find_one({"game_id": game_id, "id": request.upgrade_id}, {"_id": 0})
    if not upgrade_doc:
        raise HTTPException(status_code=404, detail="Upgrade not found")
    
    upgrade = Upgrade(**upgrade_doc)
    cost = calculate_upgrade_cost(upgrade)
    
    if game_state.points < cost:
        raise HTTPException(status_code=400, detail="Not enough points")
    
    game_state.points -= cost
    upgrade.level += 1
    
    if upgrade.type == "click":
        game_state.points_per_click += upgrade.increment
    elif upgrade.type == "persecond":
        game_state.points_per_second += upgrade.increment
    elif upgrade.type == "autoclick":
        game_state.autoclick_active = True
        game_state.autoclick_speed += upgrade.increment
    
    game_state.last_updated = datetime.now(timezone.utc)
    
    update_doc = game_state.model_dump()
    update_doc['created_at'] = update_doc['created_at'].isoformat()
    update_doc['last_updated'] = update_doc['last_updated'].isoformat()
    await db.game_states.update_one({"id": game_id}, {"$set": update_doc})
    
    await db.upgrades.update_one(
        {"game_id": game_id, "id": request.upgrade_id},
        {"$set": {"level": upgrade.level}}
    )
    
    upgrades_docs = await db.upgrades.find({"game_id": game_id}, {"_id": 0}).to_list(100)
    upgrades = [Upgrade(**u) for u in upgrades_docs]
    
    achievements_docs = await db.achievements.find({"game_id": game_id}, {"_id": 0}).to_list(100)
    achievements = [Achievement(**a) for a in achievements_docs]
    
    achievements = check_achievements(game_state, upgrades, achievements)
    
    for achievement in achievements:
        await db.achievements.update_one(
            {"game_id": game_id, "id": achievement.id},
            {"$set": {"unlocked": achievement.unlocked}}
        )
    
    return GameStateResponse(game_state=game_state, upgrades=upgrades, achievements=achievements)


@api_router.post("/game/{game_id}/prestige", response_model=GameStateResponse)
async def prestige(game_id: str):
    game_doc = await db.game_states.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if isinstance(game_doc['created_at'], str):
        game_doc['created_at'] = datetime.fromisoformat(game_doc['created_at'])
    if isinstance(game_doc['last_updated'], str):
        game_doc['last_updated'] = datetime.fromisoformat(game_doc['last_updated'])
    
    game_state = GameState(**game_doc)
    
    if game_state.total_points_earned < 1000000:
        raise HTTPException(status_code=400, detail="Precisa de 1.000.000 de pontos totais para fazer prestígio")
    
    game_state.prestige_level += 1
    game_state.prestige_multiplier = 1 + (game_state.prestige_level * 0.5)
    game_state.points = 0
    game_state.points_per_click = 1
    game_state.points_per_second = 0
    game_state.autoclick_active = False
    game_state.autoclick_speed = 0
    game_state.last_updated = datetime.now(timezone.utc)
    
    update_doc = game_state.model_dump()
    update_doc['created_at'] = update_doc['created_at'].isoformat()
    update_doc['last_updated'] = update_doc['last_updated'].isoformat()
    await db.game_states.update_one({"id": game_id}, {"$set": update_doc})
    
    await db.upgrades.update_many(
        {"game_id": game_id},
        {"$set": {"level": 0}}
    )
    
    upgrades_docs = await db.upgrades.find({"game_id": game_id}, {"_id": 0}).to_list(100)
    upgrades = [Upgrade(**u) for u in upgrades_docs]
    
    achievements_docs = await db.achievements.find({"game_id": game_id}, {"_id": 0}).to_list(100)
    achievements = [Achievement(**a) for a in achievements_docs]
    
    achievements = check_achievements(game_state, upgrades, achievements)
    
    for achievement in achievements:
        await db.achievements.update_one(
            {"game_id": game_id, "id": achievement.id},
            {"$set": {"unlocked": achievement.unlocked}}
        )
    
    return GameStateResponse(game_state=game_state, upgrades=upgrades, achievements=achievements)


@api_router.post("/game/{game_id}/passive", response_model=GameStateResponse)
async def update_passive(game_id: str):
    game_doc = await db.game_states.find_one({"id": game_id}, {"_id": 0})
    if not game_doc:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if isinstance(game_doc['created_at'], str):
        game_doc['created_at'] = datetime.fromisoformat(game_doc['created_at'])
    if isinstance(game_doc['last_updated'], str):
        game_doc['last_updated'] = datetime.fromisoformat(game_doc['last_updated'])
    
    game_state = GameState(**game_doc)
    
    now = datetime.now(timezone.utc)
    time_diff = (now - game_state.last_updated).total_seconds()
    
    if time_diff > 0:
        passive_points = game_state.points_per_second * game_state.prestige_multiplier * time_diff
        autoclick_points = 0
        if game_state.autoclick_active:
            autoclick_clicks = game_state.autoclick_speed * time_diff
            autoclick_points = autoclick_clicks * game_state.points_per_click * game_state.prestige_multiplier
        
        total_passive = passive_points + autoclick_points
        game_state.points += total_passive
        game_state.total_points_earned += total_passive
        game_state.last_updated = now
        
        update_doc = game_state.model_dump()
        update_doc['created_at'] = update_doc['created_at'].isoformat()
        update_doc['last_updated'] = update_doc['last_updated'].isoformat()
        await db.game_states.update_one({"id": game_id}, {"$set": update_doc})
    
    upgrades_docs = await db.upgrades.find({"game_id": game_id}, {"_id": 0}).to_list(100)
    upgrades = [Upgrade(**u) for u in upgrades_docs]
    
    achievements_docs = await db.achievements.find({"game_id": game_id}, {"_id": 0}).to_list(100)
    achievements = [Achievement(**a) for a in achievements_docs]
    
    return GameStateResponse(game_state=game_state, upgrades=upgrades, achievements=achievements)


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
