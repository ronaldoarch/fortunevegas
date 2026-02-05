import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { ArrowLeft, TrendingUp, TrendingDown, RefreshCw } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Historico() {
  const navigate = useNavigate();
  const { user, token } = useAuth();
  const [deposits, setDeposits] = useState<any[]>([]);
  const [withdrawals, setWithdrawals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'deposits' | 'withdrawals'>('deposits');

  useEffect(() => {
    if (!token || !user) {
      navigate('/conta');
      return;
    }
    fetchData();
  }, [token, user, navigate]);

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const [depositsRes, withdrawalsRes] = await Promise.all([
        fetch(`${API_URL}/api/public/payments/my-deposits`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        fetch(`${API_URL}/api/public/payments/my-withdrawals`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);

      if (!depositsRes.ok) throw new Error('Falha ao carregar depósitos');
      if (!withdrawalsRes.ok) throw new Error('Falha ao carregar saques');

      setDeposits(await depositsRes.json());
      setWithdrawals(await withdrawalsRes.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
      case 'approved':
        return 'text-green-400';
      case 'pending':
        return 'text-yellow-400';
      case 'failed':
      case 'rejected':
        return 'text-red-400';
      default:
        return 'text-gray-400';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
      case 'approved':
        return 'Aprovado';
      case 'pending':
        return 'Pendente';
      case 'failed':
      case 'rejected':
        return 'Rejeitado';
      default:
        return status;
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
            <h1 className="text-xl md:text-2xl font-bold">Histórico de Transações</h1>
            <button
              onClick={fetchData}
              className="ml-auto p-2 hover:bg-[#0d5d4b] rounded transition-colors"
            >
              <RefreshCw size={20} />
            </button>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Tabs */}
        <div className="flex gap-2 mb-6 border-b border-gray-800">
          <button
            onClick={() => setActiveTab('deposits')}
            className={`px-4 py-2 font-semibold transition-colors ${
              activeTab === 'deposits'
                ? 'border-b-2 border-[#d4af37] text-[#d4af37]'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Depósitos ({deposits.length})
          </button>
          <button
            onClick={() => setActiveTab('withdrawals')}
            className={`px-4 py-2 font-semibold transition-colors ${
              activeTab === 'withdrawals'
                ? 'border-b-2 border-[#d4af37] text-[#d4af37]'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Saques ({withdrawals.length})
          </button>
        </div>

        {error && (
          <div className="bg-red-500/20 border border-red-500 text-red-400 px-4 py-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#d4af37] mx-auto mb-4"></div>
            <p>Carregando transações...</p>
          </div>
        ) : (
          <>
            {activeTab === 'deposits' && (
              <div className="space-y-4">
                {deposits.length === 0 ? (
                  <div className="text-center py-12 text-gray-400">
                    <TrendingUp size={48} className="mx-auto mb-4 opacity-50" />
                    <p>Nenhum depósito encontrado</p>
                  </div>
                ) : (
                  <div className="bg-gray-900 rounded-2xl border border-gray-800 overflow-hidden">
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-gray-800">
                          <tr>
                            <th className="px-4 py-3 text-left text-sm font-semibold">ID</th>
                            <th className="px-4 py-3 text-left text-sm font-semibold">Valor</th>
                            <th className="px-4 py-3 text-left text-sm font-semibold">Status</th>
                            <th className="px-4 py-3 text-left text-sm font-semibold">Data</th>
                          </tr>
                        </thead>
                        <tbody>
                          {deposits.map((deposit) => (
                            <tr key={deposit.id} className="border-t border-gray-800 hover:bg-gray-800/50">
                              <td className="px-4 py-3">#{deposit.id}</td>
                              <td className="px-4 py-3 font-semibold text-green-400">
                                R$ {deposit.amount.toFixed(2).replace('.', ',')}
                              </td>
                              <td className="px-4 py-3">
                                <span className={getStatusColor(deposit.status)}>
                                  {getStatusLabel(deposit.status)}
                                </span>
                              </td>
                              <td className="px-4 py-3 text-gray-400 text-sm">
                                {formatDate(deposit.created_at)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'withdrawals' && (
              <div className="space-y-4">
                {withdrawals.length === 0 ? (
                  <div className="text-center py-12 text-gray-400">
                    <TrendingDown size={48} className="mx-auto mb-4 opacity-50" />
                    <p>Nenhum saque encontrado</p>
                  </div>
                ) : (
                  <div className="bg-gray-900 rounded-2xl border border-gray-800 overflow-hidden">
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-gray-800">
                          <tr>
                            <th className="px-4 py-3 text-left text-sm font-semibold">ID</th>
                            <th className="px-4 py-3 text-left text-sm font-semibold">Valor</th>
                            <th className="px-4 py-3 text-left text-sm font-semibold">Status</th>
                            <th className="px-4 py-3 text-left text-sm font-semibold">Data</th>
                          </tr>
                        </thead>
                        <tbody>
                          {withdrawals.map((withdrawal) => (
                            <tr key={withdrawal.id} className="border-t border-gray-800 hover:bg-gray-800/50">
                              <td className="px-4 py-3">#{withdrawal.id}</td>
                              <td className="px-4 py-3 font-semibold text-red-400">
                                R$ {withdrawal.amount.toFixed(2).replace('.', ',')}
                              </td>
                              <td className="px-4 py-3">
                                <span className={getStatusColor(withdrawal.status)}>
                                  {getStatusLabel(withdrawal.status)}
                                </span>
                              </td>
                              <td className="px-4 py-3 text-gray-400 text-sm">
                                {formatDate(withdrawal.created_at)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
