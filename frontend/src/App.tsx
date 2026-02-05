import { useCallback, useEffect, useState } from 'react';
import Header from './components/Header';
import HeroBanner from './components/HeroBanner';
import SearchBar from './components/SearchBar';
import NovidadesSection from './components/NovidadesSection';
import Sidebar from './components/Sidebar';
import Footer from './components/Footer';
import BottomNav from './components/BottomNav';
import ChatWidget from './components/ChatWidget';
import LoginModal from './components/LoginModal';
import RegisterModal from './components/RegisterModal';
import { applyBrandAssets, applyThemeToDocument, initThemeAndBrandFromStorage } from './utils/themeManager';

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [loginOpen, setLoginOpen] = useState(false);
  const [registerOpen, setRegisterOpen] = useState(false);
  const [filters, setFilters] = useState({ query: '', provider: '' });
  const [providers, setProviders] = useState<string[]>([]);

  const handleFiltersChange = (partial: { query?: string; provider?: string }) => {
    setFilters((prev) => ({ ...prev, ...partial }));
  };

  const handleProvidersLoaded = useCallback((items: string[]) => {
    setProviders(items);
  }, []);

  useEffect(() => {
    initThemeAndBrandFromStorage();
    const onStorage = (e: StorageEvent) => {
      if (!e.key) return;
      if (['fv_theme_list', 'fv_theme_active'].includes(e.key)) {
        applyThemeToDocument();
      }
      if (e.key === 'fv_brand_assets') {
        applyBrandAssets();
      }
    };
    window.addEventListener('storage', onStorage);
    return () => window.removeEventListener('storage', onStorage);
  }, []);

  return (
    <div className="min-h-screen bg-[#0a0e0f] text-white">
      <Header 
        onMenuClick={() => setSidebarOpen(true)}
        onLoginClick={() => {
          setRegisterOpen(false);
          setLoginOpen(true);
        }}
        onRegisterClick={() => {
          setLoginOpen(false);
          setRegisterOpen(true);
        }}
      />
      <div className="flex">
        <Sidebar
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
          filters={filters}
          onFiltersChange={handleFiltersChange}
          providers={providers}
        />
        <div className="flex-1 min-w-0 md:ml-[220px]">
          <main className="pb-20 md:pb-0">
            <HeroBanner />
            <SearchBar 
              query={filters.query}
              provider={filters.provider}
              providers={providers}
              onFiltersChange={handleFiltersChange}
            />
            <NovidadesSection
              filters={filters}
              onProvidersLoaded={handleProvidersLoaded}
            />
          </main>
          <Footer />
        </div>
      </div>
      <BottomNav />
      <ChatWidget />
      
      {/* Modais */}
      <LoginModal 
        isOpen={loginOpen}
        onClose={() => setLoginOpen(false)}
        onSwitchToRegister={() => {
          setLoginOpen(false);
          setRegisterOpen(true);
        }}
      />
      <RegisterModal 
        isOpen={registerOpen}
        onClose={() => setRegisterOpen(false)}
        onSwitchToLogin={() => {
          setRegisterOpen(false);
          setLoginOpen(true);
        }}
      />
    </div>
  );
}

export default App;
