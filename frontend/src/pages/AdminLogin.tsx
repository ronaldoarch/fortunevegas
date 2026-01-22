import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

// Backend FastAPI - usa variável de ambiente ou fallback para localhost
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function AdminLogin() {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true);

  // Verificar se o usuário logado é admin
  useEffect(() => {
    const checkAdminAccess = async () => {
      const userToken = localStorage.getItem('user_token');
      
      // Se não há token de usuário, redirecionar para home
      if (!userToken) {
        navigate('/', { replace: true });
        return;
      }

      try {
        // Verificar se o usuário logado é admin
        const response = await fetch(`${API_URL}/api/auth/me`, {
          headers: {
            'Authorization': `Bearer ${userToken}`
          }
        });

        if (response.ok) {
          const userData = await response.json();
          // Se não for admin, redirecionar para home
          if (userData.role !== 'admin') {
            navigate('/', { replace: true });
            return;
          }
          // Se for admin, permitir acesso à página de login
        } else {
          // Token inválido, redirecionar para home
          navigate('/', { replace: true });
          return;
        }
      } catch (err) {
        // Erro ao verificar, redirecionar para home
        navigate('/', { replace: true });
        return;
      } finally {
        setCheckingAuth(false);
      }
    };

    checkAdminAccess();
  }, [navigate]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (response.ok) {
        // Verificar se o usuário é admin antes de permitir login
        const userResponse = await fetch(`${API_URL}/api/auth/me`, {
          headers: {
            'Authorization': `Bearer ${data.access_token}`
          }
        });

        if (userResponse.ok) {
          const userData = await userResponse.json();
          if (userData.role === 'admin') {
            localStorage.setItem('admin_token', data.access_token);
            navigate('/admin');
          } else {
            setError('Acesso negado. Apenas administradores podem acessar o painel.');
          }
        } else {
          setError('Erro ao verificar permissões');
        }
      } else {
        setError(data.detail || 'Erro ao fazer login');
      }
    } catch (err) {
      setError('Erro de conexão com o servidor');
    } finally {
      setLoading(false);
    }
  };

  // Mostrar loading enquanto verifica autenticação
  if (checkingAuth) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white">Verificando acesso...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
      <div className="bg-gray-800 rounded-2xl border border-gray-700 w-full max-w-md p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-black text-white mb-2">
            FORTUNE <span className="text-[#d4af37]">VEGAS</span>
          </h1>
          <p className="text-gray-400">Painel Administrativo</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-6">
          {error && (
            <div className="bg-red-500/20 border border-red-500 text-red-400 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          <div>
            <label className="block text-gray-300 text-sm mb-2">Usuário</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-[#d4af37] focus:border-transparent"
              placeholder="Digite seu usuário"
              required
            />
          </div>

          <div>
            <label className="block text-gray-300 text-sm mb-2">Senha</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-[#d4af37] focus:border-transparent"
              placeholder="Digite sua senha"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-[#ff6b35] hover:bg-[#ff7b35] disabled:bg-gray-600 text-white font-bold py-3 rounded-lg transition-colors"
          >
            {loading ? 'Entrando...' : 'Entrar'}
          </button>
        </form>
      </div>
    </div>
  );
}
