import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import App from './App';
import Admin from './pages/Admin';
import AdminLogin from './pages/AdminLogin';
import Profile from './pages/Profile';
import Game from './pages/Game';
import Depositar from './pages/Depositar';
import Sacar from './pages/Sacar';
import Afiliado from './pages/Afiliado';
import Gerente from './pages/Gerente';
import Historico from './pages/Historico';
import Apostas from './pages/Apostas';

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/conta" element={<Profile />} />
        <Route path="/depositar" element={<Depositar />} />
        <Route path="/sacar" element={<Sacar />} />
        <Route path="/jogo/:gameCode" element={<Game />} />
        <Route path="/afiliado" element={<Afiliado />} />
        <Route path="/gerente" element={<Gerente />} />
        <Route path="/historico" element={<Historico />} />
        <Route path="/apostas" element={<Apostas />} />
        <Route path="/admin/login" element={<AdminLogin />} />
        <Route path="/admin" element={<Admin />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
