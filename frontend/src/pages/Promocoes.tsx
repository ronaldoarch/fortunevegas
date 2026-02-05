import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Gift, Calendar, Tag, ArrowRight } from 'lucide-react';
import Header from '../components/Header';
import Footer from '../components/Footer';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Promotion {
  id: number;
  title: string;
  description: string | null;
  type: string;
  bonus_value: number;
  bonus_type: string;
  min_deposit_amount: number;
  max_bonus_amount: number | null;
  banner_url: string | null;
  is_first_deposit_only: boolean;
  start_date: string;
  end_date: string;
}

export default function Promocoes() {
  const navigate = useNavigate();
  const [promotions, setPromotions] = useState<Promotion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchPromotions();
  }, []);

  const fetchPromotions = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_URL}/api/public/promotions`);
      if (!res.ok) throw new Error('Falha ao carregar promoções');
      const data = await res.json();
      setPromotions(data);
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar promoções');
    } finally {
      setLoading(false);
    }
  };

  const formatBonus = (promo: Promotion) => {
    if (promo.bonus_type === 'percentage') {
      return `${promo.bonus_value}%`;
    }
    return `R$ ${promo.bonus_value.toFixed(2).replace('.', ',')}`;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  const getTypeLabel = (type: string) => {
    const types: { [key: string]: string } = {
      'bonus': 'Bônus',
      'cashback': 'Cashback',
      'free_spins': 'Rodadas Grátis',
      'tournament': 'Torneio'
    };
    return types[type] || type;
  };

  return (
    <div className="min-h-screen bg-[#0a0e0f] text-white">
      <Header 
        onMenuClick={() => {}}
        onLoginClick={() => navigate('/conta')}
        onRegisterClick={() => navigate('/conta')}
      />
      
      <main className="pt-20 pb-20 md:pb-0">
        <div className="container mx-auto px-4 py-8 max-w-6xl">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="flex items-center justify-center gap-3 mb-4">
              <Gift className="text-[#d4af37]" size={32} />
              <h1 className="text-3xl md:text-4xl font-bold">Promoções</h1>
            </div>
            <p className="text-gray-400 text-sm md:text-base">
              Confira todas as promoções disponíveis e aproveite!
            </p>
          </div>

          {/* Loading */}
          {loading && (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#d4af37] mx-auto mb-4"></div>
              <p className="text-gray-400">Carregando promoções...</p>
            </div>
          )}

          {/* Error */}
          {error && !loading && (
            <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4 mb-6">
              <p className="text-red-400">{error}</p>
            </div>
          )}

          {/* Empty State */}
          {!loading && !error && promotions.length === 0 && (
            <div className="text-center py-12">
              <Gift className="text-gray-600 mx-auto mb-4" size={48} />
              <p className="text-gray-400 text-lg">Nenhuma promoção disponível no momento</p>
              <p className="text-gray-500 text-sm mt-2">Volte em breve para conferir novas ofertas!</p>
            </div>
          )}

          {/* Promotions Grid */}
          {!loading && promotions.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {promotions.map((promo) => (
                <div
                  key={promo.id}
                  className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl overflow-hidden border border-gray-700 hover:border-[#d4af37]/50 transition-all duration-300 hover:shadow-xl hover:shadow-[#d4af37]/20 group"
                >
                  {/* Banner */}
                  {promo.banner_url && (
                    <div className="relative h-48 overflow-hidden">
                      <img
                        src={`${API_URL}${promo.banner_url}`}
                        alt={promo.title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      />
                      <div className="absolute top-3 right-3">
                        <span className="bg-[#d4af37] text-black text-xs font-bold px-2 py-1 rounded uppercase">
                          {getTypeLabel(promo.type)}
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Content */}
                  <div className="p-6">
                    <div className="flex items-start justify-between mb-3">
                      <h3 className="text-xl font-bold text-white group-hover:text-[#d4af37] transition-colors">
                        {promo.title}
                      </h3>
                    </div>

                    {promo.description && (
                      <p className="text-gray-400 text-sm mb-4 line-clamp-2">
                        {promo.description}
                      </p>
                    )}

                    {/* Bonus Info */}
                    <div className="bg-[#0a4d3e]/50 rounded-lg p-3 mb-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Tag className="text-[#d4af37]" size={16} />
                        <span className="text-sm text-gray-300">Bônus:</span>
                        <span className="text-lg font-bold text-[#d4af37]">
                          {formatBonus(promo)}
                        </span>
                      </div>
                      
                      {promo.min_deposit_amount > 0 && (
                        <p className="text-xs text-gray-400">
                          Depósito mínimo: R$ {promo.min_deposit_amount.toFixed(2).replace('.', ',')}
                        </p>
                      )}
                      
                      {promo.max_bonus_amount && (
                        <p className="text-xs text-gray-400">
                          Bônus máximo: R$ {promo.max_bonus_amount.toFixed(2).replace('.', ',')}
                        </p>
                      )}

                      {promo.is_first_deposit_only && (
                        <p className="text-xs text-[#d4af37] font-semibold mt-1">
                          ⭐ Apenas para primeiro depósito
                        </p>
                      )}
                    </div>

                    {/* Dates */}
                    <div className="flex items-center gap-2 text-xs text-gray-500 mb-4">
                      <Calendar size={14} />
                      <span>
                        {formatDate(promo.start_date)} - {formatDate(promo.end_date)}
                      </span>
                    </div>

                    {/* Action Button */}
                    <button
                      onClick={() => navigate('/depositar')}
                      className="w-full bg-[#d4af37] hover:bg-[#ffd700] text-black font-bold py-3 rounded-lg transition-colors flex items-center justify-center gap-2"
                    >
                      Aproveitar Promoção
                      <ArrowRight size={18} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}
