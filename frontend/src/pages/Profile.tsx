import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Wallet, User, Mail, Phone, CreditCard, LogOut, ArrowLeft, Settings } from 'lucide-react';

export default function Profile() {
  const navigate = useNavigate();
  const { user, token, logout } = useAuth();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) {
      navigate('/');
      return;
    }
    if (user) {
      setLoading(false);
    }
  }, [token, user, navigate]);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  if (loading || !user) {
    return (
      <div className="min-h-screen bg-[#0a0e0f] text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#d4af37] mx-auto mb-4"></div>
          <p>Carregando...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0e0f] text-white">
      {/* Header */}
      <div className="bg-[#0a4d3e] border-b border-[#0d5d4b] sticky top-0 z-40">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/')}
              className="p-2 hover:bg-[#0d5d4b] rounded transition-colors"
            >
              <ArrowLeft size={20} />
            </button>
            <h1 className="text-xl md:text-2xl font-bold">Minha Conta</h1>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Saldo/Carteira */}
        <div className="bg-gradient-to-br from-[#0a4d3e] to-[#0d5d4b] rounded-2xl p-6 mb-6 border border-[#d4af37]/20">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="bg-[#d4af37]/20 p-3 rounded-lg">
                <Wallet className="text-[#d4af37]" size={24} />
              </div>
              <div>
                <p className="text-gray-300 text-sm">Saldo Disponível</p>
                <p className="text-3xl font-bold text-white">
                  R$ {user.balance.toFixed(2).replace('.', ',')}
                </p>
              </div>
            </div>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => navigate('/depositar')}
              className="flex-1 bg-[#ff6b35] hover:bg-[#ff7b35] text-white font-semibold py-3 rounded-lg transition-colors"
            >
              Depositar
            </button>
            <button
              onClick={() => navigate('/sacar')}
              className="flex-1 bg-[#d4af37] hover:bg-[#ffd700] text-black font-semibold py-3 rounded-lg transition-colors"
            >
              Sacar
            </button>
          </div>
        </div>

        {/* Informações do Perfil */}
        <div className="bg-gray-900 rounded-2xl p-6 mb-6 border border-gray-800">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <User size={20} className="text-[#d4af37]" />
            Informações Pessoais
          </h2>
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <Mail size={18} className="text-gray-400" />
              <div>
                <p className="text-gray-400 text-sm">Email</p>
                <p className="text-white">{user.email}</p>
              </div>
            </div>
            {user.cpf && (
              <div className="flex items-center gap-3">
                <CreditCard size={18} className="text-gray-400" />
                <div>
                  <p className="text-gray-400 text-sm">CPF</p>
                  <p className="text-white">{user.cpf}</p>
                </div>
              </div>
            )}
            {user.phone && (
              <div className="flex items-center gap-3">
                <Phone size={18} className="text-gray-400" />
                <div>
                  <p className="text-gray-400 text-sm">Telefone</p>
                  <p className="text-white">{user.phone}</p>
                </div>
              </div>
            )}
            <div className="flex items-center gap-3">
              <div>
                <p className="text-gray-400 text-sm">Status da Conta</p>
                <p className={`font-semibold ${user.is_verified ? 'text-green-400' : 'text-yellow-400'}`}>
                  {user.is_verified ? 'Verificada' : 'Pendente de Verificação'}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Ações */}
        <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
          <h2 className="text-xl font-bold mb-4">Ações</h2>
          <div className="space-y-3">
            <button
              onClick={() => navigate('/historico')}
              className="w-full bg-gray-800 hover:bg-gray-700 text-white font-semibold py-3 rounded-lg transition-colors text-left px-4"
            >
              Histórico de Transações
            </button>
            <button
              onClick={() => navigate('/apostas')}
              className="w-full bg-gray-800 hover:bg-gray-700 text-white font-semibold py-3 rounded-lg transition-colors text-left px-4"
            >
              Minhas Apostas
            </button>
            
            {/* Botão para Gerentes */}
            {(user.role === 'agent' || user.role === 'manager') && (
              <button
                onClick={() => navigate('/admin')}
                className="w-full bg-[#d4af37] hover:bg-[#ffd700] text-black font-semibold py-3 rounded-lg transition-colors text-left px-4 flex items-center gap-2"
              >
                <User size={18} />
                Painel do Gerente
              </button>
            )}
            
            {/* Botão para Afiliados */}
            {user.affiliate_id && (
              <button
                onClick={() => navigate('/afiliado')}
                className="w-full bg-[#0a4d3e] hover:bg-[#0d5d4b] text-white font-semibold py-3 rounded-lg transition-colors text-left px-4 flex items-center gap-2"
              >
                <User size={18} />
                Painel do Afiliado
              </button>
            )}
            
            <button
              onClick={handleLogout}
              className="w-full bg-red-600/20 hover:bg-red-600/30 border border-red-600 text-red-400 font-semibold py-3 rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              <LogOut size={18} />
              Sair da Conta
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
