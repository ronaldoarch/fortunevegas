import { useState, useEffect } from 'react';

const API_URL = import.meta.env.VITE_API_URL || 'https://api.fortunevegas.site';

export default function Footer() {
  const [logoUrl, setLogoUrl] = useState<string | null>(null);

  useEffect(() => {
    const fetchLogo = async () => {
      try {
        const res = await fetch(`${API_URL}/api/public/media/logo`);
        if (res.ok) {
          const data = await res.json();
          if (data.url) {
            const url = data.url.startsWith('/api') 
              ? `${API_URL}${data.url}`
              : `${API_URL}/api/public/media${data.url}`;
            setLogoUrl(url);
          }
        }
      } catch (err) {
        console.error('Erro ao buscar logo:', err);
      }
    };
    fetchLogo();
    
    // Polling para atualizar logo (a cada 5 segundos)
    const interval = setInterval(fetchLogo, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <footer className="w-full bg-[#0a0e0f] border-t border-gray-800 py-6 md:py-8 px-4 mt-8 md:mt-12">
      <div className="container mx-auto">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 md:gap-8 mb-6 md:mb-8">
          {/* Apostas */}
          <div>
            <h3 className="text-white font-bold mb-3 md:mb-4 text-base md:text-lg">Apostas</h3>
            <ul className="space-y-1.5 md:space-y-2">
              <li>
                <a href="/apostas-esportivas" className="text-gray-400 hover:text-[#d4af37] transition-colors text-sm md:text-base">
                  Apostas Esportivas
                </a>
              </li>
              <li>
                <a href="/promocoes" className="text-gray-400 hover:text-[#d4af37] transition-colors text-sm md:text-base">
                  Promoções
                </a>
              </li>
            </ul>
          </div>

          {/* Políticas */}
          <div>
            <h3 className="text-white font-bold mb-3 md:mb-4 text-base md:text-lg">Políticas</h3>
            <ul className="space-y-1.5 md:space-y-2">
              <li>
                <a href="/termos-e-condicoes" className="text-gray-400 hover:text-[#d4af37] transition-colors text-sm md:text-base">
                  Termos e Condições
                </a>
              </li>
              <li>
                <a href="/politica-de-privacidade" className="text-gray-400 hover:text-[#d4af37] transition-colors text-sm md:text-base">
                  Política de Privacidade
                </a>
              </li>
              <li>
                <a href="/politica-kyc" className="text-gray-400 hover:text-[#d4af37] transition-colors text-sm md:text-base">
                  Política KYC
                </a>
              </li>
              <li>
                <a href="/jogo-responsavel" className="text-gray-400 hover:text-[#d4af37] transition-colors text-sm md:text-base">
                  Jogo Responsável
                </a>
              </li>
            </ul>
          </div>

          {/* Pagamento */}
          <div className="col-span-2 md:col-span-1">
            <h3 className="text-white font-bold mb-3 md:mb-4 text-base md:text-lg">Pagamento</h3>
            <ul className="space-y-1.5 md:space-y-2">
              <li>
                <span className="text-gray-400 text-sm md:text-base">PIX</span>
              </li>
            </ul>
          </div>

          {/* Logos */}
          <div className="col-span-2 md:col-span-1">
            <h3 className="text-white font-bold mb-3 md:mb-4 text-base md:text-lg">Certificações</h3>
            <div className="flex flex-col gap-3 md:gap-4">
              <div className="w-20 h-20 md:w-24 md:h-24 bg-gray-800 rounded flex items-center justify-center overflow-hidden">
                {logoUrl ? (
                  <img 
                    src={logoUrl} 
                    alt="Fortune Vegas Logo" 
                    className="w-full h-full object-contain p-2"
                  />
                ) : (
                  <span className="text-gray-400 text-xs text-center">Logo</span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Informações Legais */}
        <div className="border-t border-gray-800 pt-4 md:pt-6 mt-4 md:mt-6">
          <p className="text-gray-500 text-xs md:text-sm text-center mb-4 leading-relaxed">
            Meta é operado pela Enigma Digital Solutions Limitada. Registro: 3102916990. 
            Endereço: Ofident Building, Office No.3, San Jose, Costa Rica. 
            Licenciado e regulamentado pelo Governo da Ilha Autônoma de Anjouan, 
            União das Comores, sob a Licença No. ALSI-202412045-F12.
          </p>
          <div className="flex flex-wrap justify-center gap-3 md:gap-4 mb-4">
            <div className="w-12 h-12 md:w-16 md:h-16 bg-gray-800 rounded flex items-center justify-center">
              <span className="text-gray-400 text-[10px] md:text-xs">GT</span>
            </div>
            <div className="w-12 h-12 md:w-16 md:h-16 bg-gray-800 rounded flex items-center justify-center">
              <span className="text-gray-400 text-[10px] md:text-xs">Meta</span>
            </div>
            <div className="w-24 h-12 md:w-32 md:h-16 bg-gray-800 rounded flex items-center justify-center">
              <span className="text-gray-400 text-[10px] md:text-xs text-center">BeGambleAware</span>
            </div>
          </div>
          <p className="text-gray-500 text-[10px] md:text-xs text-center">
            © {new Date().getFullYear()} Fortune Vegas. Todos os direitos reservados.
          </p>
        </div>
      </div>
    </footer>
  );
}
