import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import AppRouter from './AppRouter.tsx'
import { AuthProvider } from './contexts/AuthContext.tsx'
import { loadAndInitPixel } from './utils/pixelTracker'

// Backend FastAPI - usa variável de ambiente ou fallback para localhost
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Inicializar pixel do Facebook ao carregar a aplicação
loadAndInitPixel(API_URL);

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthProvider>
      <AppRouter />
    </AuthProvider>
  </StrictMode>,
)
