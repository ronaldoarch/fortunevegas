import { useState, useEffect } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import { 
  Users, DollarSign, TrendingUp, Settings, 
  LogOut, Menu, X, CreditCard, ArrowUpCircle, 
  ArrowDownCircle, Activity, RefreshCw,
  Image as ImageIcon, Home,
  ChevronUp, ChevronDown, Percent, FileText, 
  Gift, Tag, Gamepad2, Megaphone, HelpCircle, Webhook
} from 'lucide-react';
import type { ThemePalette } from '../utils/themeManager';
import { applyThemeToDocument } from '../utils/themeManager';

interface Stats {
  total_users: number;
  total_deposits: number;
  total_withdrawals: number;
  total_ftds: number;
  total_deposit_amount: number;
  total_withdrawal_amount: number;
  pending_deposits: number;
  pending_withdrawals: number;
  net_revenue: number;
  // Métricas expandidas
  usuarios_na_casa?: number;
  usuarios_registrados_hoje?: number;
  balanco_jogador_total?: number;
  jogadores_com_saldo?: number;
  ggr_gerado?: number;
  ggr_taxa?: number;
  total_pago_ggr?: number;
  pix_recebido_hoje?: number;
  pix_recebido_count_hoje?: number;
  pix_feito_hoje?: number;
  pix_feito_count_hoje?: number;
  pix_gerado_hoje?: number;
  pix_percentual_pago?: number;
  pagamentos_recebidos_hoje?: number;
  valor_pagamentos_recebidos_hoje?: number;
  pagamentos_feitos_hoje?: number;
  valor_pagamentos_feitos_hoje?: number;
  pagamentos_feitos_total?: number;
  ftd_hoje?: number;
  depositos_hoje?: number;
  total_lucro?: number;
}

// Backend FastAPI - usa variável de ambiente ou fallback para localhost
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Admin() {
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [token, setToken] = useState<string | null>(localStorage.getItem('admin_token'));
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  
  // Estado para controlar seções expansíveis
  const [expandedSections, setExpandedSections] = useState({
    financeiro: true,
    notificacoes: true,
    marketing: true,
    geral: true,
  });

  useEffect(() => {
    if (!token) {
      navigate('/admin/login');
      return;
    }
    loadStats();
  }, [token, navigate]);

  const loadStats = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/admin/stats`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Error loading stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    setToken(null);
    navigate('/admin/login');
  };

  if (!token) {
    return <Navigate to="/admin/login" replace />;
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 sticky top-0 z-50">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="md:hidden p-2 hover:bg-gray-700 rounded"
            >
              {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
            <h1 className="text-xl font-bold">Fortune Vegas Admin</h1>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 rounded transition-colors"
          >
            <LogOut size={20} />
            <span className="hidden sm:inline">Sair</span>
          </button>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside
          className={`fixed md:static left-0 top-[57px] h-[calc(100vh-57px)] w-64 bg-gray-800 border-r border-gray-700 transition-transform z-40 ${
            sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
          }`}
        >
          <nav className="p-4 space-y-1">
            <NavItem
              icon={<Home />}
              label="Painel de Controle"
              active={activeTab === 'dashboard'}
              onClick={() => setActiveTab('dashboard')}
            />
            <NavItem
              icon={<Settings />}
              label="Configuração"
              active={activeTab === 'settings'}
              onClick={() => setActiveTab('settings')}
            />
            
            <NavSection
              title="Gestão Financeira"
              expanded={expandedSections.financeiro}
              onToggle={() => setExpandedSections({...expandedSections, financeiro: !expandedSections.financeiro})}
            >
              <NavSubItem
                icon={<Percent />}
                label="GGR / Relatorio"
                active={activeTab === 'ggr'}
                onClick={() => setActiveTab('ggr')}
              />
              <NavSubItem
                icon={<DollarSign />}
                label="Depósitos e Saques"
                active={activeTab === 'transactions'}
                onClick={() => setActiveTab('transactions')}
              />
              <NavSubItem
                icon={<FileText />}
                label="Apostas"
                active={activeTab === 'bets'}
                onClick={() => setActiveTab('bets')}
              />
            </NavSection>
            
            <NavSection
              title="Centro de Notificações"
              expanded={expandedSections.notificacoes}
              onToggle={() => setExpandedSections({...expandedSections, notificacoes: !expandedSections.notificacoes})}
            >
              <NavSubItem
                icon={<Gift />}
                label="Notificações"
                active={activeTab === 'notifications'}
                onClick={() => setActiveTab('notifications')}
              />
              <NavSubItem
                icon={<Megaphone />}
                label="Promoções"
                active={activeTab === 'promotions'}
                onClick={() => setActiveTab('promotions')}
              />
            </NavSection>
            
            <NavSection
              title="Marketing"
              expanded={expandedSections.marketing}
              onToggle={() => setExpandedSections({...expandedSections, marketing: !expandedSections.marketing})}
            >
            </NavSection>
            
            <NavSection
              title="Geral"
              expanded={expandedSections.geral}
              onToggle={() => setExpandedSections({...expandedSections, geral: !expandedSections.geral})}
            >
              <NavSubItem
                icon={<Users />}
                label="Usuarios"
                active={activeTab === 'users'}
                onClick={() => setActiveTab('users')}
              />
              <NavSubItem
                icon={<Tag />}
                label="Cupom"
                active={activeTab === 'coupons'}
                onClick={() => setActiveTab('coupons')}
              />
              <NavSubItem
                icon={<ImageIcon />}
                label="Branding"
                active={activeTab === 'branding'}
                onClick={() => setActiveTab('branding')}
              />
              <NavSubItem
                icon={<CreditCard />}
                label="Gateways"
                active={activeTab === 'gateways'}
                onClick={() => setActiveTab('gateways')}
              />
              <NavSubItem
                icon={<Gamepad2 />}
                label="IGameWin"
                active={activeTab === 'igamewin'}
                onClick={() => setActiveTab('igamewin')}
              />
              <NavSubItem
                icon={<Settings />}
                label="Provedores IGameWin"
                active={activeTab === 'igamewin-providers'}
                onClick={() => setActiveTab('igamewin-providers')}
              />
              <NavSubItem
                icon={<TrendingUp />}
                label="Tracking"
                active={activeTab === 'tracking'}
                onClick={() => setActiveTab('tracking')}
              />
              <NavSubItem
                icon={<Webhook />}
                label="Webhooks"
                active={activeTab === 'webhooks'}
                onClick={() => setActiveTab('webhooks')}
              />
              <NavSubItem
                icon={<Tag />}
                label="Temas"
                active={activeTab === 'themes'}
                onClick={() => setActiveTab('themes')}
              />
              <NavSubItem
                icon={<Users />}
                label="Afiliados"
                active={activeTab === 'affiliates'}
                onClick={() => setActiveTab('affiliates')}
              />
              <NavSubItem
                icon={<HelpCircle />}
                label="Suporte"
                active={activeTab === 'support'}
                onClick={() => setActiveTab('support')}
              />
            </NavSection>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-6">
          {activeTab === 'dashboard' && <DashboardTab stats={stats} loading={loading} onRefresh={loadStats} />}
          {activeTab === 'users' && <UsersTab token={token || ''} />}
          {activeTab === 'transactions' && <TransactionsTab token={token || ''} />}
          {activeTab === 'gateways' && <GatewaysTab token={token || ''} />}
          {activeTab === 'igamewin' && <IGameWinTab token={token || ''} />}
          {activeTab === 'igamewin-providers' && <IGameWinProvidersTab token={token || ''} />}
          {activeTab === 'tracking' && <TrackingTab token={token || ''} />}
          {activeTab === 'webhooks' && <WebhooksTab token={token || ''} />}
          {activeTab === 'settings' && <SettingsTab token={token || ''} />}
          {activeTab === 'branding' && <BrandingTab token={token || ''} />}
          {activeTab === 'themes' && <ThemesTab token={token || ''} />}
          {activeTab === 'affiliates' && <AffiliatesTab token={token || ''} />}
          {activeTab === 'ggr' && <GGRTab token={token || ''} />}
          {activeTab === 'bets' && <BetsTab token={token || ''} />}
          {activeTab === 'notifications' && <NotificationsTab token={token || ''} />}
          {activeTab === 'promotions' && <PromotionsTab token={token || ''} />}
          {activeTab === 'support' && <SupportTab token={token || ''} />}
          {activeTab === 'coupons' && <CouponsTab token={token || ''} />}
        </main>
      </div>
    </div>
  );
}

function NavItem({ icon, label, active, onClick }: { icon: React.ReactNode; label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
        active ? 'bg-gray-700 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'
      }`}
    >
      <div className={active ? 'text-blue-400' : 'text-gray-400'}>{icon}</div>
      <span className="text-sm">{label}</span>
    </button>
  );
}

