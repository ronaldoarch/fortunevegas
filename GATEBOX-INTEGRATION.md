# Integração Gatebox - Documentação

## ✅ O que foi implementado

### 1. Módulo de API (`backend/gatebox_api.py`)
- Classe `GateboxAPI` para comunicação com a API Gatebox
- Autenticação automática via Bearer token
- Métodos:
  - `create_immediate_qrcode()` - Gera código PIX para depósito (Cash-in)
  - `withdraw_pix()` - Realiza transferência PIX para saque (Cash-out)
  - `get_pix_status()` - Consulta status de transação PIX
  - `validate_pix_key()` - Valida chave PIX
  - `get_balance()` - Consulta saldo da conta

### 2. Rotas Públicas (`backend/routes/payments.py`)
- **POST `/api/public/payments/deposit/pix`** - Criar depósito via PIX
  - Requer autenticação (Bearer token)
  - Parâmetros: `amount`, `payer_name`, `payer_tax_id`
  - Retorna código PIX e QR Code
  
- **POST `/api/public/payments/withdrawal/pix`** - Criar saque via PIX
  - Requer autenticação (Bearer token)
  - Parâmetros: `amount`, `pix_key`, `type_key`, `document_validation` (opcional)
  - Bloqueia saldo do usuário imediatamente

### 3. Webhooks (`backend/routes/payments.py`)
- **POST `/api/webhooks/gatebox/pix-cashin`** - Recebe notificações de depósitos
  - Atualiza status do depósito
  - Adiciona saldo ao usuário quando status for "PAID", "PAID_OUT", "CONFIRMED", "APPROVED" ou "SUCCESS"
  - Reverte saldo em caso de cancelamento
  
- **POST `/api/webhooks/gatebox/pix-cashout`** - Recebe notificações de saques
  - Atualiza status do saque
  - Reverte saldo se status for "CANCELLED", "CANCELED", "REJECTED" ou "FAILED"

## ⚙️ Configuração necessária

### 1. Criar Gateway no Painel Admin

**Passo a passo:**

1. Acesse o painel Admin do sistema
2. No menu lateral, clique em **"Gateways"** (ícone de cartão de crédito)
3. Preencha o formulário:
   - **Nome do Gateway**: "Gatebox PIX" (ou outro nome de sua preferência)
   - **Tipo**: Selecione "PIX"
   - **Username**: Seu username da Gatebox
   - **Password**: Sua password da Gatebox
   - **API URL**: `https://api.gatebox.com.br` (ou deixe em branco para usar o padrão)
   - **Ativo**: Marque a checkbox para ativar o gateway
4. Clique em **"Criar Gateway"**

**Exemplo de configuração:**
- **name**: "Gatebox PIX" (ou outro nome)
- **type**: "pix"
- **is_active**: `true`
- **credentials**: JSON com as credenciais:
  ```json
  {
    "username": "seu_username_aqui",
    "password": "sua_password_aqui",
    "api_url": "https://api.gatebox.com.br"
  }
  ```

**Credenciais de Teste (Homologação)**:
```json
{
  "username": "93892492000158",
  "password": "@Homolog1",
  "api_url": "https://api.gatebox.com.br"
}
```

**Nota**: O campo `api_url` é opcional e padrão é `https://api.gatebox.com.br`. Para ambiente de teste/sandbox, verifique a URL correta na documentação da Gatebox.

### 2. Variáveis de Ambiente

Adicionar no ambiente de produção:
- `WEBHOOK_BASE_URL`: URL base do seu backend (ex: `https://api.agenciamidas.com`)

### 3. Configurar Webhooks na Gatebox

No painel da Gatebox, configurar os webhooks:
- **PIX Cash-in**: `https://api.agenciamidas.com/api/webhooks/gatebox/pix-cashin`
- **PIX Cash-out**: `https://api.agenciamidas.com/api/webhooks/gatebox/pix-cashout`

**Nota**: A validação de webhook pode variar conforme a implementação da Gatebox. Verifique a documentação oficial para métodos de validação (se houver assinatura, token, etc.).

## 📋 Endpoints da API Gatebox

### Autenticação
- **Endpoint**: `POST /v1/customers/auth/sign-in`
- **Campos**:
  - `username`: Username da conta Gatebox
  - `password`: Password da conta Gatebox
- **Resposta**: `{ "access_token": "..." }`

### PIX Cash-in (Depósito)
- **Endpoint**: `POST /v1/customers/pix/create-immediate-qrcode`
- **Campos obrigatórios**:
  - `externalId`: ID de conciliação único
  - `amount`: Valor do depósito
  - `document`: CPF/CNPJ do pagador (sem pontuação)
  - `name`: Nome completo do pagador
  - `expire`: Tempo de expiração em segundos (padrão: 3600)
- **Campos opcionais**:
  - `email`: Email do pagador
  - `phone`: Telefone do pagador (formato: +5514987654321)
  - `identification`: Descrição a ser exibida no momento do pagamento
  - `description`: Descrição da transação

### PIX Cash-out (Saque)
- **Endpoint**: `POST /v1/customers/pix/withdraw`
- **Campos obrigatórios**:
  - `externalId`: ID de conciliação único
  - `key`: Chave PIX do recebedor
  - `name`: Nome completo do recebedor
  - `amount`: Valor do saque
- **Campos opcionais**:
  - `documentNumber`: CPF/CNPJ do recebedor (obrigatório apenas se validação de chave pix estiver ativa)
  - `description`: Descrição da transação

### Consulta Status
- **Endpoint**: `GET /v1/customers/pix/status`
- **Parâmetros** (pelo menos um obrigatório):
  - `transactionId`: ID da transação
  - `externalId`: ID externo de conciliação
  - `endToEnd`: EndToEnd da transação

### Validar Chave PIX
- **Endpoint**: `GET /v1/customers/pix/pix-search`
- **Parâmetros**:
  - `dict`: Chave PIX a ser verificada (sem pontuação)

### Consultar Saldo
- **Endpoint**: `POST /v1/customers/account/balance`

## 🔒 Segurança

- Autenticação via Bearer token (JWT) nos endpoints públicos
- Autenticação automática na API Gatebox via username/password
- Credenciais armazenadas no banco de dados (não em código)
- Suporte para diferentes URLs de API (sandbox/produção)

## 📝 Notas

- Os endpoints da Gatebox podem variar. Verifique a documentação oficial se houver erros.
- Os campos de resposta podem precisar de ajustes conforme a resposta real da API.
- A estrutura dos webhooks pode variar - os campos foram mapeados de forma genérica para suportar diferentes formatos.
- Teste primeiro em ambiente de teste antes de usar em produção.
- A validação de webhook pode não estar implementada pela Gatebox - verifique a documentação oficial.

## 🔄 Migração da SuitPay

Se você estava usando SuitPay anteriormente:

1. **Atualizar credenciais**: Trocar `client_id`/`client_secret` por `username`/`password`
2. **Atualizar webhooks**: Configurar novos endpoints `/api/webhooks/gatebox/pix-cashin` e `/api/webhooks/gatebox/pix-cashout`
3. **Remover campo sandbox**: A Gatebox usa URL diferente ao invés de flag sandbox
4. **Verificar campos de resposta**: Os campos retornados pela Gatebox podem ser diferentes da SuitPay

## 📚 Referências

- Documentação da API Gatebox: Consulte a documentação oficial da Gatebox
- Postman Collection: `GATEBOX API.postman_collection.json` no projeto
