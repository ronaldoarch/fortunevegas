import { X, Search, ChevronDown } from 'lucide-react';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  filters: { query: string; provider: string };
  onFiltersChange: (partial: { query?: string; provider?: string }) => void;
  providers?: string[];
}

export default function Sidebar({ isOpen, onClose, filters, onFiltersChange, providers = [] }: SidebarProps) {
  const popularGames = [
    'Fortune Tiger',
    'Aviator',
    'Fortune Snake',
    'Mine',
    'Fortune Rabbit',
    'Sugar Rush 1000',
    'Roleta Brasileira',
    'Bac Bo',
    'Football Studio',
    'Blackjack ao vivo',
  ];

  const liveGames = ['Jogo Ao Vivo', 'E-Sport'];

  return (
    <>
      {/* Overlay para mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={onClose}
        />
      )}
      
      {/* Sidebar */}
      <aside
        className={`fixed left-0 top-0 h-screen w-[220px] bg-[#0a4d3e] text-white z-[60] overflow-y-auto shadow-2xl transition-transform border-r border-[#0d5d4b] sidebar-custom md:fixed md:top-[60px] md:h-[calc(100vh-60px)] md:z-40 md:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        <div className="min-h-full pb-6">
          {/* Close button apenas no mobile */}
          <button
            onClick={onClose}
            className="md:hidden absolute top-3 right-3 p-2 hover:bg-[#0d5d4b] rounded transition-colors z-10"
            aria-label="Fechar menu"
          >
            <X size={20} />
          </button>

          {/* Promoções */}
          <div className="border-b border-[#0d5d4b]">
            <div className="px-4 py-3 space-y-3">
              {/* Cashback - com animação neon */}
              <button 
                onClick={() => window.location.href = '/depositar'}
                className="neon-button w-full relative bg-blue-600 rounded-lg p-4 text-left hover:bg-blue-700 transition-all duration-200 border-2 border-blue-500 overflow-hidden group"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-blue-500/0 via-blue-500/50 to-blue-500/0 animate-shimmer"></div>
                <div className="relative flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="text-xs text-blue-100 font-semibold uppercase mb-1.5 leading-tight">Cashback 25%</div>
                    <div className="text-base font-bold text-white leading-tight">Depositar</div>
                  </div>
                </div>
              </button>

              {/* Promoções - com animação neon */}
              <a
                href="/promocoes"
                className="neon-button block w-full relative bg-blue-600 rounded-lg p-4 text-left hover:bg-blue-700 transition-all duration-200 border-2 border-blue-500 overflow-hidden group"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-blue-500/0 via-blue-500/50 to-blue-500/0 animate-shimmer"></div>
                <div className="relative flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="text-xs text-blue-100 font-semibold uppercase mb-1.5 leading-tight">Acesse as</div>
                    <div className="text-base font-bold text-white leading-tight">Promoções</div>
                  </div>
                  <div className="text-3xl ml-2 flex-shrink-0">🎁</div>
                </div>
              </a>

              {/* Chat */}
              <button className="w-full bg-gray-800 border border-gray-600 rounded-lg p-4 text-left hover:bg-gray-700 transition-all duration-200 hover:border-gray-500">
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="text-xs text-gray-400 font-semibold uppercase mb-1.5 leading-tight">Chat ao vivo</div>
                    <div className="text-base font-bold text-white leading-tight">Suporte 24h</div>
                  </div>
                  <div className="text-3xl ml-2 flex-shrink-0">💬</div>
                </div>
              </button>
            </div>
          </div>

          {/* Barra de Pesquisa */}
          <div className="border-b border-[#0d5d4b] px-4 py-3">
            <div className="relative mb-2">
              <input
                type="text"
                placeholder="Pesquise um jogo..."
                value={filters.query}
                onChange={(e) => onFiltersChange({ query: e.target.value })}
                className="w-full bg-[#0d5d4b] border border-[#0a4d3e] rounded-lg px-3 py-2 pr-9 text-white text-xs placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#d4af37] focus:border-transparent transition-all duration-200"
              />
              <Search className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400" size={14} />
            </div>
            <div className="relative">
              <select
                value={filters.provider}
                onChange={(e) => onFiltersChange({ provider: e.target.value })}
                className="w-full bg-[#0d5d4b] border border-[#0a4d3e] rounded-lg px-3 py-2 text-white text-xs appearance-none focus:outline-none focus:ring-2 focus:ring-[#d4af37] focus:border-transparent transition-all duration-200 pr-8"
              >
                <option value="">Todos os provedores</option>
                {providers.map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
              <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" size={14} />
            </div>
          </div>

          {/* Jogos Populares */}
          <nav className="border-b border-[#0d5d4b]">
            <div className="flex items-center justify-between px-4 py-3 bg-[#0a4d3e]">
              <h3 className="text-sm font-bold text-[#d4af37] uppercase tracking-wide">Jogos Populares</h3>
            </div>
            <div className="px-4 pb-3">
              <ul className="space-y-1">
                {popularGames.map((game) => (
                  <li key={game}>
                    <a
                      href={`/jogo/${game.toLowerCase().replace(/\s+/g, '-')}`}
                      className="block px-1 py-2 rounded-md text-xs hover:bg-[#0d5d4b] transition-all duration-200 text-gray-100 hover:text-white"
                    >
                      {game}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          </nav>

          {/* Jogos Ao Vivo */}
          <nav className="border-b border-[#0d5d4b]">
            <div className="flex items-center justify-between px-4 py-3 bg-[#0a4d3e]">
              <h3 className="text-sm font-bold text-[#d4af37] uppercase tracking-wide">Ao Vivo</h3>
            </div>
            <div className="px-4 pb-3">
              <ul className="space-y-1">
                {liveGames.map((game) => (
                  <li key={game}>
                    <a
                      href={`/${game.toLowerCase().replace(/\s+/g, '-')}`}
                      className="block px-1 py-2 rounded-md text-xs hover:bg-[#0d5d4b] transition-all duration-200 text-gray-100 hover:text-white"
                    >
                      {game}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          </nav>

          {/* Links de Suporte */}
          <nav className="px-4 pt-4 pb-6">
            <ul className="space-y-1">
              <li>
                <a
                  href="/suporte"
                  className="block px-1 py-2 rounded-md text-xs hover:bg-[#0d5d4b] transition-all duration-200 text-gray-100 hover:text-white"
                >
                  Suporte Ao Vivo
                </a>
              </li>
              <li>
                <a
                  href="/promocoes"
                  className="block px-1 py-2 rounded-md text-xs hover:bg-[#0d5d4b] transition-all duration-200 text-gray-100 hover:text-white"
                >
                  Promoções
                </a>
              </li>
            </ul>
          </nav>
        </div>
      </aside>
    </>
  );
}
