import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { ArrowLeft, RefreshCw, Trophy, X } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Apostas() {
  const navigate = useNavigate();
  const { user, token } = useAuth();
  const [bets, setBets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!token || !user) {
      navigate('/conta');
      return;
    }
    fetchBets();
  }, [token, user, navigate]);

  const fetchBets = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_URL}/api/public/payments/my-bets`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Falha ao carregar apostas');
      setBets(await res.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'won':
        return 'text-green-400';
      case 'lost':
        return 'text-red-400';
      case 'pending':
        return 'text-yellow-400';
      case 'cancelled':
        return 'text-gray-400';
      default:
        return 'text-gray-400';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status.toLowerCase()) {
      case 'won':
        return 'Ganhou';
      case 'lost':
        return 'Perdeu';
      case 'pending':
        return 'Pendente';
      case 'cancelled':
        return 'Cancelada';
      default:
        return status;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'won':
        return <Trophy size={16} className="text-green-400" />;
      case 'lost':
        return <X size={16} className="text-red-400" />;
      default:
        return null;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const calculateProfit = (bet: any) => {
    if (bet.status === 'won') {
      return bet.win_amount - bet.amount;
    }
    return -bet.amount;
  };

  return (
    <div className="min-h-screen bg-[#0a0e0f] text-white">
      {/* Header */}
      <div className="bg-[#0a4d3e] border-b border-[#0d5d4b] sticky top-0 z-40">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/conta')}
              className="p-2 hover:bg-[#0d5d4b] rounded transition-colors"
            >
              <ArrowLeft size={20} />
            </button>
            <h1 className="text-xl md:text-2xl font-bold">Minhas Apostas</h1>
            <button
              onClick={fetchBets}
              className="ml-auto p-2 hover:bg-[#0d5d4b] rounded transition-colors"
            >
              <RefreshCw size={20} />
            </button>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {error && (
          <div className="bg-red-500/20 border border-red-500 text-red-400 px-4 py-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#d4af37] mx-auto mb-4"></div>
            <p>Carregando apostas...</p>
          </div>
        ) : bets.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            <Trophy size={48} className="mx-auto mb-4 opacity-50" />
            <p>Nenhuma aposta encontrada</p>
            <p className="text-sm mt-2">Suas apostas aparecerão aqui após você jogar</p>
          </div>
        ) : (
          <div className="bg-gray-900 rounded-2xl border border-gray-800 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-800">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-semibold">Jogo</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold">Provedor</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold">Aposta</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold">Ganho</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold">Lucro/Prejuízo</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold">Status</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold">Data</th>
                  </tr>
                </thead>
                <tbody>
                  {bets.map((bet) => {
                    const profit = calculateProfit(bet);
                    return (
                      <tr key={bet.id} className="border-t border-gray-800 hover:bg-gray-800/50">
                        <td className="px-4 py-3">
                          <div className="font-semibold">{bet.game_name || bet.game_id || '-'}</div>
                        </td>
                        <td className="px-4 py-3 text-gray-400 text-sm">
                          {bet.provider || '-'}
                        </td>
                        <td className="px-4 py-3 font-semibold">
                          R$ {bet.amount.toFixed(2).replace('.', ',')}
                        </td>
                        <td className="px-4 py-3">
                          {bet.win_amount > 0 ? (
                            <span className="text-green-400 font-semibold">
                              R$ {bet.win_amount.toFixed(2).replace('.', ',')}
                            </span>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          {profit !== 0 && (
                            <span className={`font-semibold ${profit > 0 ? 'text-green-400' : 'text-red-400'}`}>
                              {profit > 0 ? '+' : ''}R$ {profit.toFixed(2).replace('.', ',')}
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            {getStatusIcon(bet.status)}
                            <span className={getStatusColor(bet.status)}>
                              {getStatusLabel(bet.status)}
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-gray-400 text-sm">
                          {formatDate(bet.created_at)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
