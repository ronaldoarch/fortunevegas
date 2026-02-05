import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { ArrowLeft, Copy, Check, TrendingUp, DollarSign, Users } from 'lucide-react';

// Backend FastAPI - usa variável de ambiente ou fallback para localhost
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Afiliado() {
  const navigate = useNavigate();
  const { user, token } = useAuth();
  const [activeTab, setActiveTab] = useState<'comecar' | 'link' | 'dados' | 'desempenho' | 'comissao' | 'metricas'>('comecar');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [affiliateData, setAffiliateData] = useState<any>(null);
  const [affiliateLink, setAffiliateLink] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [performance, setPerformance] = useState<any>(null);
  const [metrics, setMetrics] = useState<any>(null);
  const [copied, setCopied] = useState(false);
  const [period, setPeriod] = useState<'week' | 'last_week' | 'month' | 'last_month'>('month');
  const [metricsPeriod, setMetricsPeriod] = useState<'week' | 'last_week' | 'month' | 'last_month' | 'all'>('month');

  useEffect(() => {
    if (!token || !user) {
      navigate('/conta');
      return;
    }
    if (!user.affiliate_id) {
      navigate('/conta');
      return;
    }
    loadData();
  }, [token, user, navigate, period, metricsPeriod]);

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      // Carregar dados do afiliado
      const affiliateRes = await fetch(`${API_URL}/api/public/affiliate/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (affiliateRes.ok) {
        setAffiliateData(await affiliateRes.json());
      }

      // Carregar link de afiliado
      const linkRes = await fetch(`${API_URL}/api/public/affiliate/link`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (linkRes.ok) {
        setAffiliateLink(await linkRes.json());
      }

      // Carregar estatísticas
      const statsRes = await fetch(`${API_URL}/api/public/affiliate/stats?period=${period}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (statsRes.ok) {
        setStats(await statsRes.json());
      }

      // Carregar desempenho
      const perfRes = await fetch(`${API_URL}/api/public/affiliate/performance`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (perfRes.ok) {
        setPerformance(await perfRes.json());
      }

      // Carregar métricas
      const metricsRes = await fetch(`${API_URL}/api/public/affiliate/metrics?period=${metricsPeriod}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (metricsRes.ok) {
        setMetrics(await metricsRes.json());
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const copyLink = () => {
    if (affiliateLink?.link) {
      navigator.clipboard.writeText(affiliateLink.link);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!token || !user || !user.affiliate_id) {
    return null;
  }

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
            <h1 className="text-xl md:text-2xl font-bold">Promoção</h1>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-6 max-w-6xl">
        {/* Tabs */}
        <div className="flex gap-2 mb-6 overflow-x-auto">
          <button
            onClick={() => setActiveTab('comecar')}
            className={`px-4 py-2 rounded-lg font-semibold transition-colors whitespace-nowrap ${
              activeTab === 'comecar'
                ? 'bg-[#d4af37] text-black'
                : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
            }`}
          >
            Começar
          </button>
          <button
            onClick={() => setActiveTab('link')}
            className={`px-4 py-2 rounded-lg font-semibold transition-colors whitespace-nowrap ${
              activeTab === 'link'
                ? 'bg-[#d4af37] text-black'
                : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
            }`}
          >
            Link de Convite
          </button>
          <button
            onClick={() => setActiveTab('dados')}
            className={`px-4 py-2 rounded-lg font-semibold transition-colors whitespace-nowrap ${
              activeTab === 'dados'
                ? 'bg-[#d4af37] text-black'
                : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
            }`}
          >
            Meus Dados
          </button>
          <button
            onClick={() => setActiveTab('desempenho')}
            className={`px-4 py-2 rounded-lg font-semibold transition-colors whitespace-nowrap ${
              activeTab === 'desempenho'
                ? 'bg-[#d4af37] text-black'
                : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
            }`}
          >
            Desempenho
          </button>
          <button
            onClick={() => setActiveTab('comissao')}
            className={`px-4 py-2 rounded-lg font-semibold transition-colors whitespace-nowrap ${
              activeTab === 'comissao'
                ? 'bg-[#d4af37] text-black'
                : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
            }`}
          >
            Comissão
          </button>
          <button
            onClick={() => setActiveTab('metricas')}
            className={`px-4 py-2 rounded-lg font-semibold transition-colors whitespace-nowrap ${
              activeTab === 'metricas'
                ? 'bg-[#d4af37] text-black'
                : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
            }`}
          >
            Métricas
          </button>
        </div>

        {error && (
          <div className="bg-red-500/20 border border-red-500 text-red-400 px-4 py-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        {loading && (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#d4af37] mx-auto mb-4"></div>
            <p>Carregando...</p>
          </div>
        )}

        {/* Tab Content */}
        {!loading && (
          <>
            {/* Começar Tab */}
            {activeTab === 'comecar' && (
              <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
                <h2 className="text-2xl font-bold mb-4">Como começar</h2>
                <div className="space-y-4 text-gray-300">
                  <div className="flex items-start gap-3">
                    <span className="text-[#d4af37] font-bold text-xl">1.</span>
                    <p>
                      Copie seu <span className="text-[#d4af37] font-semibold">Link de Convite</span> na aba ao lado.
                    </p>
                  </div>
                  <div className="flex items-start gap-3">
                    <span className="text-[#d4af37] font-bold text-xl">2.</span>
                    <p>
                      Compartilhe o link com seus amigos (WhatsApp, redes sociais, etc.).
                    </p>
                  </div>
                  <div className="flex items-start gap-3">
                    <span className="text-[#d4af37] font-bold text-xl">3.</span>
                    <p>
                      Quando alguém se cadastrar pelo seu link e fizer o primeiro depósito, você ganha CPA e revshare.
                    </p>
                  </div>
                  <div className="flex items-start gap-3">
                    <span className="text-[#d4af37] font-bold text-xl">4.</span>
                    <p>
                      Acompanhe tudo em <span className="text-[#d4af37] font-semibold">Meus Dados</span> e <span className="text-[#d4af37] font-semibold">Comissão</span>.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Link de Convite Tab */}
            {activeTab === 'link' && affiliateLink && (
              <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
                <h2 className="text-xl font-bold mb-4">Seu Link de Afiliado</h2>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm text-gray-400">Código:</label>
                    <p className="text-2xl font-bold text-[#d4af37] mt-1">{affiliateLink.code}</p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-400">Link completo:</label>
                    <p className="text-gray-300 mt-1 break-all">{affiliateLink.link}</p>
                  </div>
                  <button
                    onClick={copyLink}
                    className="w-full bg-[#d4af37] hover:bg-[#ffd700] text-black font-semibold py-3 rounded-lg transition-colors flex items-center justify-center gap-2"
                  >
                    {copied ? (
                      <>
                        <Check size={18} />
                        Link Copiado!
                      </>
                    ) : (
                      <>
                        <Copy size={18} />
                        Copiar Link
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}

            {/* Meus Dados Tab */}
            {activeTab === 'dados' && stats && (
              <div className="space-y-4">
                {/* Filtros de período */}
                <div className="flex gap-2 overflow-x-auto">
                  <button
                    onClick={() => setPeriod('week')}
                    className={`px-4 py-2 rounded-lg text-sm font-semibold whitespace-nowrap ${
                      period === 'week'
                        ? 'bg-[#0a4d3e] text-white'
                        : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                    }`}
                  >
                    Esta Semana
                  </button>
                  <button
                    onClick={() => setPeriod('last_week')}
                    className={`px-4 py-2 rounded-lg text-sm font-semibold whitespace-nowrap ${
                      period === 'last_week'
                        ? 'bg-[#0a4d3e] text-white'
                        : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                    }`}
                  >
                    Última Semana
                  </button>
                  <button
                    onClick={() => setPeriod('month')}
                    className={`px-4 py-2 rounded-lg text-sm font-semibold whitespace-nowrap ${
                      period === 'month'
                        ? 'bg-[#0a4d3e] text-white'
                        : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                    }`}
                  >
                    Este Mês
                  </button>
                  <button
                    onClick={() => setPeriod('last_month')}
                    className={`px-4 py-2 rounded-lg text-sm font-semibold whitespace-nowrap ${
                      period === 'last_month'
                        ? 'bg-[#0a4d3e] text-white'
                        : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                    }`}
                  >
                    Mês passado
                  </button>
                </div>

                <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
                  <h2 className="text-xl font-bold mb-4">Dados do Subordinado</h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div className="bg-gray-800 rounded-lg p-4">
                      <p className="text-gray-400 text-sm mb-1">Novos subordinados</p>
                      <p className="text-2xl font-bold">{stats.new_subordinates || 0}</p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-4">
                      <p className="text-gray-400 text-sm mb-1">Depósitos</p>
                      <p className="text-2xl font-bold">{stats.total_deposits || 0}</p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-4">
                      <p className="text-gray-400 text-sm mb-1">Primeiros Depósitos</p>
                      <p className="text-2xl font-bold">{stats.total_ftds || 0}</p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-4">
                      <p className="text-gray-400 text-sm mb-1">Usuários registrados com 1º depósito</p>
                      <p className="text-2xl font-bold">{stats.users_with_ftd || 0}</p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-4">
                      <p className="text-gray-400 text-sm mb-1">Depósito</p>
                      <p className="text-2xl font-bold text-[#d4af37]">
                        R$ {(stats.total_deposit_amount || 0).toFixed(2).replace('.', ',')}
                      </p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-4">
                      <p className="text-gray-400 text-sm mb-1">Valor do primeiro depósito</p>
                      <p className="text-2xl font-bold text-[#d4af37]">
                        R$ {(stats.total_ftd_amount || 0).toFixed(2).replace('.', ',')}
                      </p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-4">
                      <p className="text-gray-400 text-sm mb-1">Registro e 1º depósito</p>
                      <p className="text-2xl font-bold text-[#d4af37]">
                        R$ {(stats.total_ftd_amount || 0).toFixed(2).replace('.', ',')}
                      </p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-4">
                      <p className="text-gray-400 text-sm mb-1">Valor do Saque</p>
                      <p className="text-2xl font-bold text-[#d4af37]">
                        R$ {(stats.total_withdrawal_amount || 0).toFixed(2).replace('.', ',')}
                      </p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-4">
                      <p className="text-gray-400 text-sm mb-1">Número de saques</p>
                      <p className="text-2xl font-bold">{stats.total_withdrawals || 0}</p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-4">
                      <p className="text-gray-400 text-sm mb-1">Receber recompensas</p>
                      <p className="text-2xl font-bold text-[#d4af37]">
                        R$ {(stats.total_earned || 0).toFixed(2).replace('.', ',')}
                      </p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-4">
                      <p className="text-gray-400 text-sm mb-1">Apostas Válidas</p>
                      <p className="text-2xl font-bold text-[#d4af37]">R$ 0,00</p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-4">
                      <p className="text-gray-400 text-sm mb-1">V/D diretas</p>
                      <p className="text-2xl font-bold text-[#d4af37]">R$ 0,00</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Desempenho Tab */}
            {activeTab === 'desempenho' && performance && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
                    <div className="flex items-center gap-3 mb-2">
                      <Users className="text-[#d4af37]" size={24} />
                    </div>
                    <p className="text-gray-400 text-sm mb-1">Indicações</p>
                    <p className="text-3xl font-bold">{performance.referrals || 0}</p>
                  </div>
                  <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
                    <div className="flex items-center gap-3 mb-2">
                      <DollarSign className="text-[#d4af37]" size={24} />
                    </div>
                    <p className="text-gray-400 text-sm mb-1">Depósitos dos indicados</p>
                    <p className="text-3xl font-bold text-[#d4af37]">
                      R$ {(performance.deposits_from_referrals || 0).toFixed(2).replace('.', ',')}
                    </p>
                  </div>
                  <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
                    <div className="flex items-center gap-3 mb-2">
                      <TrendingUp className="text-[#d4af37]" size={24} />
                    </div>
                    <p className="text-gray-400 text-sm mb-1">CPA Ganho</p>
                    <p className="text-3xl font-bold text-[#d4af37]">
                      R$ {(performance.cpa_earned || 0).toFixed(2).replace('.', ',')}
                    </p>
                  </div>
                  <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
                    <div className="flex items-center gap-3 mb-2">
                      <DollarSign className="text-[#d4af37]" size={24} />
                    </div>
                    <p className="text-gray-400 text-sm mb-1">Revshare Ganho</p>
                    <p className="text-3xl font-bold text-[#d4af37]">
                      R$ {(performance.revshare_earned || 0).toFixed(2).replace('.', ',')}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Comissão Tab */}
            {activeTab === 'comissao' && stats && affiliateData && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
                    <p className="text-gray-400 text-sm mb-1">Total Ganho</p>
                    <p className="text-3xl font-bold text-[#d4af37]">
                      R$ {(stats.total_earned || 0).toFixed(2).replace('.', ',')}
                    </p>
                  </div>
                  <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
                    <p className="text-gray-400 text-sm mb-1">CPA Ganho</p>
                    <p className="text-3xl font-bold text-[#d4af37]">
                      R$ {(stats.cpa_earned || 0).toFixed(2).replace('.', ',')}
                    </p>
                  </div>
                  <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
                    <p className="text-gray-400 text-sm mb-1">Revshare Ganho</p>
                    <p className="text-3xl font-bold text-[#d4af37]">
                      R$ {(stats.revshare_earned || 0).toFixed(2).replace('.', ',')}
                    </p>
                  </div>
                  <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
                    <p className="text-gray-400 text-sm mb-1">Status</p>
                    <p className={`text-xl font-bold ${stats.status === 'Ativo' ? 'text-green-400' : 'text-red-400'}`}>
                      {stats.status || 'Inativo'}
                    </p>
                  </div>
                </div>

                <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
                  <h2 className="text-xl font-bold mb-4">Configurações da Comissão</h2>
                  <div className="space-y-4">
                    <div>
                      <p className="text-gray-400 text-sm mb-1">CPA (Cost Per Acquisition)</p>
                      <p className="text-2xl font-bold text-[#d4af37]">
                        R$ {(stats.cpa_rate || 0).toFixed(2).replace('.', ',')}
                      </p>
                      <p className="text-gray-400 text-sm mt-1">Por cada novo jogador com 1º depósito</p>
                    </div>
                    <div>
                      <p className="text-gray-400 text-sm mb-1">Revshare</p>
                      <p className="text-2xl font-bold text-[#d4af37]">
                        {(stats.revshare_rate || 0).toFixed(2)}%
                      </p>
                      <p className="text-gray-400 text-sm mt-1">Sobre os depósitos dos indicados</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Métricas Tab */}
            {activeTab === 'metricas' && metrics && (
              <div className="space-y-4">
                {/* Filtros de período */}
                <div className="flex gap-2 overflow-x-auto">
                  <button
                    onClick={() => setMetricsPeriod('week')}
                    className={`px-4 py-2 rounded-lg text-sm font-semibold whitespace-nowrap ${
                      metricsPeriod === 'week'
                        ? 'bg-[#0a4d3e] text-white'
                        : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                    }`}
                  >
                    Esta Semana
                  </button>
                  <button
                    onClick={() => setMetricsPeriod('last_week')}
                    className={`px-4 py-2 rounded-lg text-sm font-semibold whitespace-nowrap ${
                      metricsPeriod === 'last_week'
                        ? 'bg-[#0a4d3e] text-white'
                        : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                    }`}
                  >
                    Última Semana
                  </button>
                  <button
                    onClick={() => setMetricsPeriod('month')}
                    className={`px-4 py-2 rounded-lg text-sm font-semibold whitespace-nowrap ${
                      metricsPeriod === 'month'
                        ? 'bg-[#0a4d3e] text-white'
                        : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                    }`}
                  >
                    Este Mês
                  </button>
                  <button
                    onClick={() => setMetricsPeriod('last_month')}
                    className={`px-4 py-2 rounded-lg text-sm font-semibold whitespace-nowrap ${
                      metricsPeriod === 'last_month'
                        ? 'bg-[#0a4d3e] text-white'
                        : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                    }`}
                  >
                    Mês passado
                  </button>
                  <button
                    onClick={() => setMetricsPeriod('all')}
                    className={`px-4 py-2 rounded-lg text-sm font-semibold whitespace-nowrap ${
                      metricsPeriod === 'all'
                        ? 'bg-[#0a4d3e] text-white'
                        : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                    }`}
                  >
                    Todos
                  </button>
                </div>

                <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
                  <h2 className="text-xl font-bold mb-4">Rastreamento de Métricas</h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                    <div className="bg-gray-800 rounded-lg p-4">
                      <p className="text-gray-400 text-sm mb-1">Total de Cliques</p>
                      <p className="text-2xl font-bold">{metrics.total_clicks || 0}</p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-4">
                      <p className="text-gray-400 text-sm mb-1">Registros</p>
                      <p className="text-2xl font-bold">{metrics.total_registrations || 0}</p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-4">
                      <p className="text-gray-400 text-sm mb-1">Primeiros Depósitos</p>
                      <p className="text-2xl font-bold">{metrics.total_first_deposits || 0}</p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-4">
                      <p className="text-gray-400 text-sm mb-1">Taxa de Conversão</p>
                      <p className="text-2xl font-bold text-[#d4af37]">{metrics.conversion_rate || 0}%</p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-4">
                      <p className="text-gray-400 text-sm mb-1">Registro → Depósito</p>
                      <p className="text-2xl font-bold text-[#d4af37]">{metrics.registration_to_deposit_rate || 0}%</p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-4">
                      <p className="text-gray-400 text-sm mb-1">Total Depósitos</p>
                      <p className="text-2xl font-bold">{metrics.total_deposits || 0}</p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-4">
                      <p className="text-gray-400 text-sm mb-1">Valor Total Depósitos</p>
                      <p className="text-2xl font-bold text-[#d4af37]">
                        R$ {(metrics.total_deposit_amount || 0).toFixed(2).replace('.', ',')}
                      </p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-4">
                      <p className="text-gray-400 text-sm mb-1">Total Saques</p>
                      <p className="text-2xl font-bold">{metrics.total_withdrawals || 0}</p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
