import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { ArrowLeft, Wallet, AlertCircle, CheckCircle } from 'lucide-react';

// Backend FastAPI - usa variável de ambiente ou fallback para localhost
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Sacar() {
  const navigate = useNavigate();
  const { user, token } = useAuth();
  const [amount, setAmount] = useState('');
  const [pixKey, setPixKey] = useState('');
  const [pixKeyType, setPixKeyType] = useState('CPF');
  const [documentValidation, setDocumentValidation] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [withdrawalData, setWithdrawalData] = useState<{
    transaction_id: string;
    amount: number;
  } | null>(null);

  useEffect(() => {
    if (!token || !user) {
      navigate('/conta');
      return;
    }
  }, [token, user, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    setSuccess(false);

    try {
      const amountValue = parseFloat(amount.replace(',', '.'));
      
      if (isNaN(amountValue) || amountValue <= 0) {
        setError('Valor inválido. Digite um valor maior que zero.');
        setLoading(false);
        return;
      }

      if (amountValue < 10) {
        setError('Valor mínimo de saque é R$ 10,00');
        setLoading(false);
        return;
      }

      if (user.balance < amountValue) {
        setError('Saldo insuficiente para realizar o saque.');
        setLoading(false);
        return;
      }

      if (!pixKey || pixKey.trim().length === 0) {
        setError('Por favor, informe a chave PIX.');
        setLoading(false);
        return;
      }

      // Validar formato da chave PIX baseado no tipo
      if (pixKeyType === 'CPF' || pixKeyType === 'CNPJ') {
        const cleanKey = pixKey.replace(/\D/g, '');
        if (pixKeyType === 'CPF' && cleanKey.length !== 11) {
          setError('CPF deve conter 11 dígitos.');
          setLoading(false);
          return;
        }
        if (pixKeyType === 'CNPJ' && cleanKey.length !== 14) {
          setError('CNPJ deve conter 14 dígitos.');
          setLoading(false);
          return;
        }
      } else if (pixKeyType === 'EMAIL' && !pixKey.includes('@')) {
        setError('Email inválido.');
        setLoading(false);
        return;
      } else if (pixKeyType === 'TELEFONE') {
        const cleanPhone = pixKey.replace(/\D/g, '');
        if (cleanPhone.length < 10 || cleanPhone.length > 11) {
          setError('Telefone inválido. Use o formato: (XX) XXXXX-XXXX ou (XX) XXXX-XXXX');
          setLoading(false);
          return;
        }
      }

      const response = await fetch(`${API_URL}/api/public/payments/withdrawal/pix`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          amount: amountValue,
          pix_key: pixKey.trim(),
          type_key: pixKeyType,
          document_validation: documentValidation || undefined
        })
      });

      const data = await response.json();

      if (response.ok) {
        setWithdrawalData({
          transaction_id: data.transaction_id || '',
          amount: amountValue
        });
        setSuccess(true);
        // Limpar formulário
        setAmount('');
        setPixKey('');
        setDocumentValidation('');
      } else {
        setError(data.detail || 'Erro ao processar saque. Tente novamente.');
      }
    } catch (err) {
      setError('Erro de conexão. Verifique sua internet e tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: string) => {
    // Remove tudo que não é número
    const numbers = value.replace(/\D/g, '');
    // Converte para centavos e depois para reais
    const cents = parseInt(numbers) || 0;
    const reais = (cents / 100).toFixed(2);
    // Formata com vírgula
    return reais.replace('.', ',');
  };

  const handleAmountChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    // Permite apenas números e vírgula
    const formatted = formatCurrency(value);
    setAmount(formatted);
  };

  if (!token || !user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-[#0a0e0f] text-white">
      {/* Header */}
      <div className="bg-[#0a4d3e] border-b border-[#0d5d4b] sticky top-0 z-40">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/conta')}
              className="p-2 hover:bg-[#0d5d4b] rounded transition-colors"
            >
              <ArrowLeft size={20} />
            </button>
            <h1 className="text-xl md:text-2xl font-bold">Sacar</h1>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8 max-w-2xl">
        {!success ? (
          <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
            <div className="flex items-center gap-3 mb-6">
              <div className="bg-[#d4af37]/20 p-3 rounded-lg">
                <Wallet className="text-[#d4af37]" size={24} />
              </div>
              <div>
                <h2 className="text-xl font-bold">Saque via PIX</h2>
                <p className="text-gray-400 text-sm">Saque rápido e seguro</p>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {error && (
                <div className="bg-red-500/20 border border-red-500 text-red-400 px-4 py-3 rounded-lg flex items-start gap-2">
                  <AlertCircle size={20} className="mt-0.5 flex-shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <div>
                <label className="block text-gray-300 text-sm mb-2">
                  Valor do Saque (mínimo R$ 10,00)
                </label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">R$</span>
                  <input
                    type="text"
                    value={amount}
                    onChange={handleAmountChange}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 pl-12 py-3 text-white text-lg focus:outline-none focus:ring-2 focus:ring-[#d4af37] focus:border-transparent"
                    placeholder="0,00"
                    required
                  />
                </div>
                <p className="text-gray-400 text-xs mt-2">
                  Saldo disponível: R$ {user?.balance.toFixed(2).replace('.', ',') || '0,00'}
                </p>
              </div>

              <div>
                <label className="block text-gray-300 text-sm mb-2">
                  Tipo de Chave PIX
                </label>
                <select
                  value={pixKeyType}
                  onChange={(e) => setPixKeyType(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-[#d4af37] focus:border-transparent"
                >
                  <option value="CPF">CPF</option>
                  <option value="CNPJ">CNPJ</option>
                  <option value="EMAIL">E-mail</option>
                  <option value="TELEFONE">Telefone</option>
                  <option value="ALEATORIA">Chave Aleatória</option>
                </select>
              </div>

              <div>
                <label className="block text-gray-300 text-sm mb-2">
                  Chave PIX
                </label>
                <input
                  type="text"
                  value={pixKey}
                  onChange={(e) => setPixKey(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-[#d4af37] focus:border-transparent"
                  placeholder={
                    pixKeyType === 'CPF' ? '000.000.000-00' :
                    pixKeyType === 'CNPJ' ? '00.000.000/0000-00' :
                    pixKeyType === 'EMAIL' ? 'seu@email.com' :
                    pixKeyType === 'TELEFONE' ? '(00) 00000-0000' :
                    'Chave aleatória'
                  }
                  required
                />
              </div>

              {(pixKeyType === 'CPF' || pixKeyType === 'CNPJ') && (
                <div>
                  <label className="block text-gray-300 text-sm mb-2">
                    CPF/CNPJ para Validação (opcional)
                  </label>
                  <input
                    type="text"
                    value={documentValidation}
                    onChange={(e) => setDocumentValidation(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-[#d4af37] focus:border-transparent"
                    placeholder={pixKeyType === 'CPF' ? '000.000.000-00' : '00.000.000/0000-00'}
                  />
                  <p className="text-gray-400 text-xs mt-2">
                    Use este campo se a chave PIX for diferente do seu CPF/CNPJ cadastrado
                  </p>
                </div>
              )}

              <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                <p className="text-blue-300 text-sm">
                  <strong>Importante:</strong> O saque será processado em até 24 horas úteis. O saldo será bloqueado imediatamente e liberado após a confirmação do pagamento.
                </p>
              </div>

              <button
                type="submit"
                disabled={loading || !amount || parseFloat(amount.replace(',', '.')) < 10 || !pixKey}
                className="w-full bg-[#d4af37] hover:bg-[#ffd700] disabled:bg-gray-600 disabled:cursor-not-allowed text-black font-bold py-3 rounded-lg transition-colors"
              >
                {loading ? 'Processando saque...' : 'Confirmar Saque'}
              </button>
            </form>
          </div>
        ) : (
          <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
            <div className="text-center mb-6">
              <div className="flex justify-center mb-4">
                <div className="bg-green-500/20 p-4 rounded-full">
                  <CheckCircle className="text-green-400" size={48} />
                </div>
              </div>
              <h2 className="text-2xl font-bold mb-2">Saque Solicitado com Sucesso!</h2>
              <p className="text-gray-400">Seu saque está sendo processado</p>
            </div>

            <div className="space-y-4">
              <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
                <p className="text-green-300 text-sm">
                  <strong>Valor:</strong> R$ {withdrawalData?.amount.toFixed(2).replace('.', ',')}
                </p>
                <p className="text-green-300 text-sm mt-1">
                  <strong>Status:</strong> Processando
                </p>
                {withdrawalData?.transaction_id && (
                  <p className="text-green-300 text-sm mt-1">
                    <strong>ID da Transação:</strong> {withdrawalData.transaction_id}
                  </p>
                )}
              </div>

              <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                <p className="text-blue-300 text-sm">
                  <strong>Informações:</strong>
                </p>
                <ul className="text-blue-300 text-sm mt-2 space-y-1 list-disc list-inside">
                  <li>O saque será processado em até 24 horas úteis</li>
                  <li>Você receberá uma notificação quando o pagamento for confirmado</li>
                  <li>O saldo foi bloqueado e será liberado após a confirmação</li>
                  <li>Em caso de cancelamento, o saldo será revertido automaticamente</li>
                </ul>
              </div>

              <button
                onClick={() => {
                  setSuccess(false);
                  setWithdrawalData(null);
                  setError('');
                }}
                className="w-full bg-gray-700 hover:bg-gray-600 text-white font-semibold py-3 rounded-lg transition-colors"
              >
                Fazer Novo Saque
              </button>

              <button
                onClick={() => navigate('/conta')}
                className="w-full bg-[#0a4d3e] hover:bg-[#0d5d4b] text-white font-semibold py-3 rounded-lg transition-colors"
              >
                Voltar para Minha Conta
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
