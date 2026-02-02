import { useState, useEffect, useCallback, useRef } from "react";
import "@/App.css";
import axios from "axios";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Trophy, Zap, TrendingUp, Star, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { Toaster } from "@/components/ui/sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Imagem do Manoel Gomes
const MANOEL_IMAGE = "https://customer-assets.emergentagent.com/job_d645f490-3f44-4758-b4e3-5932150da6f0/artifacts/mwe2mbwl_321606308_3496090677301832_8430175518580223779_n.webp";

function App() {
  const [gameState, setGameState] = useState(null);
  const [upgrades, setUpgrades] = useState([]);
  const [achievements, setAchievements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [clickAnimation, setClickAnimation] = useState(false);
  const [floatingNumbers, setFloatingNumbers] = useState([]);
  const [selectedTab, setSelectedTab] = useState("game");
  const audioRef = useRef(null);

  // Som "Lá ele" do Manoel Gomes (arquivo local)
  const LAELE_SOUND = "/laele.mp3";

  // Inicializar áudio
  useEffect(() => {
    audioRef.current = new Audio(LAELE_SOUND);
    audioRef.current.volume = 0.7;
    audioRef.current.preload = "auto";
  }, []);

  // Tocar som do Manoel Gomes (para e reinicia se já estiver tocando)
  const playLaEleSound = useCallback(() => {
    if (!audioRef.current) return;
    
    // Parar o áudio atual e resetar para o início
    audioRef.current.pause();
    audioRef.current.currentTime = 0;
    
    // Tocar o som
    audioRef.current.play().catch(error => {
      console.log("Erro ao tocar áudio:", error);
    });
  }, []);

  const startGame = async () => {
    try {
      const response = await axios.post(`${API}/game/start`);
      const data = response.data;
      setGameState(data.game_state);
      setUpgrades(data.upgrades);
      setAchievements(data.achievements);
      localStorage.setItem('gameId', data.game_state.id);
      setLoading(false);
    } catch (error) {
      console.error("Erro ao iniciar jogo:", error);
      toast.error("Erro ao iniciar o jogo");
    }
  };

  const loadGame = async (gameId) => {
    try {
      const response = await axios.get(`${API}/game/${gameId}`);
      const data = response.data;
      setGameState(data.game_state);
      setUpgrades(data.upgrades);
      setAchievements(data.achievements);
      setLoading(false);
    } catch (error) {
      console.error("Erro ao carregar jogo:", error);
      await startGame();
    }
  };

  const updatePassive = async () => {
    if (!gameState) return;
    try {
      const response = await axios.post(`${API}/game/${gameState.id}/passive`);
      const data = response.data;
      setGameState(data.game_state);
      setUpgrades(data.upgrades);
      setAchievements(data.achievements);
    } catch (error) {
      console.error("Erro ao atualizar passivo:", error);
    }
  };

  useEffect(() => {
    const savedGameId = localStorage.getItem('gameId');
    if (savedGameId) {
      loadGame(savedGameId);
    } else {
      startGame();
    }
  }, []);

  useEffect(() => {
    if (!gameState) return;
    
    const interval = setInterval(() => {
      updatePassive();
    }, 1000);

    return () => clearInterval(interval);
  }, [gameState]);

  const handleClick = async () => {
    if (!gameState) return;

    // Tocar som "Lá ele" do Manoel Gomes (para e reinicia se já estiver tocando)
    playLaEleSound();
    
    setClickAnimation(true);
    setTimeout(() => setClickAnimation(false), 100);

    const pointsEarned = gameState.points_per_click * gameState.prestige_multiplier;
    
    // Adicionar número flutuante
    const id = Date.now();
    setFloatingNumbers(prev => [...prev, { id, value: pointsEarned }]);
    setTimeout(() => {
      setFloatingNumbers(prev => prev.filter(n => n.id !== id));
    }, 1000);

    try {
      const response = await axios.post(`${API}/game/${gameState.id}/click`, { clicks: 1 });
      const data = response.data;
      setGameState(data.game_state);
      setAchievements(data.achievements);
      
      // Verificar novas conquistas
      const newAchievements = data.achievements.filter((a, i) => 
        a.unlocked && !achievements[i]?.unlocked
      );
      newAchievements.forEach(ach => {
        toast.success(`🏆 Conquista desbloqueada: ${ach.name}!`);
      });
    } catch (error) {
      console.error("Erro ao clicar:", error);
    }
  };

  const buyUpgrade = async (upgradeId) => {
    if (!gameState) return;

    try {
      const response = await axios.post(`${API}/game/${gameState.id}/upgrade`, { upgrade_id: upgradeId });
      const data = response.data;
      setGameState(data.game_state);
      setUpgrades(data.upgrades);
      setAchievements(data.achievements);
      toast.success("Upgrade comprado!");
    } catch (error) {
      console.error("Erro ao comprar upgrade:", error);
      if (error.response?.status === 400) {
        toast.error("Pontos insuficientes!");
      }
    }
  };

  const doPrestige = async () => {
    if (!gameState) return;

    if (gameState.total_points_earned < 1000000) {
      toast.error("Você precisa de 1.000.000 de pontos totais para fazer prestígio!");
      return;
    }

    try {
      const response = await axios.post(`${API}/game/${gameState.id}/prestige`);
      const data = response.data;
      setGameState(data.game_state);
      setUpgrades(data.upgrades);
      setAchievements(data.achievements);
      toast.success(`🌟 Prestígio ${data.game_state.prestige_level}! Multiplicador: ${data.game_state.prestige_multiplier.toFixed(1)}x`);
    } catch (error) {
      console.error("Erro ao fazer prestígio:", error);
      toast.error(error.response?.data?.detail || "Erro ao fazer prestígio");
    }
  };

  const calculateUpgradeCost = (upgrade) => {
    return Math.floor(upgrade.base_cost * Math.pow(upgrade.cost_multiplier, upgrade.level));
  };

  const formatNumber = (num) => {
    if (num >= 1000000000) return (num / 1000000000).toFixed(2) + "B";
    if (num >= 1000000) return (num / 1000000).toFixed(2) + "M";
    if (num >= 1000) return (num / 1000).toFixed(2) + "K";
    return num.toFixed(0);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-400 via-blue-500 to-blue-600">
        <div className="text-white text-2xl font-bold">Carregando...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-400 via-blue-500 to-blue-600 relative overflow-hidden">
      <Toaster position="top-right" />
      
      {/* Canetas azuis flutuantes no fundo */}
      <div className="absolute inset-0 pointer-events-none">
        {[...Array(15)].map((_, i) => (
          <div
            key={i}
            className="pen-float absolute"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 5}s`,
              animationDuration: `${5 + Math.random() * 5}s`
            }}
          >
            ✒️
          </div>
        ))}
      </div>

      <div className="container mx-auto px-4 py-8 relative z-10">
        <header className="text-center mb-8">
          <h1 className="text-5xl md:text-6xl font-bold text-white mb-2" style={{ fontFamily: 'Bebas Neue, Impact, sans-serif' }}>
            MANOEL GOMES CLICKER
          </h1>
          <p className="text-xl text-blue-100">Caneta Azul, Azul Caneta! 🖊️</p>
        </header>

        <Tabs value={selectedTab} onValueChange={setSelectedTab} className="w-full">
          <TabsList className="grid w-full max-w-md mx-auto grid-cols-3 mb-6 bg-blue-600/50 backdrop-blur-sm border-2 border-blue-300">
            <TabsTrigger value="game" data-testid="game-tab" className="data-[state=active]:bg-white data-[state=active]:text-blue-600">
              <Zap className="w-4 h-4 mr-2" />
              Jogo
            </TabsTrigger>
            <TabsTrigger value="upgrades" data-testid="upgrades-tab" className="data-[state=active]:bg-white data-[state=active]:text-blue-600">
              <TrendingUp className="w-4 h-4 mr-2" />
              Upgrades
            </TabsTrigger>
            <TabsTrigger value="achievements" data-testid="achievements-tab" className="data-[state=active]:bg-white data-[state=active]:text-blue-600">
              <Trophy className="w-4 h-4 mr-2" />
              Conquistas
            </TabsTrigger>
          </TabsList>

          <TabsContent value="game" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Painel de Estatísticas */}
              <Card className="lg:col-span-1 bg-white/95 backdrop-blur-sm border-4 border-blue-300 shadow-2xl" data-testid="stats-panel">
                <CardHeader>
                  <CardTitle className="text-2xl text-blue-700">📊 Estatísticas</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium text-gray-600">Lá Ele Points:</span>
                      <span className="text-2xl font-bold text-blue-600" data-testid="current-points">{formatNumber(gameState.points)}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Por clique:</span>
                      <span className="text-lg font-semibold text-green-600" data-testid="points-per-click">
                        +{formatNumber(gameState.points_per_click * gameState.prestige_multiplier)}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Por segundo:</span>
                      <span className="text-lg font-semibold text-purple-600" data-testid="points-per-second">
                        +{formatNumber(gameState.points_per_second * gameState.prestige_multiplier)}
                      </span>
                    </div>
                  </div>

                  <Separator />

                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Total de Cliques:</span>
                      <span className="font-semibold text-blue-700" data-testid="total-clicks">{formatNumber(gameState.total_clicks)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Pontos Totais:</span>
                      <span className="font-semibold text-blue-700" data-testid="total-points">{formatNumber(gameState.total_points_earned)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Auto-Clicker:</span>
                      <Badge variant={gameState.autoclick_active ? "default" : "secondary"} data-testid="autoclick-status">
                        {gameState.autoclick_active ? `${gameState.autoclick_speed}/s` : "Inativo"}
                      </Badge>
                    </div>
                  </div>

                  <Separator />

                  <div className="bg-gradient-to-r from-yellow-400 to-orange-400 p-4 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-bold text-gray-800">Nível de Prestígio:</span>
                      <Badge className="bg-yellow-600 text-white" data-testid="prestige-level">
                        <Star className="w-3 h-3 mr-1" />
                        {gameState.prestige_level}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-bold text-gray-800">Multiplicador:</span>
                      <span className="text-xl font-bold text-gray-800" data-testid="prestige-multiplier">
                        {gameState.prestige_multiplier.toFixed(1)}x
                      </span>
                    </div>
                  </div>

                  <Button 
                    onClick={doPrestige}
                    disabled={gameState.total_points_earned < 1000000}
                    className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-bold py-6 text-lg"
                    data-testid="prestige-button"
                  >
                    <Sparkles className="w-5 h-5 mr-2" />
                    Fazer Prestígio
                  </Button>
                  {gameState.total_points_earned < 1000000 && (
                    <p className="text-xs text-center text-gray-600">
                      Precisa de {formatNumber(1000000 - gameState.total_points_earned)} pontos totais
                    </p>
                  )}
                </CardContent>
              </Card>

              {/* Área de Clique */}
              <Card className="lg:col-span-2 bg-white/95 backdrop-blur-sm border-4 border-blue-300 shadow-2xl" data-testid="click-area">
                <CardHeader>
                  <CardTitle className="text-3xl text-center text-blue-700">
                    Clique no Manoel! 🎤
                  </CardTitle>
                </CardHeader>
                <CardContent className="flex flex-col items-center justify-center p-8">
                  <div className="relative">
                    <button
                      onClick={handleClick}
                      data-testid="manoel-click-button"
                      className={`manoel-button ${clickAnimation ? 'clicked' : ''} relative transform transition-all hover:scale-105 active:scale-95`}
                      style={{
                        width: '300px',
                        height: '300px',
                        borderRadius: '50%',
                        border: '8px solid #1E40AF',
                        overflow: 'hidden',
                        background: `url(${MANOEL_IMAGE}) center/cover`,
                        cursor: 'pointer',
                        boxShadow: '0 10px 40px rgba(30, 64, 175, 0.5)'
                      }}
                    >
                      <div className="absolute inset-0 bg-blue-400 opacity-0 hover:opacity-20 transition-opacity" />
                    </button>

                    {/* Números flutuantes */}
                    {floatingNumbers.map(({ id, value }) => (
                      <div
                        key={id}
                        className="floating-number absolute left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2 text-4xl font-bold text-yellow-400 pointer-events-none"
                        style={{
                          textShadow: '2px 2px 4px rgba(0,0,0,0.8)',
                          animation: 'float-up 1s ease-out forwards'
                        }}
                      >
                        +{formatNumber(value)}
                      </div>
                    ))}
                  </div>

                  <div className="mt-8 text-center">
                    <p className="text-2xl font-bold text-blue-700 mb-2">
                      {gameState.total_clicks} cliques totais
                    </p>
                    <p className="text-lg text-gray-600">
                      Continue clicando para ganhar mais Lá Ele Points!
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="upgrades" className="space-y-4">
            <Card className="bg-white/95 backdrop-blur-sm border-4 border-blue-300" data-testid="upgrades-panel">
              <CardHeader>
                <CardTitle className="text-2xl text-blue-700">🚀 Melhorias</CardTitle>
                <CardDescription>Aumente seus pontos por clique e por segundo!</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {upgrades.map((upgrade) => {
                    const cost = calculateUpgradeCost(upgrade);
                    const canAfford = gameState.points >= cost;
                    const icon = upgrade.type === 'click' ? '👆' : upgrade.type === 'persecond' ? '⏱️' : '🤖';
                    
                    return (
                      <Card 
                        key={upgrade.id} 
                        className={`border-2 ${canAfford ? 'border-green-400 bg-green-50' : 'border-gray-300 bg-gray-50'}`}
                        data-testid={`upgrade-${upgrade.id}`}
                      >
                        <CardHeader>
                          <CardTitle className="text-lg flex items-center justify-between">
                            <span>{icon} {upgrade.name}</span>
                            <Badge variant="outline" data-testid={`upgrade-level-${upgrade.id}`}>Nv. {upgrade.level}</Badge>
                          </CardTitle>
                          <CardDescription>{upgrade.description}</CardDescription>
                        </CardHeader>
                        <CardContent>
                          <Button
                            onClick={() => buyUpgrade(upgrade.id)}
                            disabled={!canAfford}
                            className="w-full"
                            variant={canAfford ? "default" : "secondary"}
                            data-testid={`buy-upgrade-${upgrade.id}`}
                          >
                            Comprar por {formatNumber(cost)} pontos
                          </Button>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="achievements" className="space-y-4">
            <Card className="bg-white/95 backdrop-blur-sm border-4 border-blue-300" data-testid="achievements-panel">
              <CardHeader>
                <CardTitle className="text-2xl text-blue-700">🏆 Conquistas</CardTitle>
                <CardDescription>
                  {achievements.filter(a => a.unlocked).length} / {achievements.length} desbloqueadas
                </CardDescription>
                <Progress 
                  value={(achievements.filter(a => a.unlocked).length / achievements.length) * 100} 
                  className="mt-2"
                  data-testid="achievements-progress"
                />
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {achievements.map((achievement) => (
                    <Card 
                      key={achievement.id}
                      className={`border-2 ${achievement.unlocked ? 'border-yellow-400 bg-yellow-50' : 'border-gray-300 bg-gray-100'}`}
                      data-testid={`achievement-${achievement.id}`}
                    >
                      <CardHeader>
                        <CardTitle className="text-base flex items-center gap-2">
                          {achievement.unlocked ? '🏆' : '🔒'}
                          <span className={achievement.unlocked ? 'text-yellow-700' : 'text-gray-500'}>
                            {achievement.name}
                          </span>
                        </CardTitle>
                        <CardDescription className={achievement.unlocked ? 'text-gray-700' : 'text-gray-400'}>
                          {achievement.description}
                        </CardDescription>
                      </CardHeader>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

export default App;
