import { useState, useEffect } from 'react';
import { X, Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { trackPixelEvent } from '../utils/pixelTracker';

const API_URL = import.meta.env.VITE_API_URL || 'https://api.fortunevegas.site';

interface RegisterModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSwitchToLogin: () => void;
}

export default function RegisterModal({ isOpen, onClose, onSwitchToLogin }: RegisterModalProps) {
  const { register } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [logoUrl, setLogoUrl] = useState<string | null>(null);
  const [affiliateCode, setAffiliateCode] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    nome: '',
    telefone: '',
    senha: '',
    termos: false,
  });

  // Capturar código de afiliado da URL ao abrir o modal
  useEffect(() => {
    if (isOpen) {
      const urlParams = new URLSearchParams(window.location.search);
      const ref = urlParams.get('ref');
      if (ref) {
        setAffiliateCode(ref);
        console.log('[AFFILIATE] Código de afiliado capturado:', ref);
      }
    }
  }, [isOpen]);

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

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  return (
    <div className="fixed inset-0 bg-black/70 z-[100] flex items-center justify-center p-4 overflow-y-auto" onClick={onClose}>
      <div 
        className="bg-[#0a0e0f] rounded-2xl border border-gray-800 w-full max-w-md relative overflow-hidden my-8"
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
            SEJA BEM VINDO!
          </h2>
          <p className="text-gray-400 text-sm md:text-base">
            SE CADASTRE PARA ENTRAR
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
          {/* Nome completo */}
          <div>
            <label className="block text-gray-300 text-sm mb-2">Nome completo</label>
            <input
              type="text"
              name="nome"
              value={formData.nome}
              onChange={handleChange}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#d4af37] focus:border-transparent transition-all"
              placeholder="Seu nome completo"
              required
            />
          </div>

          {/* Telefone */}
          <div>
            <label className="block text-gray-300 text-sm mb-2">+55 Telefone com DDD</label>
            <div className="flex items-center gap-2">
              <div className="flex items-center justify-center w-12 h-12 bg-gray-800 border border-gray-700 rounded-lg">
                <span className="text-xl">🇧🇷</span>
              </div>
              <input
                type="tel"
                name="telefone"
                value={formData.telefone}
                onChange={handleChange}
                className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#d4af37] focus:border-transparent transition-all"
                placeholder="(00) 00000-0000"
                required
              />
            </div>
          </div>

          {/* Password */}
          <div>
            <label className="block text-gray-300 text-sm mb-2">Senha</label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                name="senha"
                value={formData.senha}
                onChange={handleChange}
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

          {/* Terms checkbox */}
          <div className="flex items-start gap-3 pt-2">
            <input
              type="checkbox"
              name="termos"
              id="termos"
              checked={formData.termos}
              onChange={handleChange}
              className="mt-1 w-5 h-5 bg-gray-800 border-gray-700 rounded text-[#d4af37] focus:ring-[#d4af37] focus:ring-2"
            />
            <label htmlFor="termos" className="text-gray-400 text-sm flex-1">
              Aceito os{' '}
              <a href="/termos-e-condicoes" className="text-[#d4af37] hover:text-[#ffd700] transition-colors">
                Termos e Condições
              </a>
            </label>
          </div>

          {/* Error message */}
          {error && (
            <div className="bg-red-500/20 border border-red-500 text-red-200 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          {/* Register button */}
          <button
            onClick={async () => {
              if (!formData.termos) {
                setError('Você precisa aceitar os Termos e Condições');
                return;
              }
              if (!formData.nome || !formData.telefone || !formData.senha) {
                setError('Preencha todos os campos obrigatórios');
                return;
              }
              setError('');
              setLoading(true);
              try {
                // Limpar telefone para usar como username (apenas números)
                const phoneClean = formData.telefone.replace(/\D/g, '');
                if (phoneClean.length < 10) {
                  setError('Telefone inválido. Digite o DDD e o número completo.');
                  setLoading(false);
                  return;
                }
                await register({
                  username: phoneClean,
                  password: formData.senha,
                  phone: phoneClean, // Salvar telefone limpo
                  affiliate_code: affiliateCode || undefined, // Enviar código de afiliado se existir
                });
                
                // Disparar evento de pixel para registro
                trackPixelEvent('registration', {
                  content_name: 'User Registration',
                  content_category: 'Account Creation'
                });
                
                onClose();
              } catch (err: any) {
                setError(err.message || 'Erro ao criar conta');
              } finally {
                setLoading(false);
              }
            }}
            disabled={!formData.termos || loading}
            className="w-full bg-[#ff6b35] hover:bg-[#ff7b35] disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-bold py-4 rounded-lg transition-colors text-lg flex items-center justify-center gap-2"
          >
            {loading ? 'Criando conta...' : <>Criar conta <span>→</span></>}
          </button>

          {/* Switch to login */}
          <div className="text-center pt-2">
            <span className="text-gray-400 text-sm">
              Já tem uma conta?{' '}
              <button
                onClick={onSwitchToLogin}
                className="text-[#d4af37] hover:text-[#ffd700] font-semibold transition-colors"
              >
                Entre agora!
              </button>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
