import { useState, useEffect } from 'react';
import { X, Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const API_URL = import.meta.env.VITE_API_URL || 'https://api.fortunevegas.site';

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSwitchToRegister: () => void;
}

export default function LoginModal({ isOpen, onClose, onSwitchToRegister }: LoginModalProps) {
  const { login } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [logoUrl, setLogoUrl] = useState<string | null>(null);

  useEffect(() => {
    const fetchLogo = async () => {
      try {
        const res = await fetch(`${API_URL}/api/public/media/logo`);
        if (res.ok) {
          const data = await res.json();
          if (data.url) {
            const url = data.url.startsWith('/api') 
              ? `${API_URL}${data.url}`
              : `${API_URL}/api/public/media${data.url}`;
            setLogoUrl(url);
          }
        }
      } catch (err) {
        console.error('Erro ao buscar logo:', err);
      }
    };
    if (isOpen) {
      fetchLogo();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/70 z-[100] flex items-center justify-center p-4" onClick={onClose}>
      <div 
        className="bg-[#0a0e0f] rounded-2xl border border-gray-800 w-full max-w-md relative overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors z-10"
          aria-label="Fechar"
        >
          <X size={24} />
        </button>

        {/* Header */}
        <div className="px-8 pt-8 pb-6 text-center">
          <h2 className="text-3xl md:text-4xl font-black text-white mb-2">
            BEM VINDO DE VOLTA
          </h2>
          <p className="text-gray-400 text-sm md:text-base">
            ESTAMOS FELIZES EM TE VER!
          </p>
        </div>

        {/* Image placeholder */}
        <div className="px-8 pb-6 flex justify-center">
          <div className="w-32 h-32 bg-gradient-to-br from-[#d4af37]/20 to-[#ff6b35]/20 rounded-full flex items-center justify-center overflow-hidden">
            {logoUrl ? (
              <img 
                src={logoUrl} 
                alt="Fortune Vegas Logo" 
                className="w-24 h-24 object-contain p-4"
              />
            ) : null}
          </div>
        </div>

        {/* Logo */}
        <div className="px-8 pb-6 flex justify-center">
          {logoUrl ? (
            <img 
              src={logoUrl} 
              alt="Fortune Vegas" 
              className="h-8 object-contain"
            />
          ) : (
            <div className="text-2xl font-black text-white">
              FORTUNE <span className="text-[#d4af37]">VEGAS</span>
            </div>
          )}
        </div>

        {/* Form */}
        <div className="px-8 pb-8 space-y-4">
          {/* Email */}
          <div>
            <label className="block text-gray-300 text-sm mb-2">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#d4af37] focus:border-transparent transition-all"
              placeholder="seu@email.com"
            />
          </div>

          {/* Password */}
          <div>
            <label className="block text-gray-300 text-sm mb-2">Senha</label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 pr-12 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#d4af37] focus:border-transparent transition-all"
                placeholder="Sua senha"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
                aria-label={showPassword ? 'Ocultar senha' : 'Mostrar senha'}
              >
                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </button>
            </div>
          </div>

          {/* Forgot password */}
          <div className="text-right">
            <a href="/esqueci-senha" className="text-[#d4af37] hover:text-[#ffd700] text-sm transition-colors">
              Esqueceu a senha?
            </a>
          </div>

          {/* Error message */}
          {error && (
            <div className="bg-red-500/20 border border-red-500 text-red-200 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          {/* Login button */}
          <button
            onClick={async () => {
              if (!email || !password) {
                setError('Preencha todos os campos');
                return;
              }
              setError('');
              setLoading(true);
              try {
                await login(email, password);
                onClose();
              } catch (err: any) {
                setError(err.message || 'Erro ao fazer login');
              } finally {
                setLoading(false);
              }
            }}
            disabled={loading}
            className="w-full bg-[#ff6b35] hover:bg-[#ff7b35] disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-bold py-4 rounded-lg transition-colors text-lg"
          >
            {loading ? 'Entrando...' : 'Entrar'}
          </button>

          {/* Switch to register */}
          <div className="text-center pt-2">
            <span className="text-gray-400 text-sm">
              Não tem uma conta?{' '}
              <button
                onClick={onSwitchToRegister}
                className="text-[#d4af37] hover:text-[#ffd700] font-semibold transition-colors"
              >
                Registre-se agora
              </button>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
