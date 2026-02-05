import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { ArrowLeft, Wallet, Copy, Check } from 'lucide-react';
import QRCode from 'qrcode';

// Backend FastAPI - usa variável de ambiente ou fallback para localhost
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Depositar() {
  const navigate = useNavigate();
  const { user, token } = useAuth();
  const [amount, setAmount] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [pixData, setPixData] = useState<{
    qr_code: string;
    qr_code_base64: string;
    transaction_id: string;
    deposit_id?: number;
  } | null>(null);
  const [copied, setCopied] = useState(false);
  const [settings, setSettings] = useState({ min_amount: 10.0, max_amount: 0.0 });
  const [depositStatus, setDepositStatus] = useState<'pending' | 'checking' | 'approved' | 'error'>('pending');
  const { refreshUser } = useAuth();
  const checkIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const depositStatusRef = useRef<'pending' | 'checking' | 'approved' | 'error'>('pending');

  useEffect(() => {
    if (!token || !user) {
      navigate('/conta');
      return;
    }
    // Carregar configurações de pagamento
    fetch(`${API_URL}/api/public/payments/settings`)
      .then(res => res.json())
      .then(data => setSettings(data))
      .catch(() => {
        // Usar valores padrão em caso de erro
        setSettings({ min_amount: 10.0, max_amount: 0.0 });
      });
  }, [token, user, navigate]);

  // Verificação automática do status do depósito
  useEffect(() => {
    if (!pixData?.deposit_id || !token) {
      // Limpar intervalo se não houver depósito pendente
      if (checkIntervalRef.current) {
        clearInterval(checkIntervalRef.current);
        checkIntervalRef.current = null;
      }
      return;
    }

    let isMounted = true;

    // Função para verificar status
    const checkStatus = async () => {
      // Verificar se já foi aprovado antes de fazer a requisição
      if (depositStatusRef.current === 'approved') {
        // Se já foi aprovado, parar verificação
        if (checkIntervalRef.current) {
          clearInterval(checkIntervalRef.current);
          checkIntervalRef.current = null;
        }
        return;
      }

      try {
        if (isMounted) {
          depositStatusRef.current = 'checking';
          setDepositStatus('checking');
        }
        
        const response = await fetch(`${API_URL}/api/public/payments/deposit/${pixData.deposit_id}/check-status`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        const data = await response.json();

        if (!isMounted) return;

        if (response.ok && data.balance_credited) {
          // Saldo foi creditado!
          depositStatusRef.current = 'approved';
          setDepositStatus('approved');
          if (refreshUser) {
            await refreshUser();
          }
          // Parar verificação
          if (checkIntervalRef.current) {
            clearInterval(checkIntervalRef.current);
            checkIntervalRef.current = null;
          }
        } else if (data.gatebox_status) {
          const statusLower = data.gatebox_status.toLowerCase();
          if (statusLower === 'paid' || statusLower === 'confirmed' || statusLower === 'approved' || statusLower === 'completed') {
            // Pagamento confirmado mas ainda não creditado (pode ser delay)
            depositStatusRef.current = 'checking';
            setDepositStatus('checking');
          } else {
            depositStatusRef.current = 'pending';
            setDepositStatus('pending');
          }
        } else {
          depositStatusRef.current = 'pending';
          setDepositStatus('pending');
        }
      } catch (err) {
        console.error('Erro ao verificar status:', err);
        if (isMounted) {
          depositStatusRef.current = 'error';
          setDepositStatus('error');
        }
      }
    };

    // Verificar imediatamente após um pequeno delay
    const initialTimeout = setTimeout(checkStatus, 2000);

    // Verificar a cada 10 segundos
    checkIntervalRef.current = setInterval(checkStatus, 10000);

    // Limpar intervalo ao desmontar
    return () => {
      isMounted = false;
      if (checkIntervalRef.current) {
        clearInterval(checkIntervalRef.current);
        checkIntervalRef.current = null;
      }
      clearTimeout(initialTimeout);
    };
  }, [pixData?.deposit_id, token, refreshUser]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const amountValue = parseFloat(amount.replace(',', '.'));
      
      if (isNaN(amountValue) || amountValue <= 0) {
        setError('Valor inválido. Digite um valor maior que zero.');
        setLoading(false);
        return;
      }

      if (amountValue < settings.min_amount) {
        setError(`Valor mínimo de depósito é R$ ${settings.min_amount.toFixed(2)}`);
        setLoading(false);
        return;
      }

      if (settings.max_amount > 0 && amountValue > settings.max_amount) {
        setError(`Valor máximo de depósito é R$ ${settings.max_amount.toFixed(2)}`);
        setLoading(false);
        return;
      }

      if (!user) {
        setError('Usuário não encontrado. Faça login novamente.');
        setLoading(false);
        return;
      }

      const response = await fetch(`${API_URL}/api/public/payments/deposit/pix`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          amount: amountValue,
          payer_name: user.username || 'Usuário',
          payer_tax_id: user.cpf || undefined  // Opcional - só enviar CPF válido, não usar telefone
        })
      });

      const data = await response.json();

      if (response.ok) {
        // Log para debug
        console.log('Deposit Response:', data);
        
        // Extrair dados do PIX da resposta
        const metadata = typeof data.metadata_json === 'string' 
          ? JSON.parse(data.metadata_json) 
          : data.metadata_json || {};
        
        console.log('Parsed Metadata:', metadata);
        
        const gateboxResponse = metadata.gatebox_response || {};
        const gateboxRawResponse = metadata.gatebox_raw_response || {};
        console.log('Gatebox Response:', gateboxResponse);
        console.log('Gatebox Raw Response:', gateboxRawResponse);
        
        // Verificar se há dados em um campo "data" ou "result"
        let actualGateboxData = gateboxResponse;
        if (gateboxRawResponse.data && typeof gateboxRawResponse.data === 'object') {
          actualGateboxData = gateboxRawResponse.data;
        } else if (gateboxRawResponse.result && typeof gateboxRawResponse.result === 'object') {
          actualGateboxData = gateboxRawResponse.result;
        }
        
        // Tentar extrair código PIX de várias fontes possíveis
        // A Gatebox retorna o código PIX no campo "key"
        const pixCode = (
          metadata.pix_code || 
          metadata.pix_qr_code ||
          gateboxResponse.key ||  // Campo principal da Gatebox
          gateboxResponse.qrCode || 
          gateboxResponse.pixCode || 
          gateboxResponse.emv ||
          gateboxResponse.qr_code ||
          gateboxResponse.pix_code ||
          gateboxResponse.code ||
          gateboxResponse.qrCodeString ||
          actualGateboxData.key ||  // Campo principal da Gatebox
          actualGateboxData.qrCode ||
          actualGateboxData.pixCode ||
          actualGateboxData.emv ||
          ''
        );
        
        // Tentar extrair QR Code Base64 de várias fontes possíveis
        const pixQrCodeBase64 = (
          metadata.pix_qr_code_base64 ||
          gateboxResponse.qrCodeBase64 || 
          gateboxResponse.base64 ||
          gateboxResponse.qr_code_base64 ||
          gateboxResponse.qrCodeBase64Image ||
          gateboxResponse.qrCodeImage ||
          gateboxResponse.qrCodeImageBase64 ||
          actualGateboxData.qrCodeBase64 ||
          actualGateboxData.base64 ||
          actualGateboxData.qrCodeBase64Image ||
          ''
        );
        
        console.log('Extracted PIX Code:', pixCode ? pixCode.substring(0, 50) + '...' : 'EMPTY');
        console.log('Extracted QR Code Base64:', pixQrCodeBase64 ? 'Yes' : 'No');
        
        if (!pixCode) {
          console.error('No PIX data found in response:', { metadata, gateboxResponse });
          setError('Erro: Dados do PIX não encontrados na resposta. Verifique os logs do console.');
          return;
        }
        
        // Se não houver QR Code Base64, gerar a partir do código PIX
        let finalQrCodeBase64 = pixQrCodeBase64;
        if (!finalQrCodeBase64 && pixCode) {
          try {
            // Gerar QR Code em base64 a partir do código PIX
            // QRCode.toDataURL() já retorna a string completa com prefixo data:image/png;base64,
            finalQrCodeBase64 = await QRCode.toDataURL(pixCode, {
              width: 300,
              margin: 2,
              color: {
                dark: '#000000',
                light: '#FFFFFF'
              }
            });
            console.log('QR Code generated from PIX code');
            console.log('QR Code starts with data:', finalQrCodeBase64.startsWith('data:'));
            console.log('QR Code length:', finalQrCodeBase64.length);
            console.log('QR Code first 100 chars:', finalQrCodeBase64.substring(0, 100));
          } catch (err) {
            console.error('Error generating QR Code:', err);
            // Continuar mesmo sem QR Code - o código PIX ainda pode ser copiado
            finalQrCodeBase64 = '';
          }
        }
        
        // Garantir que não há prefixo duplicado
        if (finalQrCodeBase64) {
          // Normalizar: remover todos os prefixos e adicionar apenas um
          const base64Data = finalQrCodeBase64.replace(/^data:image\/png;base64,+/g, '');
          // Garantir que tem apenas um prefixo correto
          finalQrCodeBase64 = 'data:image/png;base64,' + base64Data;
          console.log('Normalized QR Code Base64');
        }
        
        console.log('Final QR Code Base64 (first 100 chars):', finalQrCodeBase64 ? finalQrCodeBase64.substring(0, 100) : 'EMPTY');
        console.log('Final QR Code starts with data:', finalQrCodeBase64 ? finalQrCodeBase64.startsWith('data:') : false);
        console.log('Final QR Code has duplicate prefix:', finalQrCodeBase64 ? finalQrCodeBase64.includes('data:image/png;base64,data:image/png;base64,') : false);
        
        setPixData({
          qr_code: pixCode,
          qr_code_base64: finalQrCodeBase64,
          transaction_id: data.transaction_id || '',
          deposit_id: data.id
        });
        depositStatusRef.current = 'pending';
        setDepositStatus('pending');
      } else {
        setError(data.detail || 'Erro ao gerar código PIX. Tente novamente.');
      }
    } catch (err) {
      setError('Erro de conexão. Verifique sua internet e tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  const copyPixCode = () => {
    if (pixData?.qr_code) {
      navigator.clipboard.writeText(pixData.qr_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
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
            <h1 className="text-xl md:text-2xl font-bold">Depositar</h1>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8 max-w-2xl">
        {!pixData ? (
          <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
            <div className="flex items-center gap-3 mb-6">
              <div className="bg-[#d4af37]/20 p-3 rounded-lg">
                <Wallet className="text-[#d4af37]" size={24} />
              </div>
              <div>
                <h2 className="text-xl font-bold">Depósito via PIX</h2>
                <p className="text-gray-400 text-sm">Depósito rápido e seguro</p>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {error && (
                <div className="bg-red-500/20 border border-red-500 text-red-400 px-4 py-3 rounded-lg">
                  {error}
                </div>
              )}

              <div>
                <label className="block text-gray-300 text-sm mb-2">
                  Valor do Depósito {settings.max_amount > 0 
                    ? `(mínimo R$ ${settings.min_amount.toFixed(2)} e máximo R$ ${settings.max_amount.toFixed(2)})`
                    : `(mínimo R$ ${settings.min_amount.toFixed(2)})`}
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
                  Saldo atual: R$ {user?.balance.toFixed(2).replace('.', ',') || '0,00'}
                </p>
              </div>

              <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                <p className="text-blue-300 text-sm">
                  <strong>Importante:</strong> O depósito será processado automaticamente após o pagamento do PIX ser confirmado.
                </p>
              </div>

              <button
                type="submit"
                disabled={loading || !amount || parseFloat(amount.replace(',', '.')) < settings.min_amount}
                className="w-full bg-[#ff6b35] hover:bg-[#ff7b35] disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-bold py-3 rounded-lg transition-colors"
              >
                {loading ? 'Gerando código PIX...' : 'Gerar Código PIX'}
              </button>
            </form>
          </div>
        ) : (
          <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold mb-2">PIX Gerado com Sucesso!</h2>
              <p className="text-gray-400">Escaneie o QR Code ou copie o código PIX</p>
            </div>

            {pixData.qr_code_base64 && (
              <div className="bg-white p-4 rounded-lg mb-6 flex justify-center">
                <img 
                  src={pixData.qr_code_base64}
                  alt="QR Code PIX" 
                  className="max-w-xs w-full"
                  onError={(e) => {
                    console.error('Error loading QR Code image');
                    console.error('Error event:', e);
                    console.log('QR Code Base64 value (first 150 chars):', pixData.qr_code_base64.substring(0, 150));
                    console.log('QR Code starts with data:', pixData.qr_code_base64.startsWith('data:'));
                    console.log('QR Code length:', pixData.qr_code_base64.length);
                  }}
                />
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-gray-300 text-sm mb-2">Código PIX (Copiar e Colar)</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={pixData.qr_code}
                    readOnly
                    className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white text-sm font-mono break-all"
                  />
                  <button
                    onClick={copyPixCode}
                    className="bg-[#d4af37] hover:bg-[#ffd700] text-black px-4 py-3 rounded-lg transition-colors flex items-center gap-2"
                  >
                    {copied ? <Check size={20} /> : <Copy size={20} />}
                    {copied ? 'Copiado!' : 'Copiar'}
                  </button>
                </div>
              </div>

              <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
                <p className="text-green-300 text-sm">
                  <strong>Valor:</strong> R$ {amount}
                </p>
                <p className="text-green-300 text-sm mt-1">
                  <strong>Status:</strong>{' '}
                  {depositStatus === 'approved' && '✅ Pagamento confirmado e saldo creditado!'}
                  {depositStatus === 'checking' && '⏳ Verificando pagamento...'}
                  {depositStatus === 'pending' && 'Aguardando pagamento'}
                  {depositStatus === 'error' && 'Erro ao verificar status'}
                </p>
                {depositStatus === 'checking' && (
                  <p className="text-yellow-300 text-xs mt-2">
                    Verificando automaticamente a cada 10 segundos...
                  </p>
                )}
                {depositStatus === 'approved' && user && (
                  <p className="text-green-300 text-sm mt-2">
                    <strong>Novo saldo:</strong> R$ {user.balance.toFixed(2).replace('.', ',')}
                  </p>
                )}
              </div>

              <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                <p className="text-blue-300 text-sm">
                  <strong>Instruções:</strong>
                </p>
                <ol className="text-blue-300 text-sm mt-2 space-y-1 list-decimal list-inside">
                  <li>Copie o código PIX ou escaneie o QR Code</li>
                  <li>Abra o app do seu banco</li>
                  <li>Cole o código ou escaneie o QR Code</li>
                  <li>Confirme o pagamento</li>
                  <li>O saldo será creditado automaticamente após confirmação</li>
                </ol>
              </div>

              <button
                onClick={() => {
                  // Limpar intervalo antes de resetar
                  if (checkIntervalRef.current) {
                    clearInterval(checkIntervalRef.current);
                    checkIntervalRef.current = null;
                  }
                  setPixData(null);
                  setAmount('');
                  setError('');
                  depositStatusRef.current = 'pending';
                  setDepositStatus('pending');
                }}
                className="w-full bg-gray-700 hover:bg-gray-600 text-white font-semibold py-3 rounded-lg transition-colors"
              >
                Gerar Novo Depósito
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
