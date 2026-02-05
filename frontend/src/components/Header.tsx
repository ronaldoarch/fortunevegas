import { useEffect, useState } from 'react';
import { Gift, Menu as MenuIcon, Wallet, User } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import NotificationsDropdown from './NotificationsDropdown';

// Backend FastAPI - usa variável de ambiente ou fallback para localhost
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface HeaderProps {
  onMenuClick?: () => void;
  onLoginClick?: () => void;
  onRegisterClick?: () => void;
}

export default function Header({ onMenuClick, onLoginClick, onRegisterClick }: HeaderProps) {
  const navigate = useNavigate();
  const { user, token } = useAuth();
  const [logoUrl, setLogoUrl] = useState<string | null>(null);

  useEffect(() => {
    const fetchLogo = async () => {
      try {
        const res = await fetch(`${API_URL}/api/public/media/logo`);
        if (res.ok) {
          const data = await res.json();
          if (data.url) {
            // Se a URL já começar com /api, usa direto; senão constrói com API_URL
            const url = data.url.startsWith('/api') 
              ? `${API_URL}${data.url}`
              : `${API_URL}/api/public/media${data.url}`;
            setLogoUrl(url);
          } else {
            setLogoUrl(null);
          }
        }
      } catch (err) {
        console.error('Erro ao buscar logo:', err);
      }
    };
    fetchLogo();
    
    // Polling para atualizar logo (a cada 5 segundos)
    const interval = setInterval(fetchLogo, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="w-full bg-[#0a4d3e] text-white sticky top-0 z-40 shadow-md">
      <div className="container mx-auto px-3 md:px-4 py-2 md:py-3">
        <div className="flex items-center justify-between">
          {/* Logo e Menu Mobile */}
          <div className="flex items-center gap-2 md:gap-3">
            {onMenuClick && (
              <button
                onClick={onMenuClick}
                className="md:hidden p-1.5 hover:bg-[#0d5d4b] rounded transition-colors"
                aria-label="Abrir menu"
              >
                <MenuIcon size={20} />
              </button>
            )}
            <a href="/" className="flex items-center gap-1 md:gap-2 hover:opacity-80 transition-opacity">
              {logoUrl ? (
                <img src={logoUrl} alt="Fortune Vegas" className="w-10 h-10 md:w-12 md:h-12 object-contain" />
              ) : (
                <>
                  <div className="text-lg md:text-2xl font-bold tracking-tight">FORTUNE</div>
                  <div className="text-base md:text-xl font-semibold hidden sm:block">VEGAS</div>
                </>
              )}
              <Gift className="text-[#d4af37] w-4 h-4 md:w-5 md:h-5" />
            </a>
          </div>
          
          {/* Navegação CASSINO - Na mesma linha */}
          <nav className="hidden md:flex items-center gap-6">
            <a 
              href="/cassino" 
              className="py-2 px-3 border-b-2 border-[#ff6b35] text-white font-medium text-sm md:text-base hover:text-[#d4af37] transition-colors"
            >
              CASSINO
            </a>
          </nav>

          {/* Botões de Ação */}
          <div className="flex items-center gap-2 md:gap-3">
            {user ? (
              <>
                {/* Saldo */}
                <button
                  onClick={() => navigate('/conta')}
                  className="hidden md:flex items-center gap-2 px-3 py-1.5 bg-[#0d5d4b] hover:bg-[#0f6d5b] rounded-md transition-colors"
                >
                  <Wallet size={18} className="text-[#d4af37]" />
                  <span className="text-sm font-semibold">
                    R$ {user.balance.toFixed(2).replace('.', ',')}
                  </span>
                </button>
                {/* Notificações */}
                <NotificationsDropdown token={token || ''} />
                {/* Perfil */}
                <button
                  onClick={() => navigate('/conta')}
                  className="p-2 hover:bg-[#0d5d4b] rounded transition-colors"
                  aria-label="Minha conta"
                >
                  <User size={20} />
                </button>
              </>
            ) : (
              <>
                <button 
                  onClick={onLoginClick}
                  className="px-2 md:px-4 py-1.5 md:py-2 text-sm md:text-base hover:text-[#d4af37] transition-colors font-medium"
                >
                  Entrar
                </button>
                <button 
                  onClick={onRegisterClick}
                  className="px-3 md:px-6 py-1.5 md:py-2 bg-[#ff6b35] rounded-md hover:bg-[#ff7b35] transition-colors font-semibold text-sm md:text-base"
                >
                  Registre-se
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
