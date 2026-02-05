import { useState, useEffect, useRef } from 'react';
import { Search, ChevronDown } from 'lucide-react';

interface SearchBarProps {
  query?: string;
  provider?: string;
  providers?: string[];
  onFiltersChange?: (filters: { query?: string; provider?: string }) => void;
}

export default function SearchBar({ query = '', provider = '', providers = [], onFiltersChange }: SearchBarProps) {
  const [searchQuery, setSearchQuery] = useState(query);
  const [showProviderDropdown, setShowProviderDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Sincronizar com props externas
  useEffect(() => {
    setSearchQuery(query);
  }, [query]);

  // Debounce na busca
  useEffect(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    debounceTimerRef.current = setTimeout(() => {
      onFiltersChange?.({ query: searchQuery });
    }, 300); // 300ms de debounce

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [searchQuery, onFiltersChange]);

  // Fechar dropdown ao clicar fora
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowProviderDropdown(false);
      }
    };

    if (showProviderDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showProviderDropdown]);

  const handleProviderSelect = (selectedProvider: string) => {
    onFiltersChange?.({ provider: selectedProvider });
    setShowProviderDropdown(false);
  };

  return (
    <div className="w-full bg-gradient-to-b from-[#0a0e0f] to-[#0d1415] py-4 md:py-5 px-3 md:px-4 border-y border-gray-800/50">
      <div className="container mx-auto">
        <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center">
          <div className="flex-1 relative">
            <input
              type="text"
              placeholder="Pesquise um jogo..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-gray-800/80 backdrop-blur-sm border border-gray-700/50 rounded-xl px-4 md:px-5 py-3 md:py-3.5 pr-11 md:pr-12 text-white placeholder-gray-400 text-sm md:text-base focus:outline-none focus:ring-2 focus:ring-[#d4af37]/50 focus:border-[#d4af37]/50 transition-all duration-200"
            />
            <Search className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
          </div>
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setShowProviderDropdown(!showProviderDropdown)}
              className="w-full sm:w-auto bg-gray-800/80 backdrop-blur-sm border border-gray-700/50 rounded-xl px-4 md:px-5 py-3 md:py-3.5 text-white flex items-center justify-between sm:justify-center gap-2 hover:bg-gray-700/80 hover:border-gray-600 transition-all duration-200 text-sm md:text-base whitespace-nowrap hover:scale-105"
            >
              <span>{provider || 'Provedor'}</span>
              <ChevronDown size={18} className={`md:w-5 md:h-5 transition-transform ${showProviderDropdown ? 'rotate-180' : ''}`} />
            </button>
            {showProviderDropdown && (
              <div className="absolute top-full left-0 right-0 sm:right-auto mt-2 bg-gray-800 border border-gray-700 rounded-xl shadow-xl z-50 max-h-60 overflow-y-auto">
                <button
                  onClick={() => handleProviderSelect('')}
                  className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-700 transition-colors ${!provider ? 'bg-gray-700/50' : ''}`}
                >
                  Todos os provedores
                </button>
                {providers.map((p) => (
                  <button
                    key={p}
                    onClick={() => handleProviderSelect(p)}
                    className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-700 transition-colors ${provider === p ? 'bg-gray-700/50' : ''}`}
                  >
                    {p}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