function NavSection({ title, expanded, onToggle, children }: { 
  title: string; 
  expanded: boolean; 
  onToggle: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between px-4 py-2 text-gray-400 hover:text-white transition-colors"
      >
        <span className="text-sm font-medium">{title}</span>
        {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </button>
      {expanded && (
        <div className="ml-4 space-y-1">
          {children}
        </div>
      )}
    </div>
  );
}

function NavSubItem({ icon, label, active, onClick }: { icon: React.ReactNode; label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-2 px-3 py-2 rounded text-sm transition-colors ${
        active ? 'bg-gray-700 text-white' : 'text-gray-400 hover:bg-gray-700 hover:text-white'
      }`}
    >
      <div className="text-gray-500" style={{ width: '16px', height: '16px' }}>{icon}</div>
      <span>{label}</span>
    </button>
  );
}

function DashboardTab({ stats, loading, onRefresh }: { stats: Stats | null; loading: boolean; onRefresh: () => void }) {
  if (loading && !stats) {
    return <div className="text-center py-12">Carregando...</div>;
  }

  if (!stats && !loading) {
    return <div className="text-center py-12">Erro ao carregar estatísticas</div>;
  }

  if (!stats) {
    return null;
  }

  // TypeScript guard - após os checks acima, stats não pode ser null
  const safeStats = stats;

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-2xl font-bold">Dashboard</h2>
          <p className="text-sm text-gray-400">Valores reais da operação</p>
        </div>
        <button 
          onClick={onRefresh} 
          disabled={loading}
          className="flex items-center gap-2 px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <RefreshCw size={18} className={loading ? 'animate-spin' : ''} /> 
          {loading ? 'Atualizando...' : 'Atualizar'}
        </button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
        <StatCard 
          title="DEPÓSITOS TOTAIS" 
          value={`R$ ${(safeStats.total_deposit_amount ?? 0).toFixed(2)}`} 
          subtitle={`${safeStats.total_deposits ?? 0} transações aprovadas`}
          icon={<ArrowDownCircle />} 
          accent="green"
        />
        <StatCard 
          title="SAQUES TOTAIS" 
          value={`R$ ${(safeStats.total_withdrawal_amount ?? 0).toFixed(2)}`} 
          subtitle={`${safeStats.total_withdrawals ?? 0} transações aprovadas`}
          icon={<ArrowUpCircle />} 
          accent="orange"
        />
        <StatCard 
          title="PRIMEIROS DEPÓSITOS" 
          value={safeStats.total_ftds ?? 0} 
          subtitle="Usuários que fizeram 1° depósito"
          icon={<TrendingUp />} 
          accent="orange"
        />
        <StatCard 
          title="USUÁRIOS" 
          value={safeStats.total_users ?? 0} 
          subtitle={`${safeStats.jogadores_com_saldo ?? 0} com saldo`}
          icon={<Users />} 
          accent="orange"
        />
        <StatCard 
          title="GGR GERADO" 
          value={`R$ ${(safeStats.ggr_gerado ?? safeStats.net_revenue ?? 0).toFixed(2)}`} 
          subtitle={`Taxa ${safeStats.ggr_taxa ?? 17}%`}
          icon={<TrendingUp />} 
          accent="green"
        />
      </div>
    </div>
  );
}

function StatCard({ title, value, subtitle, icon, accent = false }: { 
  title: string; 
  value: string | number; 
  subtitle?: string;
  icon: React.ReactNode; 
  accent?: boolean | string
}) {
  const accentClass = accent === 'green' 
    ? 'border-green-500 bg-green-500/10' 
    : accent === 'orange' 
    ? 'border-orange-500 bg-orange-500/10' 
    : accent === true
    ? 'border-emerald-500 bg-emerald-500/10'
    : 'border-gray-700';
  
  const textAccentClass = accent === 'green'
    ? 'text-green-400'
    : accent === 'orange'
    ? 'text-orange-400'
    : accent === true
    ? 'text-emerald-400'
    : 'text-gray-400';
  
  const iconAccentClass = accent === 'green'
    ? 'text-green-400'
    : accent === 'orange'
    ? 'text-orange-400'
    : accent === true
    ? 'text-emerald-400'
    : 'text-[#d4af37]';

  return (
    <div className={`rounded-lg p-4 border ${accentClass} bg-gray-800`}>
      <div className="flex items-center justify-between mb-2">
        <h3 className={`text-xs font-semibold uppercase ${textAccentClass}`}>{title}</h3>
        <div className={iconAccentClass}>{icon}</div>
      </div>
      <p className="text-xl font-bold mb-1">{value}</p>
      {subtitle && <p className="text-xs text-gray-500">{subtitle}</p>}
    </div>
  );
}

// ==========================
// TABS IMPLEMENTADAS
// ==========================

function UsersTab({ token }: { token: string }) {
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchUsers = async () => {
    setLoading(true); setError('');
    try {
      const res = await fetch(`${API_URL}/api/admin/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Falha ao carregar usuários');
      const data = await res.json();
      setUsers(data);
    } catch (err:any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchUsers(); }, []);

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold">Usuários</h2>
        <div className="flex gap-2">
          <button 
            onClick={async () => {
              try {
                const res = await fetch(`${API_URL}/api/admin/users/export/pdf`, {
                  headers: { Authorization: `Bearer ${token}` }
                });
                if (!res.ok) throw new Error('Falha ao exportar PDF');
                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `usuarios_${new Date().toISOString().split('T')[0]}.pdf`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
              } catch (err: any) {
                alert('Erro ao exportar PDF: ' + err.message);
              }
            }}
            className="flex items-center gap-2 px-3 py-2 bg-green-600 hover:bg-green-700 rounded"
          >
            <FileText size={18} /> Exportar PDF
          </button>
          <button onClick={fetchUsers} className="flex items-center gap-2 px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded">
            <RefreshCw size={18} /> Atualizar
          </button>
        </div>
      </div>
      {error && <div className="text-red-400 mb-3">{error}</div>}
      {loading ? <div>Carregando...</div> : (
        <div className="overflow-x-auto border border-gray-700 rounded-lg">
          <table className="w-full text-sm">
            <thead className="bg-gray-800">
              <tr>
                <th className="px-3 py-2 text-left">ID</th>
                <th className="px-3 py-2 text-left">Usuário</th>
                <th className="px-3 py-2 text-left">Email</th>
                <th className="px-3 py-2 text-left">Telefone</th>
                <th className="px-3 py-2 text-left">CPF</th>
                <th className="px-3 py-2 text-left">Saldo</th>
                <th className="px-3 py-2 text-left">Bônus</th>
                <th className="px-3 py-2 text-left">Status</th>
                <th className="px-3 py-2 text-left">Data Cadastro</th>
              </tr>
            </thead>
            <tbody>
              {users.map(u => (
                <tr key={u.id} className="border-t border-gray-800">
                  <td className="px-3 py-2">{u.id}</td>
                  <td className="px-3 py-2">{u.username}</td>
                  <td className="px-3 py-2">{u.email}</td>
                  <td className="px-3 py-2">{u.phone || '-'}</td>
                  <td className="px-3 py-2">{u.cpf || '-'}</td>
                  <td className="px-3 py-2">R$ {u.balance?.toFixed(2) || '0.00'}</td>
                  <td className="px-3 py-2">R$ {u.bonus_balance?.toFixed(2) || '0.00'}</td>
                  <td className="px-3 py-2">{u.is_active ? 'Ativo' : 'Inativo'}</td>
                  <td className="px-3 py-2">{u.created_at ? new Date(u.created_at).toLocaleDateString('pt-BR') : '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ========== TRANSACTIONS TAB (Depósitos e Saques Unificados) ==========
function TransactionsTab({ token }: { token: string }) {
  const [deposits, setDeposits] = useState<any[]>([]);
  const [withdrawals, setWithdrawals] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeType, setActiveType] = useState<'deposits' | 'withdrawals'>('deposits');

  const fetchDeposits = async () => {
    setLoading(true); setError('');
    try {
      const res = await fetch(`${API_URL}/api/admin/deposits`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Falha ao carregar depósitos');
      setDeposits(await res.json());
    } catch (err:any) { setError(err.message); }
    finally { setLoading(false); }
  };

  const fetchWithdrawals = async () => {
    setLoading(true); setError('');
    try {
      const res = await fetch(`${API_URL}/api/admin/withdrawals`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Falha ao carregar saques');
      setWithdrawals(await res.json());
    } catch (err:any) { setError(err.message); }
    finally { setLoading(false); }
  };

  const fetchAll = async () => {
    await Promise.all([fetchDeposits(), fetchWithdrawals()]);
  };

  useEffect(() => { fetchAll(); }, []);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Depósitos e Saques</h2>
        <button onClick={fetchAll} className="flex items-center gap-2 px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded">
          <RefreshCw size={18} /> Atualizar
        </button>
      </div>

      <div className="flex gap-2 border-b border-gray-700">
        <button
          onClick={() => setActiveType('deposits')}
          className={`px-4 py-2 font-semibold transition-colors ${
            activeType === 'deposits'
              ? 'border-b-2 border-green-500 text-green-400'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          Depósitos ({deposits.length})
        </button>
        <button
          onClick={() => setActiveType('withdrawals')}
          className={`px-4 py-2 font-semibold transition-colors ${
            activeType === 'withdrawals'
              ? 'border-b-2 border-orange-500 text-orange-400'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          Saques ({withdrawals.length})
        </button>
      </div>

      {error && (
        <div className="bg-red-500/20 border border-red-500 rounded-lg p-3 text-red-400 text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center py-12">Carregando...</div>
      ) : activeType === 'deposits' ? (
        <TabTable
          title=""
          loading={false}
          error=""
          onRefresh={fetchDeposits}
          columns={['ID', 'User', 'Valor', 'Status', 'Criado em']}
          rows={deposits.map(d => [
            d.id,
            d.user_id,
            `R$ ${d.amount?.toFixed(2)}`,
            d.status,
            new Date(d.created_at).toLocaleString('pt-BR')
          ])}
        />
      ) : (
        <TabTable
          title=""
          loading={false}
          error=""
          onRefresh={fetchWithdrawals}
          columns={['ID', 'User', 'Valor', 'Status', 'Criado em']}
          rows={withdrawals.map(w => [
            w.id,
            w.user_id,
            `R$ ${w.amount?.toFixed(2)}`,
            w.status,
            new Date(w.created_at).toLocaleString('pt-BR')
          ])}
        />
      )}
    </div>
  );
}


function GatewaysTab({ token }: { token: string }) {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [form, setForm] = useState({ 
    name: '', 
    type: 'pix', 
    is_active: true, 
    username: '',
    password: '',
    api_url: 'https://api.gatebox.com.br'
  });
  const [editingId, setEditingId] = useState<number | null>(null);

  const fetchData = async () => {
    setLoading(true); setError(''); setSuccess('');
    try {
      const res = await fetch(`${API_URL}/api/admin/gateways`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Falha ao carregar gateways');
      setItems(await res.json());
    } catch (err:any) { setError(err.message); }
    finally { setLoading(false); }
  };

  const resetForm = () => {
    setForm({ name: '', type: 'pix', is_active: true, username: '', password: '', api_url: 'https://api.gatebox.com.br' });
    setEditingId(null);
  };

  const prepareCredentials = () => {
    return JSON.stringify({
      username: form.username,
      password: form.password,
      api_url: form.api_url || 'https://api.gatebox.com.br'
    });
  };

  const create = async () => {
    setLoading(true); setError(''); setSuccess('');
    try {
      const credentials = prepareCredentials();
      const res = await fetch(`${API_URL}/api/admin/gateways`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          name: form.name,
          type: form.type,
          is_active: form.is_active,
          credentials: credentials
        })
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Falha ao criar gateway');
      }
      setSuccess('Gateway criado com sucesso!');
      resetForm();
      await fetchData();
    } catch (err:any) { 
      setError(err.message || 'Erro ao criar gateway');
    } finally { 
      setLoading(false); 
    }
  };

  const update = async (id: number) => {
    setLoading(true); setError(''); setSuccess('');
    try {
      const credentials = prepareCredentials();
      const res = await fetch(`${API_URL}/api/admin/gateways/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          name: form.name,
          type: form.type,
          is_active: form.is_active,
          credentials: credentials
        })
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Falha ao atualizar gateway');
      }
      setSuccess('Gateway atualizado com sucesso!');
      resetForm();
      await fetchData();
    } catch (err:any) { 
      setError(err.message || 'Erro ao atualizar gateway');
    } finally { 
      setLoading(false); 
    }
  };

  const loadForEdit = (gateway: any) => {
    setEditingId(gateway.id);
    setForm({
      name: gateway.name || '',
      type: gateway.type || 'pix',
      is_active: gateway.is_active ?? true,
      username: '',
      password: '',
      api_url: 'https://api.gatebox.com.br'
    });

    // Parse credentials se existir
    if (gateway.credentials) {
      try {
        const creds = JSON.parse(gateway.credentials);
        setForm(prev => ({
          ...prev,
          username: creds.username || '',
          password: creds.password || '',
          api_url: creds.api_url || 'https://api.gatebox.com.br'
        }));
      } catch (e) {
        // Se não for JSON, deixa vazio
      }
    }
  };

  useEffect(() => { fetchData(); }, []);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Gateways</h2>
        <button onClick={fetchData} className="flex items-center gap-2 px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded">
          <RefreshCw size={18} /> Atualizar
        </button>
      </div>

      {error && (
        <div className="bg-red-500/20 border border-red-500 rounded-lg p-3 text-red-400 text-sm">
          {error}
        </div>
      )}
      {success && (
        <div className="bg-green-500/20 border border-green-500 rounded-lg p-3 text-green-400 text-sm">
          {success}
        </div>
      )}

      {/* Formulário de criar/editar */}
      <div className="bg-gray-800/60 p-6 rounded-lg border border-gray-700">
        <h3 className="text-lg font-semibold mb-4">
          {editingId ? 'Editar Gateway' : 'Adicionar Novo Gateway'}
        </h3>
        
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Nome do Gateway</label>
            <input 
              className="w-full bg-gray-700 rounded px-3 py-2 text-sm border border-gray-600 focus:border-[#d4af37] focus:outline-none" 
              placeholder="Ex: Gatebox PIX"
              value={form.name} 
              onChange={e=>setForm({...form, name:e.target.value})}
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Tipo</label>
            <select 
              className="w-full bg-gray-700 rounded px-3 py-2 text-sm border border-gray-600 focus:border-[#d4af37] focus:outline-none"
              value={form.type} 
              onChange={e=>setForm({...form, type:e.target.value})}
            >
              <option value="pix">PIX</option>
              <option value="card">Cartão</option>
              <option value="boleto">Boleto</option>
            </select>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Username</label>
            <input 
              type="text"
              className="w-full bg-gray-700 rounded px-3 py-2 text-sm border border-gray-600 focus:border-[#d4af37] focus:outline-none" 
              placeholder="Username da Gatebox"
              value={form.username} 
              onChange={e=>setForm({...form, username:e.target.value})}
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Password</label>
            <input 
              type="password"
              className="w-full bg-gray-700 rounded px-3 py-2 text-sm border border-gray-600 focus:border-[#d4af37] focus:outline-none" 
              placeholder="Password da Gatebox"
              value={form.password} 
              onChange={e=>setForm({...form, password:e.target.value})}
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm text-gray-400 mb-1">API URL</label>
            <input 
              type="text"
              className="w-full bg-gray-700 rounded px-3 py-2 text-sm border border-gray-600 focus:border-[#d4af37] focus:outline-none" 
              placeholder="https://api.gatebox.com.br"
              value={form.api_url} 
              onChange={e=>setForm({...form, api_url:e.target.value})}
            />
            <p className="text-xs text-gray-500 mt-1">URL base da API Gatebox (padrão: https://api.gatebox.com.br)</p>
          </div>

          <div className="flex items-center gap-2">
            <input 
              type="checkbox" 
              checked={form.is_active} 
              onChange={e=>setForm({...form, is_active:e.target.checked})}
              className="w-4 h-4"
            />
            <label className="text-sm text-gray-300">Ativo</label>
          </div>

          <div className="md:col-span-2 flex gap-2">
            {editingId ? (
              <>
                <button 
                  onClick={() => update(editingId)} 
                  className="flex-1 bg-[#d4af37] hover:bg-[#ffd700] text-black py-2 rounded font-semibold transition-colors"
                >
                  Atualizar Gateway
                </button>
                <button 
                  onClick={resetForm} 
                  className="px-4 bg-gray-700 hover:bg-gray-600 text-white py-2 rounded font-semibold transition-colors"
                >
                  Cancelar
                </button>
              </>
            ) : (
              <button 
                onClick={create} 
                className="flex-1 bg-[#ff6b35] hover:bg-[#ff7b35] text-white py-2 rounded font-semibold transition-colors"
              >
                Criar Gateway
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Lista de gateways */}
      {loading && items.length === 0 && (
        <div className="text-center py-12 text-gray-400">
          <RefreshCw className="animate-spin mx-auto mb-2" size={24} />
          <p>Carregando gateways...</p>
        </div>
      )}

      {!loading && items.length === 0 && (
        <div className="text-center py-12 text-gray-500 border border-gray-700 rounded-lg bg-gray-800/30">
          <p className="text-lg mb-2">Nenhum gateway configurado</p>
          <p className="text-sm">Adicione um gateway acima para começar</p>
        </div>
      )}

      {items.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-300">Gateways Configurados</h3>
          <div className="grid md:grid-cols-2 gap-4">
            {items.map(g => {
              let credentials = null;
              try {
                if (g.credentials) {
                  credentials = JSON.parse(g.credentials);
                }
              } catch (e) {
                // Não é JSON
              }

              return (
                <div key={g.id} className="relative p-5 rounded-lg border border-gray-700 bg-gradient-to-br from-gray-800/80 to-gray-900/80 hover:border-[#d4af37]/50 transition-all duration-200">
                  {/* Badge de status */}
                  <div className="absolute top-4 right-4">
                    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                      g.is_active 
                        ? 'bg-green-500/20 text-green-400 border border-green-500/30' 
                        : 'bg-red-500/20 text-red-400 border border-red-500/30'
                    }`}>
                      {g.is_active ? 'Ativo' : 'Inativo'}
                    </span>
                  </div>

                  {/* Header */}
                  <div className="mb-4 pr-16">
                    <div className="flex items-center gap-3 mb-2">
                      <div className="w-10 h-10 rounded-lg bg-[#d4af37]/20 flex items-center justify-center border border-[#d4af37]/30">
                        <Activity size={20} className="text-[#d4af37]" />
                      </div>
                      <div>
                        <h4 className="font-bold text-lg text-white">{g.name}</h4>
                        <p className="text-xs text-gray-400 uppercase tracking-wide">{g.type}</p>
                      </div>
                    </div>
                  </div>

                  {/* Credenciais */}
                  {credentials && (
                    <div className="space-y-3 pt-4 border-t border-gray-700/50">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-400">Client ID</span>
                        <span className="text-white font-mono text-xs bg-gray-900/50 px-2 py-1 rounded">
                          {credentials.client_id || credentials.ci || '—'}
                        </span>
                      </div>
                      
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-400">Client Secret</span>
                        <span className="text-white font-mono text-xs bg-gray-900/50 px-2 py-1 rounded">
                          {credentials.client_secret || credentials.cs ? '••••••••••••' : '—'}
                        </span>
                      </div>
                      
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-400">Ambiente</span>
                        <span className={`font-semibold text-xs px-2 py-1 rounded ${
                          credentials.sandbox 
                            ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' 
                            : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                        }`}>
                          {credentials.sandbox ? 'Sandbox' : 'Produção'}
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Botão de ação */}
                  <div className="mt-4 pt-4 border-t border-gray-700/50">
                    <button
                      onClick={() => loadForEdit(g)}
                      className="w-full px-4 py-2 bg-[#d4af37]/10 hover:bg-[#d4af37]/20 text-[#d4af37] rounded-lg text-sm font-semibold transition-all duration-200 border border-[#d4af37]/30 hover:border-[#d4af37]/50"
                    >
                      Editar Gateway
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

function IGameWinTab({ token }: { token: string }) {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [form, setForm] = useState({ agent_code: '', agent_key: '', api_url: 'https://api.igamewin.com', credentials: '', rtp: 96.0, is_active: true });
  const [editingId, setEditingId] = useState<number | null>(null);
  const [games, setGames] = useState<any[]>([]);
  const [providers, setProviders] = useState<any[]>([]);
  const [providerCode, setProviderCode] = useState('');
  const [loadingGames, setLoadingGames] = useState(false);
  const [gamesError, setGamesError] = useState('');
  const [agentBalance, setAgentBalance] = useState<number | null>(null);
  const [loadingBalance, setLoadingBalance] = useState(false);
  const [balanceError, setBalanceError] = useState('');

  const fetchData = async () => {
    setLoading(true); setError('');
    try {
      const res = await fetch(`${API_URL}/api/admin/igamewin-agents`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Falha ao carregar agentes');
      setItems(await res.json());
    } catch (err:any) { setError(err.message); }
    finally { setLoading(false); }
  };

  const fetchGames = async (provider?: string) => {
    setLoadingGames(true); setGamesError('');
    try {
      const query = provider || providerCode ? `?provider_code=${encodeURIComponent(provider || providerCode)}` : '';
      const res = await fetch(`${API_URL}/api/admin/igamewin/games${query}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Falha ao carregar jogos/provedores');
      const data = await res.json();
      setProviders(data.providers || []);
      if (!providerCode && !provider && data.providers?.length) {
        const first = data.providers[0];
        const code = first.code || first.provider_code || '';
        setProviderCode(code);
      }
      if (data.provider_code) {
        setProviderCode(data.provider_code);
      }
      setGames(data.games || []);
    } catch (err:any) { setGamesError(err.message); }
    finally { setLoadingGames(false); }
  };

  const fetchAgentBalance = async () => {
    setLoadingBalance(true); setBalanceError('');
    try {
      const res = await fetch(`${API_URL}/api/admin/igamewin/agent-balance`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Falha ao carregar saldo do agente');
      }
      const data = await res.json();
      setAgentBalance(data.balance);
    } catch (err:any) { 
      setBalanceError(err.message);
      setAgentBalance(null);
    }
    finally { setLoadingBalance(false); }
  };
  const resetForm = () => {
    setForm({ agent_code: '', agent_key: '', api_url: 'https://api.igamewin.com', credentials: '', rtp: 96.0, is_active: true });
    setEditingId(null);
  };

  const loadForEdit = (agent: any) => {
    setEditingId(agent.id);
    setForm({
      agent_code: agent.agent_code || '',
      agent_key: agent.agent_key || '',
      api_url: agent.api_url || 'https://api.igamewin.com',
      credentials: agent.credentials || '',
      rtp: agent.rtp !== undefined ? agent.rtp : 96.0,
      is_active: agent.is_active !== undefined ? agent.is_active : true
    });
  };

  const createOrUpdate = async () => {
    setLoading(true); setError('');
    try {
      const url = editingId
        ? `${API_URL}/api/admin/igamewin-agents/${editingId}`
        : `${API_URL}/api/admin/igamewin-agents`;
      const method = editingId ? 'PUT' : 'POST';
      
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(form)
      });
      
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`Falha ao ${editingId ? 'atualizar' : 'criar'} agente: ${txt || res.status}`);
      }
      
      await fetchData();
      await fetchGames();
      resetForm();
    } catch (err:any) { 
      setError(err.message); 
    } finally { 
      setLoading(false); 
    }
  };

  useEffect(() => { 
    fetchData(); 
    fetchGames(); 
    fetchAgentBalance();
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">IGameWin</h2>
        <div className="flex items-center gap-2">
          <button onClick={fetchData} className="flex items-center gap-2 px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded">
            <RefreshCw size={18} /> Atualizar agente
          </button>
          <button onClick={() => fetchGames()} className="flex items-center gap-2 px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded">
            <RefreshCw size={18} /> Atualizar jogos
          </button>
        </div>
      </div>
      {error && <div className="text-red-400">{error}</div>}
      {gamesError && <div className="text-red-400">{gamesError}</div>}
      {loading && <div className="text-sm text-gray-400">Carregando agente...</div>}

      {/* Saldo do Agente */}
      {items.length > 0 && items[0].is_active && (
        <div className="bg-gradient-to-br from-gray-800/80 to-gray-900/80 p-5 rounded-lg border border-gray-700">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-lg font-semibold text-white">Saldo do Agente IGameWin</h3>
              <p className="text-sm text-gray-400 mt-1">Saldo disponível para transações com usuários</p>
            </div>
            <button 
              onClick={fetchAgentBalance}
              disabled={loadingBalance}
              className="flex items-center gap-2 px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded disabled:opacity-50"
            >
              <RefreshCw size={18} className={loadingBalance ? 'animate-spin' : ''} /> Atualizar
            </button>
          </div>

          {loadingBalance ? (
            <div className="text-center py-4 text-gray-400">
              <RefreshCw className="animate-spin mx-auto mb-2" size={24} />
              <p>Consultando saldo...</p>
            </div>
          ) : balanceError ? (
            <div className="bg-red-500/20 border border-red-500 rounded-lg p-3 text-red-400 text-sm">
              {balanceError}
            </div>
          ) : agentBalance !== null ? (
            <div className="space-y-3">
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-[#d4af37]">
                  {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(agentBalance)}
                </span>
                <span className="text-sm text-gray-400">BRL</span>
              </div>
              <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3 mt-3">
                <div className="flex items-start gap-2">
                  <Activity size={18} className="text-yellow-400 mt-0.5 flex-shrink-0" />
                  <div className="text-sm text-yellow-200">
                    <p className="font-semibold mb-1">Importante:</p>
                    <p>A API da IGameWin não permite adicionar saldo ao agente diretamente. Para adicionar saldo ao agente, é necessário acessar o painel administrativo da IGameWin.</p>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-4 text-gray-400">
              <p>Clique em "Atualizar" para consultar o saldo do agente</p>
            </div>
          )}
        </div>
      )}

      <div className="bg-gray-800/60 p-4 rounded border border-gray-700">
        <h3 className="text-lg font-semibold mb-4">{editingId ? 'Editar' : 'Cadastrar Novo'} Agente</h3>
        <div className="grid md:grid-cols-2 gap-3">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Agent Code *</label>
            <input 
              className="bg-gray-700 rounded px-3 py-2 text-sm w-full" 
              placeholder="Agent Code" 
              value={form.agent_code} 
              onChange={e=>setForm({...form, agent_code:e.target.value})}
              disabled={!!editingId}
            />
            {editingId && <p className="text-xs text-gray-500 mt-1">Agent Code não pode ser alterado</p>}
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Agent Key *</label>
            <input 
              type="password"
              className="bg-gray-700 rounded px-3 py-2 text-sm w-full" 
              placeholder="Agent Key" 
              value={form.agent_key} 
              onChange={e=>setForm({...form, agent_key:e.target.value})}
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm text-gray-400 mb-1">API URL *</label>
            <input 
              className="bg-gray-700 rounded px-3 py-2 text-sm w-full" 
              placeholder="API URL" 
              value={form.api_url} 
              onChange={e=>setForm({...form, api_url:e.target.value})}
            />
            <p className="text-xs text-gray-500 mt-1">Exemplo: https://api.igamewin.com</p>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">RTP (%)</label>
            <input 
              type="number"
              step="0.01"
              min="0"
              max="100"
              className="bg-gray-700 rounded px-3 py-2 text-sm w-full" 
              placeholder="96.0" 
              value={form.rtp} 
              onChange={e=>setForm({...form, rtp: parseFloat(e.target.value) || 96.0})}
            />
            <p className="text-xs text-gray-500 mt-1">Return to Player - Percentual de retorno (padrão: 96%)</p>
          </div>
          <div className="flex items-center gap-2">
            <input 
              type="checkbox" 
              checked={form.is_active} 
              onChange={e=>setForm({...form, is_active:e.target.checked})}
              id="is_active"
            />
            <label htmlFor="is_active" className="text-sm">Ativo</label>
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm text-gray-400 mb-1">Credenciais extras (JSON)</label>
            <textarea 
              className="bg-gray-700 rounded px-3 py-2 text-sm w-full min-h-[100px]" 
              placeholder='{"agent_secret": "seu_secret_aqui", "provider_code": "default_provider"}' 
              value={form.credentials} 
              onChange={e=>setForm({...form, credentials:e.target.value})}
            />
            <p className="text-xs text-gray-500 mt-1">JSON opcional com configurações extras (agent_secret, provider_code, etc)</p>
          </div>
          <div className="flex gap-2 md:col-span-2">
            <button 
              onClick={createOrUpdate} 
              disabled={loading || !form.agent_code || !form.agent_key || !form.api_url}
              className="flex-1 bg-[#ff6b35] hover:bg-[#ff7b35] text-white py-2 rounded font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Salvando...' : editingId ? 'Atualizar Agente' : 'Cadastrar Agente'}
            </button>
            {editingId && (
              <button 
                onClick={resetForm}
                className="px-4 bg-gray-700 hover:bg-gray-600 text-white py-2 rounded font-semibold"
              >
                Cancelar
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="space-y-3">
        <h3 className="text-lg font-semibold">Agentes Cadastrados</h3>
        {items.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            <p>Nenhum agente cadastrado</p>
            <p className="text-sm mt-2">Preencha o formulário acima para cadastrar um agente</p>
          </div>
        ) : (
          <div className="grid gap-3">
            {items.map(a => (
              <div key={a.id} className="p-4 rounded border border-gray-700 bg-gray-800/50">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="font-bold text-lg mb-2">ID: {a.id}</div>
                    <div className="text-sm text-gray-400 mb-1">Agent Code: <span className="text-white font-mono">{a.agent_code}</span></div>
                    <div className="text-sm text-gray-400 mb-1">API: <span className="text-white">{a.api_url}</span></div>
                    <div className="text-sm text-gray-400 mb-1">
                      RTP: <span className="text-white font-semibold">{a.rtp !== undefined ? `${a.rtp}%` : '96.0%'}</span>
                    </div>
                    <div className="text-sm text-gray-400 mb-1">
                      Status: <span className={a.is_active ? 'text-green-400 font-semibold' : 'text-red-400 font-semibold'}>{a.is_active ? 'Ativo' : 'Inativo'}</span>
                    </div>
                    {a.credentials && (
                      <div className="text-xs text-gray-500 break-all mt-2 p-2 bg-gray-900/50 rounded">
                        <span className="text-gray-400">Credenciais:</span> {a.credentials}
                      </div>
                    )}
                  </div>
                  <div className="flex gap-2 ml-4">
                    <button
                      onClick={() => loadForEdit(a)}
                      className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded"
                    >
                      Editar
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="space-y-3 mt-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-bold">Provedores ativos</h3>
            <p className="text-sm text-gray-400">Dados vindos do IGameWin</p>
          </div>
          <span className="text-sm text-gray-300 bg-gray-800 px-3 py-1 rounded">Total: {providers.length}</span>
        </div>
        {loadingGames ? <div>Carregando provedores...</div> : (
          <div className="space-y-2">
            {providers.length === 0 && <span className="text-gray-400 text-sm">Nenhum provedor retornado.</span>}
            {providers.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {providers.map((p) => {
                  const code = p.code || p.provider_code || p.name || '';
                  const name = p.name || p.code || p.provider_code || '—';
                  const status = p.status === 1 ? 'Ativo' : 'Manutenção';
                  const active = providerCode === code;
                  return (
                    <button
                      key={code || name}
                      onClick={() => { setProviderCode(code); fetchGames(code); }}
                      className={`px-3 py-1 border rounded text-sm ${active ? 'bg-[#ff6b35] border-[#ff6b35] text-white' : 'bg-gray-800 border-gray-700 text-gray-100'}`}
                    >
                      {name} <span className="text-xs opacity-70">({status})</span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="space-y-3 mt-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-bold">Jogos ativos</h3>
            <p className="text-sm text-gray-400">Lista filtrada por status ativo</p>
          </div>
          <span className="text-sm text-gray-300 bg-gray-800 px-3 py-1 rounded">
            Total: {games.filter((g)=> g.status === 1 || g.status === true || String(g.status).toLowerCase() === 'active').length}
          </span>
        </div>
        {loadingGames ? <div>Carregando jogos...</div> : (
          <div className="overflow-x-auto border border-gray-700 rounded-lg">
            <table className="w-full text-sm">
              <thead className="bg-gray-800">
                <tr>
                  <th className="px-3 py-2 text-left">Banner</th>
                  <th className="px-3 py-2 text-left">Nome</th>
                  <th className="px-3 py-2 text-left">Provedor</th>
                  <th className="px-3 py-2 text-left">Código</th>
                  <th className="px-3 py-2 text-left">Status</th>
                </tr>
              </thead>
              <tbody>
                {games
                  .filter((g) => g.status === 1 || g.status === true || String(g.status).toLowerCase() === 'active')
                  .map((g, idx) => (
                    <tr key={g.id ?? g.game_code ?? g.code ?? idx} className="border-t border-gray-800">
                      <td className="px-3 py-2">
                        {g.banner || g.image || g.icon ? (
                          <img src={g.banner || g.image || g.icon} alt={g.game_name || g.name || g.title || g.gameTitle || '—'} className="w-16 h-10 object-cover rounded border border-gray-700" />
                        ) : (
                          <span className="text-xs text-gray-500">—</span>
                        )}
                      </td>
                      <td className="px-3 py-2">{g.game_name || g.name || g.title || g.gameTitle || '—'}</td>
                      <td className="px-3 py-2">{g.provider_code || g.provider || g.provider_name || g.vendor || g.vendor_name || providerCode || '—'}</td>
                      <td className="px-3 py-2">{g.game_code || g.code || g.game_id || g.id || g.slug || '—'}</td>
                      <td className="px-3 py-2 capitalize">ativo</td>
                    </tr>
                  ))}
                {games.filter((g)=> g.status === 1 || g.status === true || String(g.status).toLowerCase() === 'active').length === 0 && !loadingGames && (
                  <tr><td className="px-3 py-3 text-gray-400" colSpan={5}>Nenhum jogo retornado.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function SettingsTab({ token }: { token: string }) {
  const [form, setForm] = useState({ min_amount: 0, max_amount: 0, min_withdrawal: 0, is_active: true });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true); setError('');
    try {
      const res = await fetch(`${API_URL}/api/admin/ftd-settings`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Falha ao carregar configurações');
      const data = await res.json();
      setForm({ 
        min_amount: data.min_amount ?? 0,
        max_amount: data.max_amount ?? 0,
        min_withdrawal: data.min_withdrawal ?? 0,
        is_active: data.is_active 
      });
    } catch (err:any) { setError(err.message); } finally { setLoading(false); }
  };
  const save = async () => {
    setLoading(true); setError('');
    try {
      const res = await fetch(`${API_URL}/api/admin/ftd-settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(form)
      });
      if (!res.ok) throw new Error('Falha ao salvar configurações');
      await load();
    } catch (err:any) { setError(err.message); } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Configurações (FTD)</h2>
      {error && <div className="text-red-400">{error}</div>}
      {loading && <div className="text-sm text-gray-400">Carregando...</div>}
      <div className="grid md:grid-cols-2 gap-3 bg-gray-800/60 p-4 rounded border border-gray-700">
        <div>
          <label className="text-sm text-gray-300">Depósito mínimo</label>
          <input type="number" step="0.01" className="w-full bg-gray-700 rounded px-3 py-2" value={form.min_amount} onChange={e=>setForm({...form, min_amount:Number(e.target.value)})}/>
        </div>
        <div>
          <label className="text-sm text-gray-300">Depósito máximo (0 = sem limite)</label>
          <input type="number" step="0.01" className="w-full bg-gray-700 rounded px-3 py-2" value={form.max_amount} onChange={e=>setForm({...form, max_amount:Number(e.target.value)})}/>
        </div>
        <div>
          <label className="text-sm text-gray-300">Saque mínimo</label>
          <input type="number" step="0.01" className="w-full bg-gray-700 rounded px-3 py-2" value={form.min_withdrawal} onChange={e=>setForm({...form, min_withdrawal:Number(e.target.value)})}/>
        </div>
        <div className="flex items-center gap-2">
          <input type="checkbox" checked={form.is_active} onChange={e=>setForm({...form, is_active:e.target.checked})}/>
          <span>Ativo</span>
        </div>
        <button onClick={save} className="md:col-span-2 bg-[#ff6b35] hover:bg-[#ff7b35] text-white py-2 rounded font-semibold">Salvar</button>
      </div>
    </div>
  );
}

function BrandingTab({ token }: { token: string }) {
  const [logos, setLogos] = useState<Array<{ id: number; url: string; is_active: boolean; created_at: string }>>([]);
  const [banners, setBanners] = useState<Array<{ id: number; url: string; position: number; is_active: boolean }>>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const fetchAssets = async () => {
    setLoading(true);
    try {
      const [logoRes, bannersRes] = await Promise.all([
        fetch(`${API_URL}/api/admin/media/list?media_type=logo`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        fetch(`${API_URL}/api/admin/media/list?media_type=banner`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      
      if (logoRes.ok) {
        const logosData = await logoRes.json();
        setLogos(logosData.sort((a: any, b: any) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()));
      }
      
      if (bannersRes.ok) {
        const bannersData = await bannersRes.json();
        setBanners(bannersData.sort((a: any, b: any) => a.position - b.position));
      }
    } catch (err) {
      console.error('Erro ao buscar assets:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssets();
  }, []);

  const handleLogoUpload = async (file?: File | null) => {
    if (!file) return;
    setLoading(true);
    setMessage('');
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('media_type', 'logo');
      
      const res = await fetch(`${API_URL}/api/admin/media/upload`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData
      });
      
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Erro ao fazer upload');
      }
      
      await fetchAssets();
      setMessage('Logo enviado e aplicado em tempo real.');
    } catch (err: any) {
      setMessage(err.message || 'Erro ao fazer upload do logo.');
    } finally {
      setLoading(false);
    }
  };

  const handleBannerUpload = async (fileList: FileList | null) => {
    if (!fileList || fileList.length === 0) return;
    setLoading(true);
    setMessage('');
    try {
      const uploads = Array.from(fileList).map(async (file) => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('media_type', 'banner');
        
        const res = await fetch(`${API_URL}/api/admin/media/upload`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
          body: formData
        });
        
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || 'Erro ao fazer upload');
        }
        
        return await res.json();
      });
      
      await Promise.all(uploads);
      await fetchAssets();
      setMessage('Banners adicionados e aplicados em tempo real.');
    } catch (err: any) {
      setMessage(err.message || 'Erro ao fazer upload dos banners.');
    } finally {
      setLoading(false);
    }
  };

  const removeLogo = async (id: number) => {
    setLoading(true);
    setMessage('');
    try {
      const res = await fetch(`${API_URL}/api/admin/media/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (!res.ok) throw new Error('Erro ao remover logo');
      
      await fetchAssets();
      setMessage('Logo removido.');
    } catch (err: any) {
      setMessage(err.message || 'Erro ao remover logo.');
    } finally {
      setLoading(false);
    }
  };

  const removeBanner = async (id: number) => {
    setLoading(true);
    setMessage('');
    try {
      const res = await fetch(`${API_URL}/api/admin/media/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (!res.ok) throw new Error('Erro ao remover banner');
      
      await fetchAssets();
      setMessage('Banner removido.');
    } catch (err: any) {
      setMessage(err.message || 'Erro ao remover banner.');
    } finally {
      setLoading(false);
    }
  };

  const toggleActive = async (id: number) => {
    setLoading(true);
    setMessage('');
    try {
      const res = await fetch(`${API_URL}/api/admin/media/${id}/toggle-active`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (!res.ok) throw new Error('Erro ao alterar status');
      
      await fetchAssets();
      setMessage('Status atualizado.');
    } catch (err: any) {
      setMessage(err.message || 'Erro ao alterar status.');
    } finally {
      setLoading(false);
    }
  };

  const moveBanner = async (id: number, direction: 'up' | 'down') => {
    const index = banners.findIndex(b => b.id === id);
    if (index === -1) return;
    
    const newPosition = direction === 'up' ? index - 1 : index + 1;
    if (newPosition < 0 || newPosition >= banners.length) return;

    setLoading(true);
    setMessage('');
    try {
      const targetBanner = banners[newPosition];
      const currentBanner = banners[index];
      
      // Trocar posições
      const formData1 = new FormData();
      formData1.append('position', newPosition.toString());
      
      const formData2 = new FormData();
      formData2.append('position', index.toString());

      await Promise.all([
        fetch(`${API_URL}/api/admin/media/${currentBanner.id}/position`, {
          method: 'PUT',
          headers: { Authorization: `Bearer ${token}` },
          body: formData1
        }),
        fetch(`${API_URL}/api/admin/media/${targetBanner.id}/position`, {
          method: 'PUT',
          headers: { Authorization: `Bearer ${token}` },
          body: formData2
        })
      ]);
      
      await fetchAssets();
      setMessage('Ordem atualizada.');
    } catch (err: any) {
      setMessage(err.message || 'Erro ao reordenar.');
    } finally {
      setLoading(false);
    }
  };

  const getImageUrl = (url: string) => {
    return url.startsWith('/api') ? `${API_URL}${url}` : `${API_URL}/api/public/media${url}`;
  };

  // Drag and drop handlers
  const [dragActive, setDragActive] = useState(false);
  const [dragBannerActive, setDragBannerActive] = useState(false);

  const handleDrag = (e: React.DragEvent, type: 'logo' | 'banner') => {
    e.preventDefault();
    e.stopPropagation();
    if (type === 'logo') setDragActive(true);
    else setDragBannerActive(true);
  };

  const handleDragLeave = (e: React.DragEvent, type: 'logo' | 'banner') => {
    e.preventDefault();
    e.stopPropagation();
    if (type === 'logo') setDragActive(false);
    else setDragBannerActive(false);
  };

  const handleDrop = (e: React.DragEvent, type: 'logo' | 'banner') => {
    e.preventDefault();
    e.stopPropagation();
    if (type === 'logo') setDragActive(false);
    else setDragBannerActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      if (type === 'logo') {
        handleLogoUpload(e.dataTransfer.files[0]);
      } else {
        handleBannerUpload(e.dataTransfer.files);
      }
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Branding</h2>
          <p className="text-sm text-gray-400">Gerencie logos e banners da plataforma.</p>
        </div>
      </div>
      {message && <div className={`text-sm ${message.includes('Erro') ? 'text-red-400' : 'text-emerald-400'}`}>{message}</div>}
      {loading && <div className="text-sm text-gray-400">Carregando...</div>}

      <div className="grid md:grid-cols-2 gap-4">
        {/* Logo Section */}
        <div className="bg-gray-800/60 p-4 rounded border border-gray-700 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold">Logo</h3>
          </div>
          
          {/* Drag & Drop Area */}
          <div
            onDragEnter={(e) => handleDrag(e, 'logo')}
            onDragLeave={(e) => handleDragLeave(e, 'logo')}
            onDragOver={(e) => handleDrag(e, 'logo')}
            onDrop={(e) => handleDrop(e, 'logo')}
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              dragActive 
                ? 'border-emerald-500 bg-emerald-500/10' 
                : 'border-gray-600 hover:border-gray-500'
            }`}
          >
            <input
              type="file"
              accept="image/*"
              onChange={(e) => handleLogoUpload(e.target.files?.[0])}
              className="hidden"
              id="logo-upload"
              disabled={loading}
            />
            <label htmlFor="logo-upload" className="cursor-pointer">
              <div className="space-y-2">
                <div className="text-sm text-gray-300">
                  Arraste e solte os arquivos ou <span className="text-emerald-400 underline">Clique aqui</span>
                </div>
                <div className="text-xs text-gray-500">
                  Recomendado: 200x60px | Formatos: PNG, JPG, SVG | Opcional
                </div>
              </div>
            </label>
          </div>
          
          {logos.length > 0 && (
            <div className="space-y-2">
              {logos.map((logo) => (
                <div key={logo.id} className={`p-2 rounded border ${logo.is_active ? 'border-emerald-500 bg-emerald-500/10' : 'border-gray-700 bg-gray-900'}`}>
                  <div className="flex items-center gap-2 mb-2">
                    <img src={getImageUrl(logo.url)} alt="Logo" className="max-h-16 object-contain" />
                    <div className="flex-1">
                      <div className="text-xs text-gray-400">
                        {logo.is_active ? '[Ativo]' : '[Inativo]'}
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => toggleActive(logo.id)}
                      className={`text-xs px-2 py-1 rounded ${logo.is_active ? 'bg-gray-700 hover:bg-gray-600' : 'bg-emerald-600 hover:bg-emerald-700'}`}
                      disabled={loading}
                    >
                      {logo.is_active ? 'Desativar' : 'Ativar'}
                    </button>
                    <button
                      onClick={() => removeLogo(logo.id)}
                      className="text-xs px-2 py-1 rounded bg-red-600/60 hover:bg-red-600/80"
                      disabled={loading}
                    >
                      Remover
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Banner Section */}
        <div className="bg-gray-800/60 p-4 rounded border border-gray-700 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold">Banners</h3>
          </div>
          
          {/* Drag & Drop Area */}
          <div
            onDragEnter={(e) => handleDrag(e, 'banner')}
            onDragLeave={(e) => handleDragLeave(e, 'banner')}
            onDragOver={(e) => handleDrag(e, 'banner')}
            onDrop={(e) => handleDrop(e, 'banner')}
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              dragBannerActive 
                ? 'border-emerald-500 bg-emerald-500/10' 
                : 'border-gray-600 hover:border-gray-500'
            }`}
          >
            <input
              type="file"
              accept="image/*"
              multiple
              onChange={(e) => handleBannerUpload(e.target.files)}
              className="hidden"
              id="banner-upload"
              disabled={loading}
            />
            <label htmlFor="banner-upload" className="cursor-pointer">
              <div className="space-y-2">
                <div className="text-sm text-gray-300">
                  Arraste e solte os arquivos ou <span className="text-emerald-400 underline">Clique aqui</span>
                </div>
                <div className="text-xs text-gray-500">
                  Múltiplos arquivos para carrossel | Formatos: PNG, JPG
                </div>
              </div>
            </label>
          </div>
          
          {banners.length > 0 && (
            <div className="space-y-2">
              {banners.map((banner, index) => (
                <div key={banner.id} className={`p-2 rounded border ${banner.is_active ? 'border-emerald-500 bg-emerald-500/10' : 'border-gray-700 bg-gray-900'}`}>
                  <div className="flex items-center gap-2 mb-2">
                    <img src={getImageUrl(banner.url)} alt={`Banner ${banner.id}`} className="max-h-20 w-full object-cover rounded" />
                  </div>
                  <div className="flex items-center justify-between gap-2">
                    <div className="text-xs text-gray-400">
                      Posição: {index + 1} {banner.is_active ? '| [Ativo]' : '| [Inativo]'}
                    </div>
                    <div className="flex gap-1">
                      <button
                        onClick={() => moveBanner(banner.id, 'up')}
                        disabled={loading || index === 0}
                        className="text-xs px-2 py-1 rounded bg-gray-700 hover:bg-gray-600 disabled:opacity-30"
                        title="Mover para cima"
                      >
                        ^
                      </button>
                      <button
                        onClick={() => moveBanner(banner.id, 'down')}
                        disabled={loading || index === banners.length - 1}
                        className="text-xs px-2 py-1 rounded bg-gray-700 hover:bg-gray-600 disabled:opacity-30"
                        title="Mover para baixo"
                      >
                        v
                      </button>
                      <button
                        onClick={() => toggleActive(banner.id)}
                        className={`text-xs px-2 py-1 rounded ${banner.is_active ? 'bg-gray-700 hover:bg-gray-600' : 'bg-emerald-600 hover:bg-emerald-700'}`}
                        disabled={loading}
                      >
                        {banner.is_active ? 'ON' : 'OFF'}
                      </button>
                      <button
                        onClick={() => removeBanner(banner.id)}
                        className="text-xs px-2 py-1 rounded bg-red-600/60 hover:bg-red-600/80"
                        disabled={loading}
                      >
                        ✕
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ThemesTab({ token }: { token: string }) {
  const [themes, setThemes] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [form, setForm] = useState({
    name: 'Novo tema',
    is_default: false,
    is_active: true,
    bg: '#0a0e0f',
    surface: '#0d1415',
    card: '#0f1b1d',
    accent: '#d4af37',
    accentSoft: '#0f6f5a',
    text: '#ffffff',
    muted: '#cbd5e1'
  });
  const [editingId, setEditingId] = useState<number | null>(null);

  const fetchThemes = async () => {
    setLoading(true); setError('');
    try {
      const res = await fetch(`${API_URL}/api/admin/themes`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Falha ao carregar temas');
      const data = await res.json();
      setThemes(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const saveTheme = async () => {
    setLoading(true); setError('');
    try {
      const colors = {
        bg: form.bg,
        surface: form.surface,
        card: form.card,
        accent: form.accent,
        accentSoft: form.accentSoft,
        text: form.text,
        muted: form.muted
      };

      const url = editingId
        ? `${API_URL}/api/admin/themes/${editingId}`
        : `${API_URL}/api/admin/themes`;
      const method = editingId ? 'PUT' : 'POST';
      
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          name: form.name,
          is_default: form.is_default,
          is_active: form.is_active,
          colors_json: JSON.stringify(colors)
        })
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Falha ao salvar');
      }
      
      const savedTheme = await res.json();
      
      // Se foi marcado como padrão, aplicar automaticamente
      if (form.is_default) {
        const themeColors = JSON.parse(savedTheme.colors_json);
        applyThemeToDocument({
          id: String(savedTheme.id),
          name: savedTheme.name,
          ...themeColors
        } as ThemePalette);
      }
      
      await fetchThemes();
      setForm({ name: 'Novo tema', is_default: false, is_active: true, bg: '#0a0e0f', surface: '#0d1415', card: '#0f1b1d', accent: '#d4af37', accentSoft: '#0f6f5a', text: '#ffffff', muted: '#cbd5e1' });
      setEditingId(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const applyTheme = async (theme: any) => {
    try {
      setLoading(true);
      // Marcar como padrão e aplicar
      const colors = JSON.parse(theme.colors_json);
      applyThemeToDocument({
        id: String(theme.id),
        name: theme.name,
        ...colors
      } as ThemePalette);
      
      // Atualizar tema para ser padrão
      await fetch(`${API_URL}/api/admin/themes/${theme.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ is_default: true, is_active: true })
      });
      await fetchThemes();
    } catch (err: any) {
      setError(err.message || 'Erro ao aplicar tema');
    } finally {
      setLoading(false);
    }
  };

  const deleteTheme = async (id: number) => {
    if (!confirm('Deletar este tema?')) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/themes/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Falha ao deletar');
      await fetchThemes();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadForEdit = (theme: any) => {
    setEditingId(theme.id);
    const colors = JSON.parse(theme.colors_json);
    setForm({
      name: theme.name,
      is_default: theme.is_default,
      is_active: theme.is_active,
      ...colors
    });
  };

  const createNewTheme = () => {
    setEditingId(null);
    setForm({
      name: 'Novo tema',
      is_default: false,
      is_active: true,
      bg: '#0a0e0f',
      surface: '#0d1415',
      card: '#0f1b1d',
      accent: '#d4af37',
      accentSoft: '#0f6f5a',
      text: '#ffffff',
      muted: '#cbd5e1'
    });
  };

  // Aplicar tema em tempo real quando as cores mudarem
  useEffect(() => {
    if (form.bg && form.surface && form.card && form.accent && form.accentSoft && form.text && form.muted) {
      applyThemeToDocument({
        id: editingId ? String(editingId) : 'preview',
        name: form.name || 'Preview',
        bg: form.bg,
        surface: form.surface,
        card: form.card,
        accent: form.accent,
        accentSoft: form.accentSoft,
        text: form.text,
        muted: form.muted
      } as ThemePalette);
    }
  }, [form.bg, form.surface, form.card, form.accent, form.accentSoft, form.text, form.muted, editingId, form.name]);

  useEffect(() => {
    fetchThemes();
    // Carregar tema ativo ao iniciar
    fetch(`${API_URL}/api/admin/themes/active`)
      .then(res => {
        if (res.ok) {
          return res.json();
        }
        return null;
      })
      .then(theme => {
        if (theme && theme.colors_json) {
          const colors = JSON.parse(theme.colors_json);
          applyThemeToDocument({
            id: String(theme.id),
            name: theme.name,
            ...colors
          } as ThemePalette);
        }
      })
      .catch(err => console.error('Erro ao carregar tema ativo:', err));
  }, []);

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-2xl font-bold">Temas</h2>
        <p className="text-sm text-gray-400">Crie e aplique temas em tempo real. As cores refletem imediatamente na plataforma.</p>
      </div>

      {error && <div className="text-red-400">{error}</div>}

      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Gerenciar Temas</h3>
        <button 
          onClick={createNewTheme}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-semibold"
        >
          + Novo Tema
        </button>
      </div>

      <div className="grid md:grid-cols-2 gap-4 bg-gray-800/60 p-4 rounded border border-gray-700">
        <div className="space-y-3">
          <label className="text-sm text-gray-300">Nome do tema</label>
          <input className="w-full bg-gray-700 rounded px-3 py-2" value={form.name} onChange={(e) => setForm({...form, name: e.target.value})} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <ColorInput label="Fundo" value={form.bg} onChange={(v) => setForm({...form, bg: v})} />
          <ColorInput label="Superfície" value={form.surface} onChange={(v) => setForm({...form, surface: v})} />
          <ColorInput label="Cards" value={form.card} onChange={(v) => setForm({...form, card: v})} />
          <ColorInput label="Acento" value={form.accent} onChange={(v) => setForm({...form, accent: v})} />
          <ColorInput label="Acento suave" value={form.accentSoft} onChange={(v) => setForm({...form, accentSoft: v})} />
          <ColorInput label="Texto" value={form.text} onChange={(v) => setForm({...form, text: v})} />
          <ColorInput label="Texto secundário" value={form.muted} onChange={(v) => setForm({...form, muted: v})} />
        </div>
        <div className="md:col-span-2 flex gap-3">
          <div className="flex items-center gap-2">
            <input type="checkbox" checked={form.is_default} onChange={(e) => setForm({...form, is_default: e.target.checked})} />
            <label className="text-sm text-gray-300">Tema Padrão</label>
          </div>
        </div>
        <div className="md:col-span-2 flex gap-3">
          <button onClick={saveTheme} disabled={loading} className="bg-[#ff6b35] hover:bg-[#ff7b35] text-white px-4 py-2 rounded font-semibold disabled:opacity-50">
            {editingId ? 'Atualizar' : 'Salvar'} tema
          </button>
          {editingId && (
            <button onClick={() => { setEditingId(null); setForm({ name: 'Novo tema', is_default: false, is_active: true, bg: '#0a0e0f', surface: '#0d1415', card: '#0f1b1d', accent: '#d4af37', accentSoft: '#0f6f5a', text: '#ffffff', muted: '#cbd5e1' }); }} className="px-4 py-2 border border-gray-600 rounded hover:border-gray-400">
              Cancelar
            </button>
          )}
        </div>
      </div>

      {loading && themes.length === 0 && <div>Carregando...</div>}

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
        {themes.map((t) => {
          const colors = JSON.parse(t.colors_json);
          return (
            <div key={t.id} className={`p-4 rounded border ${t.is_default ? 'border-[#d4af37]' : 'border-gray-700'} bg-gray-800/60`}>
              <div className="flex items-center justify-between mb-2">
                <div>
                  <h3 className="font-semibold">{t.name}</h3>
                  <p className="text-xs text-gray-400">{t.is_default ? '[Padrão]' : ''}</p>
                </div>
                <div className="flex gap-1">
                  <Swatch color={colors.bg} />
                  <Swatch color={colors.card} />
                  <Swatch color={colors.accent} />
                </div>
              </div>
              <div className="flex gap-2">
                <button onClick={() => applyTheme(t)} className="flex-1 bg-[#0f6f5a] hover:bg-[#158f75] text-white py-1.5 rounded text-sm">Aplicar</button>
                <button onClick={() => loadForEdit(t)} className="px-3 py-1.5 border border-gray-700 rounded text-sm hover:border-gray-500">Editar</button>
                <button onClick={() => deleteTheme(t.id)} className="px-3 py-1.5 border border-gray-700 rounded text-sm hover:border-gray-500">Excluir</button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ColorInput({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <label className="text-sm text-gray-300 flex items-center gap-2">
      <span className="w-28">{label}</span>
      <input type="color" value={value} onChange={(e) => onChange(e.target.value)} className="h-10 w-16 border border-gray-600 rounded bg-gray-700" />
      <input value={value} onChange={(e) => onChange(e.target.value)} className="flex-1 bg-gray-700 rounded px-2 py-1 text-xs" />
    </label>
  );
}

function Swatch({ color }: { color: string }) {
  return <span className="w-6 h-6 rounded border border-gray-600" style={{ background: color }} />;
}

// Table helper
function TabTable({ title, loading, error, onRefresh, columns, rows }:{ title:string; loading:boolean; error:string; onRefresh:()=>void; columns:string[]; rows:(string|number)[][] }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold">{title}</h2>
        <button onClick={onRefresh} className="flex items-center gap-2 px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded">
          <RefreshCw size={18} /> Atualizar
        </button>
      </div>
      {error && <div className="text-red-400 mb-2">{error}</div>}
      {loading ? <div>Carregando...</div> : (
        <div className="overflow-x-auto border border-gray-700 rounded-lg">
          <table className="w-full text-sm">
            <thead className="bg-gray-800">
              <tr>
                {columns.map(c => <th key={c} className="px-3 py-2 text-left">{c}</th>)}
              </tr>
            </thead>
            <tbody>
              {rows.map((r,i) => (
                <tr key={i} className="border-t border-gray-800">
                  {r.map((c,j)=><td key={j} className="px-3 py-2">{c}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
// ========== GGR TAB ==========
function GGRTab({ token }: { token: string }) {
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  const fetchReport = async () => {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      
      const res = await fetch(`${API_URL}/api/admin/ggr/report?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Falha ao carregar relatório');
      setReport(await res.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReport();
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">GGR / Relatório</h2>
        <button onClick={fetchReport} className="flex items-center gap-2 px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded">
          <RefreshCw size={18} /> Atualizar
        </button>
      </div>

      <div className="grid md:grid-cols-2 gap-4 mb-4">
        <div>
          <label className="text-sm text-gray-300">Data Inicial</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            onBlur={fetchReport}
            className="w-full bg-gray-700 rounded px-3 py-2 mt-1"
          />
        </div>
        <div>
          <label className="text-sm text-gray-300">Data Final</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            onBlur={fetchReport}
            className="w-full bg-gray-700 rounded px-3 py-2 mt-1"
          />
        </div>
      </div>

      {error && <div className="text-red-400">{error}</div>}
      {loading && <div className="text-sm text-gray-400">Carregando...</div>}

      {report && (
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard title="GGR" value={`R$ ${report.ggr?.toFixed(2) || '0.00'}`} icon={<TrendingUp />} />
          <StatCard title="NGR" value={`R$ ${report.ngr?.toFixed(2) || '0.00'}`} icon={<DollarSign />} />
          <StatCard title="Total Apostado" value={`R$ ${report.bets?.total_amount?.toFixed(2) || '0.00'}`} icon={<Activity />} />
          <StatCard title="Total Ganho" value={`R$ ${report.bets?.total_wins?.toFixed(2) || '0.00'}`} icon={<DollarSign />} />
          <StatCard title="Depósitos" value={`R$ ${report.deposits?.total?.toFixed(2) || '0.00'}`} subtitle={`${report.deposits?.count || 0} transações`} icon={<ArrowDownCircle />} />
          <StatCard title="Saques" value={`R$ ${report.withdrawals?.total?.toFixed(2) || '0.00'}`} subtitle={`${report.withdrawals?.count || 0} transações`} icon={<ArrowUpCircle />} />
          <StatCard title="Apostas" value={report.bets?.count || 0} subtitle={`R$ ${report.bets?.total_amount?.toFixed(2) || '0.00'}`} icon={<Activity />} />
          <StatCard title="Taxa GGR" value={`${report.ggr_rate?.toFixed(2) || '0.00'}%`} icon={<Percent />} />
        </div>
      )}
    </div>
  );
}

// ========== BETS TAB ==========
function BetsTab({ token }: { token: string }) {
  const [bets, setBets] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchBets = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_URL}/api/admin/bets`, {
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

  useEffect(() => {
    fetchBets();
  }, [token]);

  return (
    <TabTable
      title="Apostas"
      loading={loading}
      error={error}
      onRefresh={fetchBets}
      columns={['ID', 'Usuário', 'Jogo', 'Provedor', 'Valor', 'Ganho', 'Status', 'Data']}
      rows={bets.map(b => [
        b.id,
        b.username || `User ${b.user_id}`,
        b.game_name || b.game_id || '-',
        b.provider || '-',
        `R$ ${b.amount?.toFixed(2)}`,
        `R$ ${b.win_amount?.toFixed(2)}`,
        b.status,
        new Date(b.created_at).toLocaleString('pt-BR')
      ])}
    />
  );
}

// ========== NOTIFICATIONS TAB ==========
function NotificationsTab({ token }: { token: string }) {
  const [notifications, setNotifications] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    title: '',
    message: '',
    type: 'info',
    user_id: '',
    link: ''
  });

  const fetchNotifications = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_URL}/api/admin/notifications`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Falha ao carregar notificações');
      setNotifications(await res.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const createNotification = async () => {
    if (!form.title || !form.message) {
      setError('Título e mensagem são obrigatórios');
      return;
    }
    
    setLoading(true);
    setError('');
    try {
      const body: any = {
        title: form.title,
        message: form.message,
        type: form.type
      };
      if (form.user_id) body.user_id = parseInt(form.user_id);
      if (form.link) body.link = form.link;

      const res = await fetch(`${API_URL}/api/admin/notifications`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify(body)
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Falha ao criar notificação');
      }
      await fetchNotifications();
      setShowForm(false);
      setForm({ title: '', message: '', type: 'info', user_id: '', link: '' });
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const deleteNotification = async (id: number) => {
    if (!confirm('Tem certeza que deseja deletar esta notificação?')) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/notifications/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Falha ao deletar');
      await fetchNotifications();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, [token]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Notificações</h2>
        <div className="flex gap-2">
          <button onClick={() => setShowForm(!showForm)} className="px-3 py-2 bg-[#d4af37] hover:bg-[#c5a028] text-black rounded font-semibold">
            {showForm ? 'Cancelar' : 'Nova Notificação'}
          </button>
          <button onClick={fetchNotifications} className="flex items-center gap-2 px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded">
            <RefreshCw size={18} /> Atualizar
          </button>
        </div>
      </div>

      {showForm && (
        <div className="bg-gray-800/60 p-4 rounded border border-gray-700 space-y-3">
          <h3 className="font-semibold">Criar Notificação</h3>
          <div className="grid md:grid-cols-2 gap-3">
            <input
              placeholder="Título *"
              value={form.title}
              onChange={(e) => setForm({...form, title: e.target.value})}
              className="bg-gray-700 rounded px-3 py-2 text-sm"
              required
            />
            <select
              value={form.type}
              onChange={(e) => setForm({...form, type: e.target.value})}
              className="bg-gray-700 rounded px-3 py-2 text-sm"
            >
              <option value="info">Info</option>
              <option value="success">Sucesso</option>
              <option value="warning">Aviso</option>
              <option value="error">Erro</option>
              <option value="promotion">Promoção</option>
            </select>
            <textarea
              placeholder="Mensagem *"
              value={form.message}
              onChange={(e) => setForm({...form, message: e.target.value})}
              className="bg-gray-700 rounded px-3 py-2 text-sm md:col-span-2"
              rows={3}
              required
            />
            <input
              placeholder="User ID (opcional, deixe vazio para global)"
              value={form.user_id}
              onChange={(e) => setForm({...form, user_id: e.target.value})}
              className="bg-gray-700 rounded px-3 py-2 text-sm"
              type="number"
            />
            <input
              placeholder="Link (opcional)"
              value={form.link}
              onChange={(e) => setForm({...form, link: e.target.value})}
              className="bg-gray-700 rounded px-3 py-2 text-sm"
            />
          </div>
          <button onClick={createNotification} disabled={loading} className="bg-[#ff6b35] hover:bg-[#ff7b35] text-white py-2 px-4 rounded font-semibold disabled:opacity-50">
            Criar
          </button>
        </div>
      )}

      {error && <div className="text-red-400">{error}</div>}
      {loading && !showForm && <div className="text-sm text-gray-400">Carregando...</div>}

      <div className="overflow-x-auto border border-gray-700 rounded-lg">
        <table className="w-full text-sm">
          <thead className="bg-gray-800">
            <tr>
              <th className="px-3 py-2 text-left">ID</th>
              <th className="px-3 py-2 text-left">Título</th>
              <th className="px-3 py-2 text-left">Tipo</th>
              <th className="px-3 py-2 text-left">Usuário</th>
              <th className="px-3 py-2 text-left">Ativa</th>
              <th className="px-3 py-2 text-left">Data</th>
              <th className="px-3 py-2 text-left">Ações</th>
            </tr>
          </thead>
          <tbody>
            {notifications.length === 0 && !loading ? (
              <tr>
                <td colSpan={7} className="px-3 py-4 text-center text-gray-400">
                  Nenhuma notificação encontrada
                </td>
              </tr>
            ) : (
              notifications.map(n => (
                <tr key={n.id} className="border-t border-gray-800">
                  <td className="px-3 py-2">{n.id}</td>
                  <td className="px-3 py-2">{n.title}</td>
                  <td className="px-3 py-2">
                    <span className={`px-2 py-1 rounded text-xs ${
                      n.type === 'success' ? 'bg-green-500/20 text-green-400' :
                      n.type === 'error' ? 'bg-red-500/20 text-red-400' :
                      n.type === 'warning' ? 'bg-yellow-500/20 text-yellow-400' :
                      n.type === 'promotion' ? 'bg-purple-500/20 text-purple-400' :
                      'bg-blue-500/20 text-blue-400'
                    }`}>
                      {n.type}
                    </span>
                  </td>
                  <td className="px-3 py-2">{n.username || (n.user_id ? `User ${n.user_id}` : 'Global')}</td>
                  <td className="px-3 py-2">{n.is_active ? 'SIM' : 'NAO'}</td>
                  <td className="px-3 py-2">{new Date(n.created_at).toLocaleString('pt-BR')}</td>
                  <td className="px-3 py-2">
                    <button
                      onClick={() => deleteNotification(n.id)}
                      disabled={loading}
                      className="text-red-400 hover:text-red-300 text-xs disabled:opacity-50"
                    >
                      Deletar
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}


// ========== AFFILIATES TAB ==========
function AffiliatesTab({ token }: { token: string }) {
  const [affiliates, setAffiliates] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    user_id: '',
    code: '',
    cpa: 0,
    revshare: 0,
    is_active: true
  });
  const [editingId, setEditingId] = useState<number | null>(null);

  const fetchUsers = async () => {
    try {
      const res = await fetch(`${API_URL}/api/admin/users?limit=1000`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        setUsers(await res.json());
      }
    } catch (err) {
      console.error('Erro ao carregar usuários:', err);
    }
  };

  const fetchAffiliates = async () => {
    setLoading(true); setError('');
    try {
      const res = await fetch(`${API_URL}/api/admin/affiliates`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Falha ao carregar afiliados');
      const data = await res.json();
      // Buscar estatísticas para cada afiliado
      const affiliatesWithStats = await Promise.all(data.map(async (affiliate: any) => {
        try {
          // Buscar usuários vinculados a este afiliado
          const usersRes = await fetch(`${API_URL}/api/admin/users?affiliate_id=${affiliate.id}`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          const subordinateUsers = usersRes.ok ? await usersRes.json() : [];
          const subordinateIds = subordinateUsers.map((u: any) => u.id);
          
          // Buscar depósitos dos subordinados
          const depositsRes = await fetch(`${API_URL}/api/admin/deposits`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          const allDeposits = depositsRes.ok ? await depositsRes.json() : [];
          const deposits = allDeposits.filter((d: any) => subordinateIds.includes(d.user_id));
          const totalDeposits = deposits.reduce((sum: number, d: any) => sum + (d.amount || 0), 0);
          
          // Buscar FTDs
          const ftdsRes = await fetch(`${API_URL}/api/admin/ftds`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          const allFtds = ftdsRes.ok ? await ftdsRes.json() : [];
          const ftds = allFtds.filter((f: any) => subordinateIds.includes(f.user_id));
          
          // Extrair CPA do metadata do afiliado
          const metadata = affiliate.metadata_json ? JSON.parse(affiliate.metadata_json) : {};
          const cpaRate = metadata.cpa || 2.0; // Valor padrão se não configurado
          
          // Calcular ganhos
          const cpaEarned = ftds.length * cpaRate;
          const revshareRate = affiliate.commission_rate || 0;
          const revshareEarned = (totalDeposits * revshareRate) / 100;
          const totalEarned = cpaEarned + revshareEarned;
          
          // Buscar usuário vinculado ao afiliado (o próprio afiliado)
          // O backend agora retorna user_id e user_name diretamente
          const affiliateUserId = affiliate.user_id || null;
          const affiliateUserName = affiliate.user_name || null;
          
          // Se não veio do backend, tentar buscar na lista de usuários
          let finalUserName = affiliateUserName;
          if (!finalUserName && affiliateUserId) {
            const foundUser = users.find((u: any) => u.id === affiliateUserId);
            finalUserName = foundUser?.username || '-';
          }
          
          return {
            ...affiliate,
            user_id: affiliateUserId || subordinateUsers[0]?.id || null,
            user_name: finalUserName || subordinateUsers[0]?.username || '-',
            cpa: cpaRate,
            revshare: revshareRate,
            deposits_brought: totalDeposits,
            total_earned: totalEarned,
            referrals: subordinateUsers.length
          };
        } catch (err) {
          const metadata = affiliate.metadata_json ? JSON.parse(affiliate.metadata_json) : {};
          const cpaRate = metadata.cpa || 0;
          const affiliateUser = users.find((u: any) => u.affiliate_id === affiliate.id);
          return {
            ...affiliate,
            user_id: affiliateUser?.id || null,
            user_name: affiliateUser?.username || '-',
            cpa: cpaRate,
            revshare: affiliate.commission_rate || 0,
            deposits_brought: 0,
            total_earned: 0,
            referrals: 0
          };
        }
      }));
      setAffiliates(affiliatesWithStats);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const createOrUpdate = async () => {
    setLoading(true); setError('');
    try {
      const selectedUser = users.find(u => u.id === parseInt(form.user_id));
      if (!selectedUser && !editingId) {
        throw new Error('Selecione um usuário');
      }
      
      const affiliateData = {
        code: form.code,
        name: selectedUser?.username || selectedUser?.email || form.code,
        email: selectedUser?.email || '',
        phone: selectedUser?.phone || '',
        commission_rate: form.revshare,
        is_active: form.is_active,
        metadata_json: JSON.stringify({ cpa: form.cpa, user_id: parseInt(form.user_id) })
      };
      
      const url = editingId
        ? `${API_URL}/api/admin/affiliates/${editingId}`
        : `${API_URL}/api/admin/affiliates`;
      const method = editingId ? 'PUT' : 'POST';
      
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(affiliateData)
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Falha ao salvar');
      }
      
      // O backend agora vincula automaticamente o usuário ao afiliado
      // Não precisa fazer chamada adicional
      
      await fetchAffiliates();
      setShowForm(false);
      setForm({ user_id: '', code: '', cpa: 0, revshare: 0, is_active: true });
      setEditingId(null);
      setError('');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadForEdit = (affiliate: any) => {
    setEditingId(affiliate.id);
    const metadata = affiliate.metadata_json ? JSON.parse(affiliate.metadata_json) : {};
    setForm({
      user_id: affiliate.user_id?.toString() || '',
      code: affiliate.code,
      cpa: metadata.cpa || 0,
      revshare: affiliate.commission_rate || 0,
      is_active: affiliate.is_active ?? true
    });
    setShowForm(true);
  };

  const deleteAffiliate = async (id: number) => {
    if (!confirm('Deletar este afiliado?')) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/affiliates/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Falha ao deletar');
      await fetchAffiliates();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
    fetchAffiliates();
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Afiliados</h2>
        <div className="flex gap-2">
          <button
            onClick={() => { setShowForm(!showForm); setEditingId(null); setForm({ user_id: '', code: '', cpa: 0, revshare: 0, is_active: true }); }}
            className="px-3 py-2 bg-[#d4af37] hover:bg-[#c5a028] text-black rounded font-semibold"
          >
            {showForm ? 'Cancelar' : 'Novo Afiliado'}
          </button>
          <button onClick={fetchAffiliates} className="flex items-center gap-2 px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded">
            <RefreshCw size={18} /> Atualizar
          </button>
        </div>
      </div>

      {error && <div className="text-red-400">{error}</div>}

      {showForm && (
        <div className="bg-gray-800/60 p-6 rounded-lg border border-gray-700 space-y-4">
          <h3 className="text-lg font-semibold">{editingId ? 'Editar' : 'Criar Novo'} Afiliado</h3>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Usuário *</label>
              <select
                value={form.user_id}
                onChange={(e) => setForm({...form, user_id: e.target.value})}
                className="w-full bg-gray-700 rounded px-3 py-2 text-sm border border-gray-600"
                disabled={!!editingId}
              >
                <option value="">Selecione um usuário</option>
                {users.map(u => (
                  <option key={u.id} value={u.id}>{u.username} {u.email ? `(${u.email})` : ''}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Código do Afiliado *</label>
              <input
                placeholder="Ex: AFF001"
                value={form.code}
                onChange={(e) => setForm({...form, code: e.target.value.toUpperCase()})}
                className="w-full bg-gray-700 rounded px-3 py-2 text-sm border border-gray-600"
                disabled={!!editingId}
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">CPA (R$)</label>
              <input
                type="number"
                step="0.01"
                placeholder="0.00"
                value={form.cpa}
                onChange={(e) => setForm({...form, cpa: parseFloat(e.target.value) || 0})}
                className="w-full bg-gray-700 rounded px-3 py-2 text-sm border border-gray-600"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Revshare (%)</label>
              <input
                type="number"
                step="0.01"
                placeholder="0.00"
                value={form.revshare}
                onChange={(e) => setForm({...form, revshare: parseFloat(e.target.value) || 0})}
                className="w-full bg-gray-700 rounded px-3 py-2 text-sm border border-gray-600"
              />
            </div>
          </div>
          <button
            onClick={createOrUpdate}
            disabled={loading || !form.code || !form.user_id}
            className="bg-[#d4af37] hover:bg-[#ffd700] text-black py-2 px-4 rounded font-semibold disabled:opacity-50"
          >
            {loading ? 'Salvando...' : editingId ? 'Atualizar' : 'Criar'}
          </button>
        </div>
      )}

      {loading && affiliates.length === 0 && <div>Carregando...</div>}

      <div className="bg-gray-800/60 rounded-lg border border-gray-700 overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <h3 className="text-lg font-semibold">Lista de Afiliados</h3>
          <button onClick={fetchAffiliates} className="flex items-center gap-2 px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded text-sm">
            <RefreshCw size={16} /> Atualizar
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-700">
              <tr>
                <th className="px-4 py-3 text-left">ID</th>
                <th className="px-4 py-3 text-left">Usuário</th>
                <th className="px-4 py-3 text-left">Código</th>
                <th className="px-4 py-3 text-left">CPA (R$)</th>
                <th className="px-4 py-3 text-left">Revshare (%)</th>
                <th className="px-4 py-3 text-left">Trouxe (depósitos)</th>
                <th className="px-4 py-3 text-left">Total Ganho</th>
                <th className="px-4 py-3 text-left">Indicações</th>
                <th className="px-4 py-3 text-left">Status</th>
                <th className="px-4 py-3 text-left">Ações</th>
              </tr>
            </thead>
            <tbody>
              {affiliates.length === 0 && !loading ? (
                <tr>
                  <td colSpan={10} className="px-4 py-8 text-center text-gray-400">
                    Nenhum afiliado cadastrado
                  </td>
                </tr>
              ) : (
                affiliates.map(a => (
                  <tr key={a.id} className="border-t border-gray-700 hover:bg-gray-800/50">
                    <td className="px-4 py-3">{a.id}</td>
                    <td className="px-4 py-3">{a.user_name || '-'}</td>
                    <td className="px-4 py-3 font-mono">{a.code}</td>
                    <td className="px-4 py-3">R$ {a.cpa?.toFixed(2) || '0.00'}</td>
                    <td className="px-4 py-3">{a.revshare?.toFixed(2) || '0.00'}%</td>
                    <td className="px-4 py-3">R$ {a.deposits_brought?.toFixed(2) || '0.00'}</td>
                    <td className="px-4 py-3">R$ {a.total_earned?.toFixed(2) || '0.00'}</td>
                    <td className="px-4 py-3">{a.referrals || 0}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded text-xs ${a.is_active ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'}`}>
                        {a.is_active ? 'Ativo' : 'Inativo'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2">
                        <button
                          onClick={() => loadForEdit(a)}
                          className="text-blue-400 hover:text-blue-300 text-sm"
                        >
                          Editar
                        </button>
                        <button
                          onClick={() => deleteAffiliate(a.id)}
                          className="text-red-400 hover:text-red-300 text-sm"
                        >
                          Deletar
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function IGameWinProvidersTab({ token }: { token: string }) {
  const [configs, setConfigs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [availableProviders, setAvailableProviders] = useState<any[]>([]);
  const [loadingProviders, setLoadingProviders] = useState(false);
  const [form, setForm] = useState({ provider_code: '', provider_name: '', position: 1, is_active: true });
  const [editingId, setEditingId] = useState<number | null>(null);

  const fetchConfigs = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_URL}/api/admin/igamewin-provider-configs`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Falha ao carregar configurações');
      setConfigs(await res.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailableProviders = async () => {
    setLoadingProviders(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/igamewin/games`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setAvailableProviders(data.providers || []);
      }
    } catch (err) {
      console.error('Erro ao buscar provedores:', err);
    } finally {
      setLoadingProviders(false);
    }
  };

  useEffect(() => {
    fetchConfigs();
    fetchAvailableProviders();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');

    try {
      const url = editingId
        ? `${API_URL}/api/admin/igamewin-provider-configs/${editingId}`
        : `${API_URL}/api/admin/igamewin-provider-configs`;
      const method = editingId ? 'PUT' : 'POST';

      const res = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(form)
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Falha ao salvar configuração');
      }

      setMessage(editingId ? 'Configuração atualizada com sucesso!' : 'Configuração criada com sucesso!');
      setForm({ provider_code: '', provider_name: '', position: 1, is_active: true });
      setEditingId(null);
      await fetchConfigs();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (config: any) => {
    setForm({
      provider_code: config.provider_code,
      provider_name: config.provider_name,
      position: config.position,
      is_active: config.is_active
    });
    setEditingId(config.id);
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Tem certeza que deseja deletar esta configuração?')) return;

    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/igamewin-provider-configs/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Falha ao deletar');
      setMessage('Configuração deletada com sucesso!');
      await fetchConfigs();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleReorder = async (configIds: number[]) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/igamewin-provider-configs/reorder`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(configIds)
      });
      if (!res.ok) throw new Error('Falha ao reordenar');
      setMessage('Ordem atualizada com sucesso!');
      await fetchConfigs();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const moveUp = (index: number) => {
    if (index === 0) return;
    const newConfigs = [...configs];
    [newConfigs[index - 1], newConfigs[index]] = [newConfigs[index], newConfigs[index - 1]];
    setConfigs(newConfigs);
    handleReorder(newConfigs.map(c => c.id));
  };

  const moveDown = (index: number) => {
    if (index === configs.length - 1) return;
    const newConfigs = [...configs];
    [newConfigs[index], newConfigs[index + 1]] = [newConfigs[index + 1], newConfigs[index]];
    setConfigs(newConfigs);
    handleReorder(newConfigs.map(c => c.id));
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Provedores IGameWin</h2>
      <p className="text-gray-400">Configure até 3 provedores preferidos e defina a ordem de exibição</p>

      {error && <div className="bg-red-500/20 border border-red-500 text-red-200 px-4 py-3 rounded">{error}</div>}
      {message && <div className="bg-green-500/20 border border-green-500 text-green-200 px-4 py-3 rounded">{message}</div>}

      <form onSubmit={handleSubmit} className="bg-gray-800 p-6 rounded-lg space-y-4">
        <h3 className="text-lg font-semibold">{editingId ? 'Editar' : 'Adicionar'} Provedor</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Código do Provedor</label>
            <input
              type="text"
              value={form.provider_code}
              onChange={(e) => setForm({ ...form, provider_code: e.target.value.toUpperCase() })}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
              required
              placeholder="Ex: PGSOFT, PRAGMATIC"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Nome do Provedor</label>
            <input
              type="text"
              value={form.provider_name}
              onChange={(e) => setForm({ ...form, provider_name: e.target.value })}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
              required
              placeholder="Ex: PG Soft, Pragmatic Play"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Posição (1, 2 ou 3)</label>
            <select
              value={form.position}
              onChange={(e) => setForm({ ...form, position: parseInt(e.target.value) })}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
              required
            >
              <option value={1}>1 - Primeiro</option>
              <option value={2}>2 - Segundo</option>
              <option value={3}>3 - Terceiro</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="is_active"
              checked={form.is_active}
              onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
              className="w-4 h-4"
            />
            <label htmlFor="is_active" className="text-sm">Ativo</label>
          </div>
        </div>

        <div className="flex gap-2">
          <button
            type="submit"
            disabled={loading}
            className="bg-[#d4af37] hover:bg-[#ffd700] text-black px-4 py-2 rounded font-semibold disabled:opacity-50"
          >
            {editingId ? 'Atualizar' : 'Adicionar'}
          </button>
          {editingId && (
            <button
              type="button"
              onClick={() => {
                setForm({ provider_code: '', provider_name: '', position: 1, is_active: true });
                setEditingId(null);
              }}
              className="bg-gray-600 hover:bg-gray-500 px-4 py-2 rounded"
            >
              Cancelar
            </button>
          )}
        </div>
      </form>

      {loadingProviders && (
        <div className="bg-gray-800 p-4 rounded">
          <p className="text-gray-400">Carregando provedores disponíveis...</p>
        </div>
      )}

      {availableProviders.length > 0 && (
        <div className="bg-gray-800 p-4 rounded">
          <h3 className="text-lg font-semibold mb-2">Provedores Disponíveis</h3>
          <div className="flex flex-wrap gap-2">
            {availableProviders.map((p: any) => (
              <button
                key={p.code || p.provider_code}
                onClick={() => {
                  if (!configs.find(c => c.provider_code === (p.code || p.provider_code))) {
                    setForm({
                      provider_code: p.code || p.provider_code,
                      provider_name: p.name || p.provider_name || p.code || p.provider_code,
                      position: configs.length + 1,
                      is_active: true
                    });
                  }
                }}
                className="bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded text-sm"
                disabled={configs.some(c => c.provider_code === (p.code || p.provider_code))}
              >
                {p.name || p.provider_name || p.code || p.provider_code}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="bg-gray-800 rounded-lg overflow-hidden">
        <div className="p-4 border-b border-gray-700">
          <h3 className="text-lg font-semibold">Provedores Configurados ({configs.length}/3)</h3>
        </div>
        {loading ? (
          <div className="p-4 text-center text-gray-400">Carregando...</div>
        ) : configs.length === 0 ? (
          <div className="p-4 text-center text-gray-400">Nenhum provedor configurado</div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-900">
              <tr>
                <th className="px-4 py-3 text-left">Posição</th>
                <th className="px-4 py-3 text-left">Código</th>
                <th className="px-4 py-3 text-left">Nome</th>
                <th className="px-4 py-3 text-left">Status</th>
                <th className="px-4 py-3 text-left">Ações</th>
              </tr>
            </thead>
            <tbody>
              {configs.map((config, index) => (
                <tr key={config.id} className="border-b border-gray-700">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold">{config.position}</span>
                      <div className="flex flex-col gap-1">
                        <button
                          onClick={() => moveUp(index)}
                          disabled={index === 0 || loading}
                          className="text-xs text-gray-400 hover:text-white disabled:opacity-50"
                        >
                          ↑
                        </button>
                        <button
                          onClick={() => moveDown(index)}
                          disabled={index === configs.length - 1 || loading}
                          className="text-xs text-gray-400 hover:text-white disabled:opacity-50"
                        >
                          ↓
                        </button>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">{config.provider_code}</td>
                  <td className="px-4 py-3">{config.provider_name}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded text-xs ${config.is_active ? 'bg-green-500/20 text-green-300' : 'bg-gray-500/20 text-gray-300'}`}>
                      {config.is_active ? 'Ativo' : 'Inativo'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleEdit(config)}
                        className="text-[#d4af37] hover:text-[#ffd700] text-xs"
                      >
                        Editar
                      </button>
                      <button
                        onClick={() => handleDelete(config.id)}
                        className="text-red-400 hover:text-red-300 text-xs"
                      >
                        Deletar
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

// ========== PROMOTIONS TAB ==========
function PromotionsTab({ token }: { token: string }) {
  const [promotions, setPromotions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [uploadingBanner, setUploadingBanner] = useState<number | null>(null);
  const [form, setForm] = useState({
    title: '',
    description: '',
    type: 'bonus',
    bonus_value: '',
    bonus_type: 'percentage',
    min_deposit_amount: '',
    max_bonus_amount: '',
    is_first_deposit_only: false,
    is_withdrawable: false,
    start_date: '',
    end_date: '',
    is_active: true
  });

  const fetchPromotions = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_URL}/api/admin/promotions`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Falha ao carregar promoções');
      setPromotions(await res.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const createPromotion = async () => {
    if (!form.title || !form.bonus_value || !form.start_date || !form.end_date) {
      setError('Preencha todos os campos obrigatórios');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const body: any = {
        title: form.title,
        description: form.description || null,
        type: form.type,
        bonus_value: parseFloat(form.bonus_value),
        bonus_type: form.bonus_type,
        min_deposit_amount: form.min_deposit_amount ? parseFloat(form.min_deposit_amount) : 0.0,
        is_first_deposit_only: form.is_first_deposit_only,
        is_withdrawable: form.is_withdrawable,
        is_active: form.is_active,
        start_date: new Date(form.start_date).toISOString(),
        end_date: new Date(form.end_date).toISOString()
      };
      
      if (form.max_bonus_amount) {
        body.max_bonus_amount = parseFloat(form.max_bonus_amount);
      }

      const res = await fetch(`${API_URL}/api/admin/promotions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(body)
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Falha ao criar promoção');
      }

      await fetchPromotions();
      setShowForm(false);
      setForm({
        title: '',
        description: '',
        type: 'bonus',
        bonus_value: '',
        bonus_type: 'percentage',
        min_deposit_amount: '',
        max_bonus_amount: '',
        is_first_deposit_only: false,
        is_withdrawable: false,
        start_date: '',
        end_date: '',
        is_active: true
      });
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleBannerUpload = async (promotionId: number, file: File) => {
    setUploadingBanner(promotionId);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const res = await fetch(`${API_URL}/api/admin/promotions/${promotionId}/upload-banner`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`
        },
        body: formData
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Falha ao fazer upload do banner');
      }

      await fetchPromotions();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setUploadingBanner(null);
    }
  };

  useEffect(() => {
    if (token) {
      fetchPromotions();
    }
  }, [token]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Promoções</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-[#ff6b35] hover:bg-[#ff7b35] text-white rounded"
        >
          {showForm ? 'Cancelar' : 'Nova Promoção'}
        </button>
      </div>

      {error && (
        <div className="bg-red-500/20 border border-red-500 rounded-lg p-3 text-red-400 text-sm">
          {error}
        </div>
      )}

      {showForm && (
        <div className="bg-gray-800/60 p-6 rounded-lg border border-gray-700">
          <h3 className="text-lg font-semibold mb-4">Nova Promoção</h3>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Título</label>
              <input
                className="w-full bg-gray-700 rounded px-3 py-2 text-sm border border-gray-600"
                value={form.title}
                onChange={e => setForm({...form, title: e.target.value})}
                placeholder="Título da promoção"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Tipo</label>
              <select
                className="w-full bg-gray-700 rounded px-3 py-2 text-sm border border-gray-600"
                value={form.type}
                onChange={e => setForm({...form, type: e.target.value})}
              >
                <option value="bonus">Bônus</option>
                <option value="cashback">Cashback</option>
                <option value="free_spins">Free Spins</option>
                <option value="tournament">Torneio</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Tipo de Bônus</label>
              <select
                className="w-full bg-gray-700 rounded px-3 py-2 text-sm border border-gray-600"
                value={form.bonus_type}
                onChange={e => setForm({...form, bonus_type: e.target.value})}
              >
                <option value="percentage">Percentual (%)</option>
                <option value="fixed">Valor Fixo (R$)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Valor do Bônus</label>
              <input
                type="number"
                step="0.01"
                className="w-full bg-gray-700 rounded px-3 py-2 text-sm border border-gray-600"
                value={form.bonus_value}
                onChange={e => setForm({...form, bonus_value: e.target.value})}
                placeholder={form.bonus_type === 'percentage' ? '10' : '50.00'}
                required
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Depósito Mínimo (R$)</label>
              <input
                type="number"
                step="0.01"
                className="w-full bg-gray-700 rounded px-3 py-2 text-sm border border-gray-600"
                value={form.min_deposit_amount}
                onChange={e => setForm({...form, min_deposit_amount: e.target.value})}
                placeholder="0.00"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Bônus Máximo (R$)</label>
              <input
                type="number"
                step="0.01"
                className="w-full bg-gray-700 rounded px-3 py-2 text-sm border border-gray-600"
                value={form.max_bonus_amount}
                onChange={e => setForm({...form, max_bonus_amount: e.target.value})}
                placeholder="Deixe vazio para sem limite"
              />
              <p className="text-xs text-gray-500 mt-1">Apenas para cupons percentuais</p>
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm text-gray-400 mb-1">Descrição</label>
              <textarea
                className="w-full bg-gray-700 rounded px-3 py-2 text-sm border border-gray-600"
                value={form.description}
                onChange={e => setForm({...form, description: e.target.value})}
                placeholder="Descrição da promoção"
                rows={3}
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Data Início</label>
              <input
                type="datetime-local"
                className="w-full bg-gray-700 rounded px-3 py-2 text-sm border border-gray-600"
                value={form.start_date}
                onChange={e => setForm({...form, start_date: e.target.value})}
                required
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Data Fim</label>
              <input
                type="datetime-local"
                className="w-full bg-gray-700 rounded px-3 py-2 text-sm border border-gray-600"
                value={form.end_date}
                onChange={e => setForm({...form, end_date: e.target.value})}
                required
              />
            </div>
            <div className="md:col-span-2 flex items-center gap-2">
              <input
                type="checkbox"
                checked={form.is_first_deposit_only}
                onChange={e => setForm({...form, is_first_deposit_only: e.target.checked})}
                className="w-4 h-4"
              />
              <label className="text-sm text-gray-300">Aplicar apenas no primeiro depósito</label>
            </div>
            <div className="md:col-span-2 flex items-center gap-2">
              <input
                type="checkbox"
                checked={form.is_withdrawable}
                onChange={e => setForm({...form, is_withdrawable: e.target.checked})}
                className="w-4 h-4"
              />
              <label className="text-sm text-gray-300">Bônus sacável (pode ser retirado)</label>
            </div>
            <div className="md:col-span-2 flex items-center gap-2">
              <input
                type="checkbox"
                checked={form.is_active}
                onChange={e => setForm({...form, is_active: e.target.checked})}
                className="w-4 h-4"
              />
              <label className="text-sm text-gray-300">Ativa</label>
            </div>
          </div>
          <div className="mt-4 flex gap-2">
            <button
              onClick={createPromotion}
              disabled={loading}
              className="px-4 py-2 bg-[#d4af37] hover:bg-[#ffd700] text-black rounded disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Criando...' : 'Criar Promoção'}
            </button>
            <button
              onClick={() => {
                setShowForm(false);
                setForm({
                  title: '',
                  description: '',
                  type: 'bonus',
                  bonus_value: '',
                  bonus_type: 'percentage',
                  min_deposit_amount: '',
                  max_bonus_amount: '',
                  is_first_deposit_only: false,
                  is_withdrawable: false,
                  start_date: '',
                  end_date: '',
                  is_active: true
                });
              }}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}

      {loading ? (
        <div className="text-center py-12">Carregando promoções...</div>
      ) : promotions.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          <p>Nenhuma promoção cadastrada</p>
          <p className="text-sm mt-2">Clique em "Nova Promoção" para criar uma</p>
        </div>
      ) : (
        <div className="bg-gray-800/60 rounded-lg border border-gray-700 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-700">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-semibold">Título</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Tipo</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Status</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Data Início</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Data Fim</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Ações</th>
              </tr>
            </thead>
            <tbody>
              {promotions.map((promo) => (
                <tr key={promo.id} className="border-t border-gray-700">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      {promo.banner_url && (
                        <img 
                          src={`${API_URL}${promo.banner_url}`} 
                          alt={promo.title}
                          className="w-16 h-10 object-cover rounded"
                        />
                      )}
                      <span>{promo.title}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div>
                      <div className="font-semibold">{promo.type}</div>
                      <div className="text-xs text-gray-400">
                        {promo.bonus_value}{promo.bonus_type === 'percentage' ? '%' : ' R$'}
                        {promo.is_first_deposit_only && ' (1º depósito)'}
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded text-xs ${promo.is_active ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'}`}>
                      {promo.is_active ? 'Ativa' : 'Inativa'}
                    </span>
                  </td>
                  <td className="px-4 py-3">{new Date(promo.start_date).toLocaleDateString('pt-BR')}</td>
                  <td className="px-4 py-3">{new Date(promo.end_date).toLocaleDateString('pt-BR')}</td>
                  <td className="px-4 py-3">
                    <div className="flex flex-col gap-1">
                      <input
                        type="file"
                        accept="image/*"
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (file) {
                            handleBannerUpload(promo.id, file);
                          }
                        }}
                        className="hidden"
                        id={`banner-upload-${promo.id}`}
                      />
                      <label
                        htmlFor={`banner-upload-${promo.id}`}
                        className="text-xs text-blue-400 hover:text-blue-300 cursor-pointer"
                      >
                        {uploadingBanner === promo.id ? 'Enviando...' : promo.banner_url ? 'Trocar Banner' : 'Adicionar Banner'}
                      </label>
                      <button className="text-blue-400 hover:text-blue-300 text-sm">Editar</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ========== SUPPORT TAB ==========
function SupportTab({ token: _token }: { token: string }) {
  const [config, setConfig] = useState({
    support_email: '',
    support_phone: '',
    support_whatsapp: '',
    chat_widget_url: '',
    support_link: '',
    is_active: true
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const fetchConfig = async () => {
    setLoading(true);
    setError('');
    try {
      // TODO: Implementar endpoint de configuração de suporte no backend
      // const res = await fetch(`${API_URL}/api/admin/support/config`, {
      //   headers: { Authorization: `Bearer ${token}` }
      // });
      // if (!res.ok) throw new Error('Falha ao carregar configurações');
      // setConfig(await res.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async () => {
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      // TODO: Implementar endpoint de salvar configuração de suporte no backend
      // const res = await fetch(`${API_URL}/api/admin/support/config`, {
      //   method: 'PUT',
      //   headers: {
      //     'Content-Type': 'application/json',
      //     Authorization: `Bearer ${token}`
      //   },
      //   body: JSON.stringify(config)
      // });
      // if (!res.ok) throw new Error('Falha ao salvar configurações');
      setSuccess('Configurações salvas com sucesso!');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConfig();
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Configuração de Suporte</h2>
          <p className="text-sm text-gray-400">Configure links e informações de contato</p>
        </div>
      </div>

      {error && (
        <div className="bg-red-500/20 border border-red-500 rounded-lg p-3 text-red-400 text-sm">
          {error}
        </div>
      )}

      {success && (
        <div className="bg-green-500/20 border border-green-500 rounded-lg p-3 text-green-400 text-sm">
          {success}
        </div>
      )}

      <div className="bg-gray-800/60 p-6 rounded-lg border border-gray-700">
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Email de Suporte</label>
            <input
              type="email"
              className="w-full bg-gray-700 rounded px-3 py-2 text-sm border border-gray-600"
              value={config.support_email}
              onChange={e => setConfig({...config, support_email: e.target.value})}
              placeholder="suporte@exemplo.com"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Telefone</label>
            <input
              type="tel"
              className="w-full bg-gray-700 rounded px-3 py-2 text-sm border border-gray-600"
              value={config.support_phone}
              onChange={e => setConfig({...config, support_phone: e.target.value})}
              placeholder="(00) 00000-0000"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">WhatsApp</label>
            <input
              type="text"
              className="w-full bg-gray-700 rounded px-3 py-2 text-sm border border-gray-600"
              value={config.support_whatsapp}
              onChange={e => setConfig({...config, support_whatsapp: e.target.value})}
              placeholder="https://wa.me/5511999999999"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Link de Suporte</label>
            <input
              type="url"
              className="w-full bg-gray-700 rounded px-3 py-2 text-sm border border-gray-600"
              value={config.support_link}
              onChange={e => setConfig({...config, support_link: e.target.value})}
              placeholder="https://exemplo.com/suporte"
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm text-gray-400 mb-1">URL do Widget de Chat</label>
            <input
              type="url"
              className="w-full bg-gray-700 rounded px-3 py-2 text-sm border border-gray-600"
              value={config.chat_widget_url}
              onChange={e => setConfig({...config, chat_widget_url: e.target.value})}
              placeholder="https://exemplo.com/widget.js"
            />
          </div>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={config.is_active}
              onChange={e => setConfig({...config, is_active: e.target.checked})}
              className="w-4 h-4"
            />
            <label className="text-sm text-gray-300">Suporte Ativo</label>
          </div>
        </div>
        <div className="mt-6 flex gap-2">
          <button
            onClick={saveConfig}
            disabled={loading}
            className="px-4 py-2 bg-[#d4af37] hover:bg-[#ffd700] text-black rounded disabled:opacity-50"
          >
            {loading ? 'Salvando...' : 'Salvar Configurações'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ========== COIN STORE TAB (REMOVED) ==========

// ========== COUPONS TAB ==========
function CouponsTab({ token }: { token: string }) {
  const [coupons, setCoupons] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    code: '',
    type: 'percentage',
    value: '',
    max_uses: '',
    valid_from: '',
    valid_until: '',
    min_deposit_amount: '',
    max_bonus_amount: '',
    is_withdrawable: false,
    is_active: true
  });

  const fetchCoupons = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_URL}/api/admin/coupons`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Falha ao carregar cupons');
      setCoupons(await res.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const createCoupon = async () => {
    if (!form.code || !form.value || !form.valid_from || !form.valid_until) {
      setError('Preencha todos os campos obrigatórios');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const body: any = {
        code: form.code.toUpperCase().trim(),
        type: form.type,
        value: parseFloat(form.value),
        valid_from: new Date(form.valid_from).toISOString(),
        valid_until: new Date(form.valid_until).toISOString(),
        min_deposit_amount: form.min_deposit_amount ? parseFloat(form.min_deposit_amount) : 0.0,
        is_withdrawable: form.is_withdrawable,
        is_active: form.is_active
      };
      
      if (form.max_uses) {
        body.max_uses = parseInt(form.max_uses);
      }
      
      if (form.max_bonus_amount) {
        body.max_bonus_amount = parseFloat(form.max_bonus_amount);
      }

      const res = await fetch(`${API_URL}/api/admin/coupons`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(body)
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Falha ao criar cupom');
      }

      await fetchCoupons();
      setShowForm(false);
      setForm({
        code: '',
        type: 'percentage',
        value: '',
        max_uses: '',
        valid_from: '',
        valid_until: '',
        min_deposit_amount: '',
        max_bonus_amount: '',
        is_withdrawable: false,
        is_active: true
      });
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchCoupons();
    }
  }, [token]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Cupons</h2>
          <p className="text-sm text-gray-400">Gerenciamento de cupons de desconto</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-[#ff6b35] hover:bg-[#ff7b35] text-white rounded"
        >
          {showForm ? 'Cancelar' : 'Novo Cupom'}
        </button>
      </div>

      {error && (
        <div className="bg-red-500/20 border border-red-500 rounded-lg p-3 text-red-400 text-sm">
          {error}
        </div>
      )}

      {showForm && (
        <div className="bg-gray-800/60 p-6 rounded-lg border border-gray-700">
          <h3 className="text-lg font-semibold mb-4">Novo Cupom</h3>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Código do Cupom</label>
              <input
                className="w-full bg-gray-700 rounded px-3 py-2 text-sm border border-gray-600"
                value={form.code}
                onChange={e => setForm({...form, code: e.target.value.toUpperCase()})}
                placeholder="EXEMPLO123"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Tipo</label>
              <select
                className="w-full bg-gray-700 rounded px-3 py-2 text-sm border border-gray-600"
                value={form.type}
                onChange={e => setForm({...form, type: e.target.value})}
              >
                <option value="percentage">Percentual (%)</option>
                <option value="fixed">Valor Fixo (R$)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Valor</label>
              <input
                type="number"
                className="w-full bg-gray-700 rounded px-3 py-2 text-sm border border-gray-600"
                value={form.value}
                onChange={e => setForm({...form, value: e.target.value})}
                placeholder={form.type === 'percentage' ? '10' : '50.00'}
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Máximo de Usos</label>
              <input
                type="number"
                className="w-full bg-gray-700 rounded px-3 py-2 text-sm border border-gray-600"
                value={form.max_uses}
                onChange={e => setForm({...form, max_uses: e.target.value})}
                placeholder="100 (deixe vazio para ilimitado)"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Válido De</label>
              <input
                type="datetime-local"
                className="w-full bg-gray-700 rounded px-3 py-2 text-sm border border-gray-600"
                value={form.valid_from}
                onChange={e => setForm({...form, valid_from: e.target.value})}
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Válido Até</label>
              <input
                type="datetime-local"
                className="w-full bg-gray-700 rounded px-3 py-2 text-sm border border-gray-600"
                value={form.valid_until}
                onChange={e => setForm({...form, valid_until: e.target.value})}
                required
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Depósito Mínimo (R$)</label>
              <input
                type="number"
                step="0.01"
                className="w-full bg-gray-700 rounded px-3 py-2 text-sm border border-gray-600"
                value={form.min_deposit_amount}
                onChange={e => setForm({...form, min_deposit_amount: e.target.value})}
                placeholder="0.00"
              />
              <p className="text-xs text-gray-500 mt-1">Valor mínimo do depósito para usar o cupom</p>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Bônus Máximo (R$)</label>
              <input
                type="number"
                step="0.01"
                className="w-full bg-gray-700 rounded px-3 py-2 text-sm border border-gray-600"
                value={form.max_bonus_amount}
                onChange={e => setForm({...form, max_bonus_amount: e.target.value})}
                placeholder="Deixe vazio para sem limite"
              />
              <p className="text-xs text-gray-500 mt-1">Valor máximo do bônus (apenas para cupons percentuais)</p>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={form.is_withdrawable}
                onChange={e => setForm({...form, is_withdrawable: e.target.checked})}
                className="w-4 h-4"
              />
              <label className="text-sm text-gray-300">Bônus sacável (pode ser retirado)</label>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={form.is_active}
                onChange={e => setForm({...form, is_active: e.target.checked})}
                className="w-4 h-4"
              />
              <label className="text-sm text-gray-300">Ativo</label>
            </div>
          </div>
          <div className="mt-4 flex gap-2">
            <button
              onClick={createCoupon}
              disabled={loading}
              className="px-4 py-2 bg-[#d4af37] hover:bg-[#ffd700] text-black rounded disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Criando...' : 'Criar Cupom'}
            </button>
            <button
              onClick={() => {
                setShowForm(false);
                setForm({
                  code: '',
                  type: 'percentage',
                  value: '',
                  max_uses: '',
                  valid_from: '',
                  valid_until: '',
                  min_deposit_amount: '',
                  max_bonus_amount: '',
                  is_withdrawable: false,
                  is_active: true
                });
              }}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}

      {loading ? (
        <div className="text-center py-12">Carregando cupons...</div>
      ) : coupons.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          <p>Nenhum cupom cadastrado</p>
          <p className="text-sm mt-2">Clique em "Novo Cupom" para criar um</p>
        </div>
      ) : (
        <div className="bg-gray-800/60 rounded-lg border border-gray-700 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-700">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-semibold">Código</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Tipo</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Valor</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Usos</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Válido Até</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Status</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Ações</th>
              </tr>
            </thead>
            <tbody>
              {coupons.map((coupon) => (
                <tr key={coupon.id} className="border-t border-gray-700">
                  <td className="px-4 py-3 font-mono font-bold">{coupon.code}</td>
                  <td className="px-4 py-3">{coupon.type === 'percentage' ? 'Percentual' : 'Fixo'}</td>
                  <td className="px-4 py-3">
                    {coupon.type === 'percentage' ? `${coupon.value}%` : `R$ ${coupon.value}`}
                  </td>
                  <td className="px-4 py-3">{coupon.uses || 0} / {coupon.max_uses || '∞'}</td>
                  <td className="px-4 py-3">{new Date(coupon.valid_until).toLocaleDateString('pt-BR')}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded text-xs ${coupon.is_active ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'}`}>
                      {coupon.is_active ? 'Ativo' : 'Inativo'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <button className="text-blue-400 hover:text-blue-300 text-sm">Editar</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function TrackingTab({ token }: { token: string }) {
  const [configs, setConfigs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [form, setForm] = useState({
    name: '',
    type: 'webhook',
    url: '',
    pixel_id: '',
    access_token: '',
    api_key: '',
    is_active: true,
    metadata_json: ''
  });
  const [editingId, setEditingId] = useState<number | null>(null);

  const fetchConfigs = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_URL}/api/admin/tracking-configs`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Falha ao carregar configurações');
      setConfigs(await res.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConfigs();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');

    try {
      const url = editingId
        ? `${API_URL}/api/admin/tracking-configs/${editingId}`
        : `${API_URL}/api/admin/tracking-configs`;
      const method = editingId ? 'PUT' : 'POST';

      const res = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(form)
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Falha ao salvar configuração');
      }

      setMessage(editingId ? 'Configuração atualizada com sucesso!' : 'Configuração criada com sucesso!');
      setForm({
        name: '',
        type: 'webhook',
        url: '',
        pixel_id: '',
        access_token: '',
        api_key: '',
        is_active: true,
        metadata_json: ''
      });
      setEditingId(null);
      await fetchConfigs();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (config: any) => {
    setForm({
      name: config.name,
      type: config.type,
      url: config.url || '',
      pixel_id: config.pixel_id || '',
      access_token: config.access_token || '',
      api_key: config.api_key || '',
      is_active: config.is_active,
      metadata_json: config.metadata_json || ''
    });
    setEditingId(config.id);
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Tem certeza que deseja deletar esta configuração?')) return;

    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/tracking-configs/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Falha ao deletar');
      setMessage('Configuração deletada com sucesso!');
      await fetchConfigs();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Tracking de Conversões</h2>
      <p className="text-gray-400">Configure webhooks, pixels e APIs para rastrear conversões</p>

      {error && <div className="bg-red-500/20 border border-red-500 text-red-200 px-4 py-3 rounded">{error}</div>}
      {message && <div className="bg-green-500/20 border border-green-500 text-green-200 px-4 py-3 rounded">{message}</div>}

      <form onSubmit={handleSubmit} className="bg-gray-800 p-6 rounded-lg space-y-4">
        <h3 className="text-lg font-semibold">{editingId ? 'Editar' : 'Adicionar'} Configuração de Tracking</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Nome</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
              required
              placeholder="Ex: Facebook Pixel, Webhook Conversões"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Tipo</label>
            <select
              value={form.type}
              onChange={(e) => setForm({ ...form, type: e.target.value })}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
              required
            >
              <option value="webhook">Webhook</option>
              <option value="pixel">Pixel</option>
              <option value="api">API</option>
            </select>
          </div>
        </div>

        {form.type === 'webhook' && (
          <div>
            <label className="block text-sm font-medium mb-2">URL do Webhook *</label>
            <input
              type="url"
              value={form.url}
              onChange={(e) => setForm({ ...form, url: e.target.value })}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
              required={form.type === 'webhook'}
              placeholder="https://exemplo.com/webhook"
            />
          </div>
        )}

        {form.type === 'pixel' && (
          <>
            <div>
              <label className="block text-sm font-medium mb-2">Pixel ID *</label>
              <input
                type="text"
                value={form.pixel_id}
                onChange={(e) => setForm({ ...form, pixel_id: e.target.value })}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
                required={form.type === 'pixel'}
                placeholder="Ex: 123456789012345"
              />
              <p className="text-xs text-gray-400 mt-1">ID do Pixel (Facebook Pixel, Google Pixel, etc)</p>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Access Token (Token de Acesso) *</label>
              <input
                type="password"
                value={form.access_token}
                onChange={(e) => setForm({ ...form, access_token: e.target.value })}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
                required={form.type === 'pixel'}
                placeholder="Token de acesso da API de Conversões"
              />
              <p className="text-xs text-gray-400 mt-1">Token necessário para usar a API de Conversões (Facebook Conversions API, Google Conversions API, etc)</p>
            </div>
          </>
        )}

        {form.type === 'api' && (
          <>
            <div>
              <label className="block text-sm font-medium mb-2">Access Token</label>
              <input
                type="password"
                value={form.access_token}
                onChange={(e) => setForm({ ...form, access_token: e.target.value })}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
                placeholder="Token de acesso da API"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">API Key</label>
              <input
                type="password"
                value={form.api_key}
                onChange={(e) => setForm({ ...form, api_key: e.target.value })}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
                placeholder="Chave da API"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">URL da API (opcional)</label>
              <input
                type="url"
                value={form.url}
                onChange={(e) => setForm({ ...form, url: e.target.value })}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
                placeholder="https://api.exemplo.com"
              />
            </div>
          </>
        )}

        <div>
          <label className="block text-sm font-medium mb-2">Metadata JSON (opcional)</label>
          <textarea
            value={form.metadata_json}
            onChange={(e) => setForm({ ...form, metadata_json: e.target.value })}
            className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
            rows={3}
            placeholder='{"key": "value"}'
          />
        </div>

        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="is_active"
            checked={form.is_active}
            onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
            className="w-4 h-4"
          />
          <label htmlFor="is_active" className="text-sm">Ativo</label>
        </div>

        <div className="flex gap-2">
          <button
            type="submit"
            disabled={loading}
            className="bg-[#d4af37] hover:bg-[#ffd700] text-black px-4 py-2 rounded font-semibold disabled:opacity-50"
          >
            {editingId ? 'Atualizar' : 'Adicionar'}
          </button>
          {editingId && (
            <button
              type="button"
              onClick={() => {
                setForm({
                  name: '',
                  type: 'webhook',
                  url: '',
                  pixel_id: '',
                  access_token: '',
                  api_key: '',
                  is_active: true,
                  metadata_json: ''
                });
                setEditingId(null);
              }}
              className="bg-gray-600 hover:bg-gray-500 px-4 py-2 rounded"
            >
              Cancelar
            </button>
          )}
        </div>
      </form>

      <div className="bg-gray-800 rounded-lg overflow-hidden">
        <div className="p-4 border-b border-gray-700">
          <h3 className="text-lg font-semibold">Configurações de Tracking</h3>
        </div>
        {loading ? (
          <div className="p-4 text-center text-gray-400">Carregando...</div>
        ) : configs.length === 0 ? (
          <div className="p-4 text-center text-gray-400">Nenhuma configuração de tracking</div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-900">
              <tr>
                <th className="px-4 py-3 text-left">Nome</th>
                <th className="px-4 py-3 text-left">Tipo</th>
                <th className="px-4 py-3 text-left">Configuração</th>
                <th className="px-4 py-3 text-left">Status</th>
                <th className="px-4 py-3 text-left">Ações</th>
              </tr>
            </thead>
            <tbody>
              {configs.map((config) => (
                <tr key={config.id} className="border-b border-gray-700">
                  <td className="px-4 py-3">{config.name}</td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-1 rounded text-xs bg-blue-500/20 text-blue-300 capitalize">
                      {config.type}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-xs text-gray-400">
                      {config.type === 'webhook' && config.url && (
                        <div>URL: {config.url.substring(0, 50)}...</div>
                      )}
                      {config.type === 'pixel' && (
                        <>
                          {config.pixel_id && <div>Pixel ID: {config.pixel_id}</div>}
                          {config.access_token && <div>Token: ••••••••</div>}
                        </>
                      )}
                      {config.type === 'api' && (
                        <div>
                          {config.url && <div>URL: {config.url.substring(0, 30)}...</div>}
                          {config.access_token && <div>Token: ••••••••</div>}
                          {config.api_key && <div>API Key: ••••••••</div>}
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded text-xs ${config.is_active ? 'bg-green-500/20 text-green-300' : 'bg-gray-500/20 text-gray-300'}`}>
                      {config.is_active ? 'Ativo' : 'Inativo'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleEdit(config)}
                        className="text-[#d4af37] hover:text-[#ffd700] text-xs"
                      >
                        Editar
                      </button>
                      <button
                        onClick={() => handleDelete(config.id)}
                        className="text-red-400 hover:text-red-300 text-xs"
                      >
                        Deletar
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function WebhooksTab({ token }: { token: string }) {
  const [webhookUrl, setWebhookUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchWebhookUrl();
  }, []);

  const fetchWebhookUrl = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_URL}/api/admin/webhook-url`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Falha ao carregar URL do webhook');
      const data = await res.json();
      setWebhookUrl(data.webhook_url);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(webhookUrl);
    alert('URL copiada para a área de transferência!');
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Webhook Gatebox</h2>
        <p className="text-gray-400">Configure esta URL no painel da Gatebox para receber notificações de eventos</p>
      </div>

      {error && <div className="bg-red-500/20 border border-red-500 text-red-200 px-4 py-3 rounded">{error}</div>}

      {loading && <div className="bg-blue-500/20 border border-blue-500 text-blue-200 px-4 py-3 rounded">Carregando URL do webhook...</div>}

      <div className="bg-gray-800 rounded-lg p-6">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">URL do Webhook</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={webhookUrl}
                readOnly
                className="flex-1 bg-gray-700 border border-gray-600 rounded px-3 py-2 text-sm font-mono"
              />
              <button
                onClick={copyToClipboard}
                className="bg-[#d4af37] hover:bg-[#ffd700] text-black px-4 py-2 rounded font-semibold"
              >
                Copiar
              </button>
            </div>
          </div>

          <div className="bg-blue-500/10 border border-blue-500/30 rounded p-4">
            <h3 className="text-sm font-semibold text-blue-300 mb-2">Instruções:</h3>
            <ol className="list-decimal list-inside space-y-1 text-sm text-gray-300">
              <li>Acesse o painel da Gatebox</li>
              <li>Vá em Configurações → Webhooks</li>
              <li>Cole a URL acima no campo de webhook</li>
              <li>Salve as configurações</li>
            </ol>
          </div>

          <div className="bg-yellow-500/10 border border-yellow-500/30 rounded p-4">
            <p className="text-sm text-yellow-300">
              <strong>Importante:</strong> Esta URL recebe todos os eventos da Gatebox (depósitos, saques, etc.) e processa automaticamente conforme o tipo de evento.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
