import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { ArrowLeft, Loader2, AlertCircle, Maximize2, Minimize2, X } from 'lucide-react';

// Backend FastAPI - usa variável de ambiente ou fallback para localhost
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Game() {
  const { gameCode } = useParams<{ gameCode: string }>();
  const navigate = useNavigate();
  const { user, token, loading: authLoading } = useAuth();
  const [gameUrl, setGameUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [headerVisible, setHeaderVisible] = useState(true);
  const gameContainerRef = useRef<HTMLDivElement>(null);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    // Aguardar o AuthContext terminar de carregar
    if (authLoading) {
      return;
    }

    if (!token || !user) {
      setError('Você precisa estar logado para jogar');
      setLoading(false);
      return;
    }

    // Verificar se o usuário tem saldo (real + bônus)
    const totalBalance = (user.balance || 0) + (user.bonus_balance || 0);
    if (totalBalance <= 0) {
      setError('Você precisa ter saldo para jogar. Faça um depósito primeiro.');
      setLoading(false);
      return;
    }

    if (!gameCode) {
      setError('Código do jogo não encontrado');
      setLoading(false);
      return;
    }

    const launchGame = async () => {
      try {
        const res = await fetch(`${API_URL}/api/public/games/${gameCode}/launch?lang=pt`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (!res.ok) {
          const data = await res.json().catch(() => ({ detail: 'Erro ao iniciar jogo' }));
          throw new Error(data.detail || 'Erro ao iniciar jogo');
        }

        const data = await res.json();
        setGameUrl(data.game_url || data.launch_url);
      } catch (err: any) {
        setError(err.message || 'Erro ao carregar jogo');
      } finally {
        setLoading(false);
      }
    };

    launchGame();

    // Cleanup: garantir que overflow seja restaurado ao sair da página
    return () => {
      document.body.style.overflow = '';
      document.documentElement.style.overflow = '';
    };
  }, [gameCode, token, user, authLoading]);

  // Detectar mudanças de fullscreen e aplicar estilos
  useEffect(() => {
    const handleFullscreenChange = () => {
      const isFullscreenNow = !!(
        document.fullscreenElement ||
        (document as any).webkitFullscreenElement ||
        (document as any).mozFullScreenElement ||
        (document as any).msFullscreenElement
      );
      setIsFullscreen(isFullscreenNow);
      
      // Aplicar/remover overflow hidden apenas quando em fullscreen
      if (isFullscreenNow) {
        document.body.style.overflow = 'hidden';
        document.documentElement.style.overflow = 'hidden';
      } else {
        document.body.style.overflow = '';
        document.documentElement.style.overflow = '';
      }
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
    document.addEventListener('mozfullscreenchange', handleFullscreenChange);
    document.addEventListener('MSFullscreenChange', handleFullscreenChange);

    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
      document.removeEventListener('webkitfullscreenchange', handleFullscreenChange);
      document.removeEventListener('mozfullscreenchange', handleFullscreenChange);
      document.removeEventListener('MSFullscreenChange', handleFullscreenChange);
      // Limpar estilos ao desmontar
      document.body.style.overflow = '';
      document.documentElement.style.overflow = '';
    };
  }, []);

  // Função para entrar em fullscreen
  const enterFullscreen = async () => {
    const container = gameContainerRef.current;
    if (!container) return;

    try {
      if (container.requestFullscreen) {
        await container.requestFullscreen();
      } else if ((container as any).webkitRequestFullscreen) {
        await (container as any).webkitRequestFullscreen();
      } else if ((container as any).mozRequestFullScreen) {
        await (container as any).mozRequestFullScreen();
      } else if ((container as any).msRequestFullscreen) {
        await (container as any).msRequestFullscreen();
      }
      setHeaderVisible(false);
      // Aplicar overflow hidden quando entrar em fullscreen
      document.body.style.overflow = 'hidden';
      document.documentElement.style.overflow = 'hidden';
    } catch (err) {
      console.error('Erro ao entrar em fullscreen:', err);
    }
  };

  // Função para sair de fullscreen
  const exitFullscreen = async () => {
    try {
      if (document.exitFullscreen) {
        await document.exitFullscreen();
      } else if ((document as any).webkitExitFullscreen) {
        await (document as any).webkitExitFullscreen();
      } else if ((document as any).mozCancelFullScreen) {
        await (document as any).mozCancelFullScreen();
      } else if ((document as any).msExitFullscreen) {
        await (document as any).msExitFullscreen();
      }
      setHeaderVisible(true);
      // Remover overflow hidden ao sair de fullscreen
      document.body.style.overflow = '';
      document.documentElement.style.overflow = '';
    } catch (err) {
      console.error('Erro ao sair de fullscreen:', err);
    }
  };

  // Detectar se é mobile
  const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0e0f] text-white flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="animate-spin h-12 w-12 text-[#d4af37] mx-auto mb-4" />
          <p className="text-lg">Carregando jogo...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#0a0e0f] text-white">
        <div className="container mx-auto px-4 py-8">
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-2 text-[#d4af37] hover:text-[#ffd700] mb-6 transition-colors"
          >
            <ArrowLeft size={20} />
            Voltar
          </button>
          <div className="bg-red-500/20 border border-red-500 rounded-lg p-6 flex items-start gap-4">
            <AlertCircle className="text-red-400 flex-shrink-0 mt-1" size={24} />
            <div>
              <h2 className="text-xl font-bold text-red-400 mb-2">Erro ao carregar jogo</h2>
              <p className="text-red-200">{error}</p>
              <button
                onClick={() => navigate('/')}
                className="mt-4 px-4 py-2 bg-[#ff6b35] hover:bg-[#ff7b35] rounded-lg transition-colors"
              >
                Voltar para Home
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div 
      ref={gameContainerRef}
      className={`bg-[#0a0e0f] text-white ${isFullscreen ? 'fixed inset-0 z-50' : 'min-h-screen'}`}
      style={isFullscreen ? { height: '100vh', width: '100vw' } : {}}
    >
      {/* Header com botão voltar - oculto em fullscreen ou mobile */}
      {headerVisible && !isFullscreen && (
        <div className="bg-[#0a4d3e] border-b border-[#0d5d4b] sticky top-0 z-40">
          <div className="container mx-auto px-4 py-3 flex items-center justify-between">
            <button
              onClick={() => navigate('/')}
              className="flex items-center gap-2 text-white hover:text-[#d4af37] transition-colors"
            >
              <ArrowLeft size={20} />
              <span className="font-medium">Voltar</span>
            </button>
            <button
              onClick={enterFullscreen}
              className="flex items-center gap-2 text-white hover:text-[#d4af37] transition-colors"
              title="Tela cheia"
            >
              <Maximize2 size={20} />
            </button>
          </div>
        </div>
      )}

      {/* Botão de sair do fullscreen - apenas quando em fullscreen */}
      {isFullscreen && (
        <div className="fixed top-0 left-0 right-0 z-50 bg-[#0a4d3e]/90 backdrop-blur-sm border-b border-[#0d5d4b]">
          <div className="container mx-auto px-4 py-2 flex items-center justify-between">
            <button
              onClick={exitFullscreen}
              className="flex items-center gap-2 text-white hover:text-[#d4af37] transition-colors"
              title="Sair da tela cheia"
            >
              <Minimize2 size={20} />
              <span className="font-medium text-sm">Sair</span>
            </button>
            <button
              onClick={() => {
                exitFullscreen();
                navigate('/');
              }}
              className="flex items-center gap-2 text-white hover:text-red-400 transition-colors"
              title="Fechar jogo"
            >
              <X size={20} />
            </button>
          </div>
        </div>
      )}

      {/* Iframe do jogo */}
      {gameUrl && (
        <div 
          className="w-full"
          style={{
            height: isFullscreen 
              ? '100vh' 
              : isMobile 
                ? 'calc(100dvh - env(safe-area-inset-top) - env(safe-area-inset-bottom))'
                : 'calc(100vh - 60px)'
          }}
        >
          <iframe
            ref={iframeRef}
            src={gameUrl}
            className="w-full h-full border-0"
            title="Jogo"
            allow="fullscreen; autoplay; payment; geolocation"
            allowFullScreen
            style={{
              height: '100%',
              width: '100%'
            }}
          />
        </div>
      )}

      {/* Botão flutuante para fullscreen no mobile - apenas quando não está em fullscreen */}
      {isMobile && !isFullscreen && headerVisible && (
        <button
          onClick={enterFullscreen}
          className="fixed bottom-20 right-4 z-50 bg-[#d4af37] hover:bg-[#ffd700] text-black p-3 rounded-full shadow-lg transition-colors"
          title="Tela cheia"
        >
          <Maximize2 size={24} />
        </button>
      )}
    </div>
  );
}
