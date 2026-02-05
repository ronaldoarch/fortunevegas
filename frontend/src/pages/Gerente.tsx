import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { ArrowLeft, Users, DollarSign, TrendingUp, Plus, Trash2 } from 'lucide-react';

// Backend FastAPI - usa variável de ambiente ou fallback para localhost
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Gerente() {
  const navigate = useNavigate();
  const { user, token } = useAuth();
  const [activeTab, setActiveTab] = useState<'comecar' | 'subs' | 'desempenho' | 'comissao'>('comecar');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [settings, setSettings] = useState<any>(null);
  const [subAffiliates, setSubAffiliates] = useState<any[]>([]);
  const [performance, setPerformance] = useState<any>(null);
  const [commission, setCommission] = useState<any>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    code: '',
    cpa_rate: '',
    revshare_rate: ''
  });

  useEffect(() => {
    if (!token || !user) {
      navigate('/conta');
      return;
    }
    if (user.role !== 'agent' && user.role !== 'manager') {
      navigate('/conta');
      return;
    }
    loadData();
  }, [token, user, navigate]);

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      // Carregar configurações
      const settingsRes = await fetch(`${API_URL}/api/public/manager/settings`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (settingsRes.ok) {
        setSettings(await settingsRes.json());
      }

      // Carregar sub-afiliados
      const subsRes = await fetch(`${API_URL}/api/public/manager/sub-affiliates`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (subsRes.ok) {
        setSubAffiliates(await subsRes.json());
      }

      // Carregar desempenho
      const perfRes = await fetch(`${API_URL}/api/public/manager/performance`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (perfRes.ok) {
        setPerformance(await perfRes.json());
      }

      // Carregar comissão
      const commRes = await fetch(`${API_URL}/api/public/manager/commission`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (commRes.ok) {
        setCommission(await commRes.json());
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSub = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/public/manager/sub-affiliates`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          username: form.username,
          email: form.email,
          password: form.password,
          code: form.code,
          cpa_rate: parseFloat(form.cpa_rate),
          revshare_rate: parseFloat(form.revshare_rate) || 0
        })
      });

      const data = await response.json();

      if (response.ok) {
        setShowForm(false);
        setForm({ username: '', email: '', password: '', code: '', cpa_rate: '', revshare_rate: '' });
        await loadData();
      } else {
        setError(data.detail || 'Erro ao criar sub-afiliado');
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!token || !user || (user.role !== 'agent' && user.role !== 'manager')) {
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
            <h1 className="text-xl md:text-2xl font-bold">Painel do Gerente</h1>
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
            onClick={() => setActiveTab('subs')}
            className={`px-4 py-2 rounded-lg font-semibold transition-colors whitespace-nowrap ${
              activeTab === 'subs'
                ? 'bg-[#d4af37] text-black'
                : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
            }`}
          >
            Sub-Afiliados
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
        </div>

        {error && (
          <div className="bg-red-500/20 border border-red-500 text-red-400 px-4 py-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        {loading && !settings && (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#d4af37] mx-auto mb-4"></div>
            <p>Carregando...</p>
          </div>
        )}

        {/* Tab Content */}
        {!loading && settings && (
          <>
            {/* Começar Tab */}
            {activeTab === 'comecar' && (
              <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
                <h2 className="text-2xl font-bold mb-4">Como funciona o painel do Gerente</h2>
                <div className="space-y-4 text-gray-300">
                  <div className="flex items-start gap-3">
                    <span className="text-[#d4af37] font-bold text-xl">1.</span>
                    <p>
                      O admin atribuiu um <span className="text-[#d4af37] font-semibold">CPA Pool</span> (ex: R$ {settings.cpa_pool?.toFixed(2) || '0,00'}) para você.
                    </p>
                  </div>
                  <div className="flex items-start gap-3">
                    <span className="text-[#d4af37] font-bold text-xl">2.</span>
                    <p>
                      Crie <span className="text-[#d4af37] font-semibold">Sub-Afiliados</span> na aba ao lado e distribua o CPA entre eles.
                    </p>
                  </div>
                  <div className="flex items-start gap-3">
                    <span className="text-[#d4af37] font-bold text-xl">3.</span>
                    <p>
                      Quando um sub-afiliado trouxer alguém pelo link e essa pessoa fizer o 1º depósito: o sub ganha o CPA que você definiu e você ganha a mesma quantia (comissão sobre o que distribuiu).
                    </p>
                  </div>
                  <div className="flex items-start gap-3">
                    <span className="text-[#d4af37] font-bold text-xl">4.</span>
                    <p>
                      Exemplo: você tem {settings.cpa_pool?.toFixed(2) || '0,00'} de CPA, cria um sub com 15 de CPA. Quando o sub converter, ele ganha 15 e você ganha 15.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Sub-Afiliados Tab */}
            {activeTab === 'subs' && (
              <div className="space-y-4">
                <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-bold">+ Criar Sub-Afiliado</h2>
                    <button
                      onClick={() => setShowForm(!showForm)}
                      className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
                    >
                      {showForm ? 'Cancelar' : 'Novo'}
                    </button>
                  </div>

                  {showForm && (
                    <form onSubmit={handleCreateSub} className="space-y-4">
                      <div>
                        <label className="block text-sm text-gray-400 mb-1">Username *</label>
                        <input
                          type="text"
                          value={form.username}
                          onChange={e => setForm({...form, username: e.target.value})}
                          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-400 mb-1">Email *</label>
                        <input
                          type="email"
                          value={form.email}
                          onChange={e => setForm({...form, email: e.target.value})}
                          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-400 mb-1">Senha *</label>
                        <input
                          type="password"
                          value={form.password}
                          onChange={e => setForm({...form, password: e.target.value})}
                          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-400 mb-1">Código do Afiliado *</label>
                        <input
                          type="text"
                          value={form.code}
                          onChange={e => setForm({...form, code: e.target.value.toUpperCase()})}
                          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
                          placeholder="SUB001"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-400 mb-1">CPA (R$) - para este sub *</label>
                        <input
                          type="number"
                          step="0.01"
                          value={form.cpa_rate}
                          onChange={e => setForm({...form, cpa_rate: e.target.value})}
                          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
                          placeholder="15"
                          required
                        />
                        <p className="text-xs text-gray-500 mt-1">
                          Disponível: R$ {(settings.cpa_available || 0).toFixed(2)}
                        </p>
                      </div>
                      <div>
                        <label className="block text-sm text-gray-400 mb-1">Revshare (%)</label>
                        <input
                          type="number"
                          step="0.01"
                          value={form.revshare_rate}
                          onChange={e => setForm({...form, revshare_rate: e.target.value})}
                          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
                          placeholder="0"
                        />
                      </div>
                      <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-[#d4af37] hover:bg-[#ffd700] text-black font-semibold py-3 rounded-lg transition-colors disabled:opacity-50"
                      >
                        Criar Sub-Afiliado
                      </button>
                    </form>
                  )}
                </div>

                <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
                  <h2 className="text-xl font-bold mb-4">Meus Sub-Afiliados</h2>
                  <div className="mb-4 p-4 bg-gray-800 rounded-lg">
                    <p className="text-sm text-gray-400">
                      CPA Pool: <span className="text-[#d4af37] font-semibold">R$ {(settings.cpa_pool || 0).toFixed(2)}</span> | 
                      Distribuído: <span className="text-[#d4af37] font-semibold">R$ {(settings.cpa_distributed || 0).toFixed(2)}</span>
                    </p>
                  </div>
                  {subAffiliates.length === 0 ? (
                    <div className="text-center py-8 text-gray-400">
                      <p>Nenhum sub-afiliado cadastrado ainda.</p>
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead>
                          <tr className="border-b border-gray-700">
                            <th className="px-4 py-3 text-left text-sm font-semibold">Código</th>
                            <th className="px-4 py-3 text-left text-sm font-semibold">Nome</th>
                            <th className="px-4 py-3 text-left text-sm font-semibold">CPA</th>
                            <th className="px-4 py-3 text-left text-sm font-semibold">Revshare</th>
                            <th className="px-4 py-3 text-left text-sm font-semibold">Criado em</th>
                          </tr>
                        </thead>
                        <tbody>
                          {subAffiliates.map((sub) => (
                            <tr key={sub.id} className="border-b border-gray-700">
                              <td className="px-4 py-3">{sub.affiliate_code}</td>
                              <td className="px-4 py-3">{sub.affiliate_name}</td>
                              <td className="px-4 py-3 text-[#d4af37]">R$ {sub.cpa_rate.toFixed(2)}</td>
                              <td className="px-4 py-3 text-[#d4af37]">{sub.revshare_rate.toFixed(2)}%</td>
                              <td className="px-4 py-3 text-gray-400 text-sm">
                                {new Date(sub.created_at).toLocaleDateString('pt-BR')}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
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
                    <p className="text-gray-400 text-sm mb-1">Sub-Afiliados</p>
                    <p className="text-3xl font-bold">{performance.sub_affiliates || 0}</p>
                  </div>
                  <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
                    <div className="flex items-center gap-3 mb-2">
                      <DollarSign className="text-[#d4af37]" size={24} />
                    </div>
                    <p className="text-gray-400 text-sm mb-1">CPA Pool</p>
                    <p className="text-3xl font-bold text-[#d4af37]">
                      R$ {(performance.cpa_pool || 0).toFixed(2).replace('.', ',')}
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
            {activeTab === 'comissao' && commission && (
              <div className="space-y-4">
                <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
                  <h2 className="text-xl font-bold mb-4">Sua Comissão</h2>
                  <p className="text-gray-300 mb-6">
                    Você ganha o mesmo valor de CPA que atribui aos sub-afiliados quando eles convertem. 
                    Também recebe revshare sobre os depósitos dos indicados dos seus subs.
                  </p>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="bg-gray-800 rounded-lg p-4">
                      <p className="text-gray-400 text-sm mb-1">Total Ganho</p>
                      <p className="text-3xl font-bold text-[#d4af37]">
                        R$ {(commission.total_earned || 0).toFixed(2).replace('.', ',')}
                      </p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-4">
                      <p className="text-gray-400 text-sm mb-1">CPA Ganho</p>
                      <p className="text-3xl font-bold text-[#d4af37]">
                        R$ {(commission.cpa_earned || 0).toFixed(2).replace('.', ',')}
                      </p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-4">
                      <p className="text-gray-400 text-sm mb-1">Revshare Ganho</p>
                      <p className="text-3xl font-bold text-[#d4af37]">
                        R$ {(commission.revshare_earned || 0).toFixed(2).replace('.', ',')}
                      </p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-4">
                      <p className="text-gray-400 text-sm mb-1">Revshare (%)</p>
                      <p className="text-3xl font-bold text-[#d4af37]">
                        {(commission.revshare_rate || 0).toFixed(2)}%
                      </p>
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
