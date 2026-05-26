# Integração Keiko Exchange - Documentação

## Análise da API (conformidade)

A documentação Keiko Exchange foi comparada com a arquitetura existente (Gatebox). Pontos validados:

| Requisito Keiko | Implementação Fortune Vegas |
|-----------------|----------------------------|
| Auth `POST /auth/integrations/token` (client_id + client_secret) | `KeikoAPI._authenticate()` com cache de token (3600s) |
| PIX Cash-In `POST /pix/in/charges` | Depósito via `create_pix_charge()` |
| PIX Cash-Out `POST /pix/out/transfers` | Saque com mapeamento de `pix_key_type` |
| Consulta `GET /transactions` | `check_deposit_status` via polling |
| Webhooks normalizados (`pix_in.*`, `pix_out.*`) | `POST /api/webhooks/keiko` |
| Webhook URL no painel Keiko (não por request) | Aba Webhooks no Admin |
| Idempotency key | `external_id` enviado como `idempotency_key` |
| Telefone PIX `+55...` | `format_phone_for_keiko()` |

**Escopo desta integração:** PIX BRL (cash-in, cash-out, webhooks). Custódia Tron/USDT (`/custody/tron/*`) não foi incluída — pode ser adicionada em fase posterior se necessário.

## Arquivos criados/alterados

- `backend/keiko_api.py` — Cliente HTTP da API Keiko
- `backend/gateway_service.py` — Detecção de provedor e helpers
- `backend/routes/payments.py` — Depósito, saque, status e webhook Keiko
- `backend/routes/admin.py` — URLs de webhook Gatebox + Keiko
- `frontend/src/pages/Admin.tsx` — Seletor de provedor no painel Gateways
- `frontend/src/pages/Depositar.tsx` — Leitura de QR Keiko (`br_code`)

## Configuração no Painel Admin

1. Acesse **Admin → Gateways**
2. Clique em **Adicionar Novo Gateway**
3. Preencha:
   - **Nome:** `Keiko PIX` (ou similar)
   - **Tipo:** PIX
   - **Provedor:** Keiko Exchange
   - **Client ID:** UUID emitido pela Keiko
   - **Client Secret:** `cs_live_...`
   - **API URL:** `https://api.keikobank.com`
   - **Ativo:** marcado
4. Desative outros gateways PIX para que apenas um fique ativo

**Exemplo de credentials (JSON interno):**
```json
{
  "provider": "keiko",
  "client_id": "be9cd100-e83f-4d3f-bc5b-695ec1aa2e04",
  "client_secret": "cs_live_xxxxxxxxxxxxxxxxxxxxxxxxx",
  "api_url": "https://api.keikobank.com"
}
```

## Webhook Keiko

1. Acesse **Admin → Webhooks**
2. Copie a URL **Keiko Exchange**
3. No painel Keiko Exchange (configurações da conta cliente), registre essa URL
4. Eventos suportados: `pix_in.succeeded`, `pix_in.refunded`, `pix_out.succeeded`, `pix_out.failed`, etc.

URL padrão: `https://api.fortunevegas.site/api/webhooks/keiko`  
(ajuste `WEBHOOK_BASE_URL` no ambiente se necessário)

## Endpoints utilizados

| Operação | Método Keiko | Rota interna |
|----------|--------------|--------------|
| Token | `POST /auth/integrations/token` | Automático no cliente |
| Depósito | `POST /pix/in/charges` | `POST /api/public/payments/deposit/pix` |
| Saque | `POST /pix/out/transfers` | `POST /api/public/payments/withdrawal/pix` |
| Status | `GET /transactions` | `POST /api/public/payments/deposit/{id}/check-status` |
| Webhook | — | `POST /api/webhooks/keiko` |

## Referências

- API Base: https://api.keikobank.com
- Painel: https://www.keikobank.com
- Repositório: https://github.com/ronaldoarch/fortunevegas
