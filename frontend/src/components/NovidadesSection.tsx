import { useEffect, useMemo, useRef, useState } from 'react';
import { ChevronLeft, ChevronRight, Heart } from 'lucide-react';

interface Game {
  id: string;
  title: string;
  provider?: string;
  banner?: string;
  code?: string;
}

type Filters = {
  query?: string;
  provider?: string;
};

interface NovidadesSectionProps {
  filters?: Filters;
  onProvidersLoaded?: (providers: string[]) => void;
}

// Backend expõe /api/public/games via FastAPI - usa variável de ambiente ou fallback
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_URL = `${API_BASE_URL}/api/public/games`;

export default function NovidadesSection({ filters, onProvidersLoaded }: NovidadesSectionProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [gamesPerPage, setGamesPerPage] = useState(4);
  const [games, setGames] = useState<Game[]>([]);
  const [loading, setLoading] = useState(true);
  const providersLoadedRef = useRef(false);

  useEffect(() => {
    const updateGamesPerPage = () => {
      if (window.innerWidth < 640) {
        setGamesPerPage(2);
      } else if (window.innerWidth < 1024) {
        setGamesPerPage(3);
      } else {
        setGamesPerPage(4);
      }
    };

    updateGamesPerPage();
    window.addEventListener('resize', updateGamesPerPage);
    return () => window.removeEventListener('resize', updateGamesPerPage);
  }, []);

  const [gamesByProvider, setGamesByProvider] = useState<Record<string, { provider_name: string; games: Game[] }>>({});

  useEffect(() => {
    const fetchGames = async () => {
      setLoading(true);
      try {
        const res = await fetch(API_URL);
        if (!res.ok) throw new Error('Falha ao carregar jogos');
        const data = await res.json();
        
        // Se há games_by_provider, usar essa estrutura (configurada pelo admin)
        if (data.games_by_provider && Object.keys(data.games_by_provider).length > 0) {
          const providerMap: Record<string, { provider_name: string; games: Game[] }> = {};
          Object.entries(data.games_by_provider).forEach(([providerCode, providerData]: [string, any]) => {
            providerMap[providerCode] = {
              provider_name: providerData.provider_name || providerCode,
              games: (providerData.games || []).map((g: any, idx: number) => ({
                id: g.code || g.name || String(idx),
                title: g.name || g.title || 'Jogo',
                provider: providerCode,
                banner: g.banner,
                code: g.code,
              }))
            };
          });
          setGamesByProvider(providerMap);
          
          // Para compatibilidade, também manter lista plana
          const allGames: Game[] = [];
          Object.values(providerMap).forEach(provider => {
            allGames.push(...provider.games);
          });
          setGames(allGames);
          
          if (!providersLoadedRef.current) {
            const providerNames = Object.values(providerMap).map(p => p.provider_name);
            onProvidersLoaded?.(providerNames);
            providersLoadedRef.current = true;
          }
        } else {
          // Fallback: usar formato antigo (lista plana)
          const mapped: Game[] = (data.games || []).map((g: any, idx: number) => ({
            id: g.code || g.name || String(idx),
            title: g.name || g.title || 'Jogo',
            provider: g.provider,
            banner: g.banner,
            code: g.code,
          }));
          setGames(mapped);
          setGamesByProvider({});
          
          if (!providersLoadedRef.current) {
            const uniqueProviders = Array.from(
              new Set(
                mapped
                  .map((g) => g.provider?.trim())
                  .filter((p): p is string => Boolean(p))
              )
            ).sort((a, b) => a.localeCompare(b));
            onProvidersLoaded?.(uniqueProviders);
            providersLoadedRef.current = true;
          }
        }
      } catch (err) {
        console.error('Erro ao buscar jogos', err);
      } finally {
        setLoading(false);
      }
    };
    fetchGames();
  }, []);

  const normalizedQuery = (filters?.query || '').trim().toLowerCase();
  const normalizedProvider = (filters?.provider || '').trim().toLowerCase();

  useEffect(() => {
    setCurrentIndex(0);
  }, [normalizedQuery, normalizedProvider]);

  const filteredGames = useMemo(() => {
    return games.filter((game) => {
      const matchesProvider = normalizedProvider
        ? (game.provider || '').toLowerCase() === normalizedProvider
        : true;
      const matchesQuery = normalizedQuery
        ? (game.title || '').toLowerCase().includes(normalizedQuery) ||
          (game.code || '').toLowerCase().includes(normalizedQuery) ||
          (game.provider || '').toLowerCase().includes(normalizedQuery)
        : true;
      return matchesProvider && matchesQuery;
    });
  }, [games, normalizedProvider, normalizedQuery]);

  const maxIndex = Math.max(0, filteredGames.length - gamesPerPage);

  const nextSlide = () => {
    setCurrentIndex((prev) => Math.min(prev + 1, maxIndex));
  };

  const prevSlide = () => {
    setCurrentIndex((prev) => Math.max(prev - 1, 0));
  };

  const displayedGames = filteredGames.slice(currentIndex, currentIndex + gamesPerPage);

  // Se há games_by_provider configurado, usar ele (já ordenado pelo admin)
  // Caso contrário, agrupar manualmente pelos jogos filtrados
  const providerEntries = useMemo(() => {
    if (Object.keys(gamesByProvider).length > 0) {
      // Usar estrutura configurada pelo admin
      return Object.entries(gamesByProvider).map(([_providerCode, providerData]) => {
        // Aplicar filtros aos jogos do provedor
        let filteredProviderGames = providerData.games.filter((game) => {
          const matchesProvider = normalizedProvider
            ? (game.provider || '').toLowerCase() === normalizedProvider
            : true;
          const matchesQuery = normalizedQuery
            ? (game.title || '').toLowerCase().includes(normalizedQuery) ||
              (game.code || '').toLowerCase().includes(normalizedQuery) ||
              (game.provider || '').toLowerCase().includes(normalizedQuery)
            : true;
          return matchesProvider && matchesQuery;
        });
        return [providerData.provider_name, filteredProviderGames] as [string, Game[]];
      }).filter(([_, games]) => games.length > 0); // Remover provedores sem jogos após filtro
    } else {
      // Fallback: agrupar manualmente
      const grouped = filteredGames.reduce<Record<string, Game[]>>((acc, game) => {
        const key = (game.provider || 'Outros').trim() || 'Outros';
        if (!acc[key]) acc[key] = [];
        acc[key].push(game);
        return acc;
      }, {});
      return Object.entries(grouped).sort((a, b) => a[0].localeCompare(b[0]));
    }
  }, [gamesByProvider, filteredGames, normalizedProvider, normalizedQuery]);

  const renderGameCard = (game: Game) => (
    <a
      key={game.id}
      href={`/jogo/${game.code || game.id}`}
      className="group relative bg-gradient-to-br from-gray-800/90 via-gray-900/90 to-gray-950/90 backdrop-blur-sm rounded-2xl overflow-hidden border border-gray-700/50 hover:border-[#d4af37]/60 transition-all duration-300 hover:scale-105 hover:shadow-2xl hover:shadow-[#d4af37]/20"
    >
      <div className="aspect-[3/4] bg-gradient-to-br from-gray-700/50 to-gray-800/50 flex items-center justify-center relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-[#d4af37]/0 to-transparent group-hover:from-[#d4af37]/10 group-hover:to-transparent transition-all duration-300"></div>
        {game.banner ? (
          <img
            src={game.banner}
            alt={game.title}
            className="absolute inset-0 w-full h-full object-cover"
          />
        ) : (
          <div className="text-5xl md:text-6xl group-hover:scale-125 group-hover:rotate-12 transition-all duration-300 relative z-10">🎮</div>
        )}
        <button
          className="absolute top-3 right-3 p-2 bg-black/70 backdrop-blur-sm rounded-full hover:bg-red-600/80 transition-all duration-200 opacity-0 group-hover:opacity-100 z-20 hover:scale-110"
          onClick={(e) => {
            e.preventDefault();
          }}
          aria-label="Adicionar aos favoritos"
        >
          <Heart size={18} className="text-white" />
        </button>
      </div>
      <div className="p-4 bg-gradient-to-b from-gray-900/90 to-gray-950/90">
        <h3 className="text-white font-bold text-sm md:text-base truncate group-hover:text-[#d4af37] transition-colors duration-300">{game.title}</h3>
        {game.provider && (
          <p className="text-gray-400 text-xs mt-1.5 font-medium uppercase tracking-wide">{game.provider}</p>
        )}
      </div>
    </a>
  );

  return (
    <div className="w-full bg-gradient-to-b from-[#0d1415] to-[#0a0e0f] py-10 md:py-12 px-4">
      <div className="container mx-auto">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-6 md:mb-8 gap-4">
          <h2 className="text-2xl sm:text-3xl md:text-4xl font-black text-white flex items-center gap-3">
            <span className="bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">NOVIDADES</span>
            <span className="text-3xl md:text-4xl animate-pulse">🔥</span>
          </h2>
          <div className="flex items-center gap-3 md:gap-4 w-full sm:w-auto justify-between sm:justify-end">
            <div className="flex gap-2">
              <button
                onClick={prevSlide}
                disabled={currentIndex === 0}
                className="p-2.5 bg-gray-800/80 backdrop-blur-sm rounded-xl hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-200 hover:scale-110 border border-gray-700/50"
                aria-label="Anterior"
              >
                <ChevronLeft size={20} className="text-white" />
              </button>
              <button
                onClick={nextSlide}
                disabled={currentIndex >= maxIndex}
                className="p-2.5 bg-gray-800/80 backdrop-blur-sm rounded-xl hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-200 hover:scale-110 border border-gray-700/50"
                aria-label="Próximo"
              >
                <ChevronRight size={20} className="text-white" />
              </button>
            </div>
            <a
              href="/novidades"
              className="text-[#d4af37] hover:text-[#ffd700] transition-all duration-200 font-bold flex items-center gap-2 text-sm md:text-base hover:gap-3"
            >
              Ver todos <span className="text-lg">›</span>
            </a>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-6">
          {loading && games.length === 0 && (
            <>
              <div className="aspect-[3/4] bg-gray-800/50 rounded-2xl animate-pulse"></div>
              <div className="aspect-[3/4] bg-gray-800/50 rounded-2xl animate-pulse"></div>
              <div className="aspect-[3/4] bg-gray-800/50 rounded-2xl animate-pulse"></div>
            </>
          )}
          {!loading && displayedGames.map(renderGameCard)}
          {!loading && filteredGames.length === 0 && (
            <div className="col-span-2 sm:col-span-3 lg:col-span-4 text-gray-400 text-sm">
              Nenhum jogo encontrado para os filtros selecionados.
              </div>
                )}
              </div>

        {!loading && providerEntries.length > 0 && (
          <div className="mt-10 md:mt-12 space-y-8">
            <div className="flex items-center justify-between">
              <h3 className="text-xl md:text-2xl font-black text-white flex items-center gap-3">
                <span className="bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">POR PROVEDOR</span>
              </h3>
              <span className="text-sm text-gray-400">
                {providerEntries.length} {providerEntries.length === 1 ? 'provedor' : 'provedores'}
              </span>
            </div>

            <div className="space-y-6">
              {providerEntries.map(([providerName, providerGames]) => (
                <div key={providerName} className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-1.5 h-8 rounded-full bg-[#d4af37]" />
                      <h4 className="text-lg md:text-xl font-extrabold uppercase tracking-wide">{providerName}</h4>
                      <span className="text-xs text-gray-400">({providerGames.length})</span>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 md:gap-6">
                    {providerGames.map(renderGameCard)}
                  </div>
                </div>
          ))}
        </div>
          </div>
        )}
      </div>
    </div>
  );
}
