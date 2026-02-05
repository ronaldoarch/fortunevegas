# 📦 Guia de Deploy no Coolify - Fortune Vegas Backend

Este guia explica como configurar o deploy do backend Fortune Vegas no Coolify.

## 📋 Pré-requisitos

1. **PostgreSQL**: Banco de dados PostgreSQL configurado no Coolify
2. **Volume Persistente**: Para armazenar uploads de imagens (banners e logos)

---

## 🚀 Configuração no Coolify

### 1. Criar Novo Projeto/Application

1. Acesse seu Coolify
2. Vá em **Projects** → **Create a new Application**
3. Selecione **Deploy any public Git repositories**
4. Preencha:
   - **Repository URL**: `https://github.com/ronaldoarch/fortunevegas`
   - **Branch**: `cloudflare-deploy` (ou a branch que você usar)
   - **Base Directory**: `/backend`
   - **Port**: `8000`
   - **Build Pack**: `Nixpacks` (ou use Dockerfile customizado)

---

## ⚙️ Variáveis de Ambiente

Configure estas variáveis no Coolify (Environment Variables):

### Banco de Dados

```env
DATABASE_URL=postgresql://usuario:senha@host:5432/fortunevegas
```

**Formato completo:**
```
postgresql://[user]:[password]@[host]:[port]/[database]
```

**Exemplo:**
```
DATABASE_URL=postgresql://postgres:senha123@postgres-db.coolify.internal:5432/fortunevegas
```

### Segurança (JWT)

```env
SECRET_KEY=sua-chave-secreta-super-segura-aqui-mude-em-producao
```

**Gerar uma chave segura:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### CORS (Opcional - se usar frontend separado)

Se o frontend estiver em outro domínio, ajuste no `main.py` ou adicione:

```env
CORS_ORIGINS=http://localhost:5173,https://seu-dominio.com
```

---

## 📁 Volume Persistente

**IMPORTANTE**: Configure um volume persistente para os uploads.

### No Coolify:

1. Na página da aplicação, vá em **Persistent Storage** (ou **Volumes**)
2. Clique em **Add Volume Mount**
3. Configure:
   - **Name**: `fortunevegas-uploads`
   - **Source Path**: `/root/fortunevegas-uploads` (ou outro caminho no servidor)
   - **Destination Path**: `/app/uploads` ⚠️ **OBRIGATÓRIO**

Isso garante que os banners e logos enviados não sejam perdidos em atualizações/restarts.

📖 **Guia Detalhado**: Veja [VOLUME-PERSISTENTE.md](./VOLUME-PERSISTENTE.md) para instruções passo a passo com screenshots.

---

## 🔧 Build Settings

### Build Command (se usar Nixpacks)
```
pip install -r requirements.txt
```

### Start Command (se não usar Dockerfile)
```
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1
```

### Health Check
```
GET /api/health
```

---

## 🗄️ Banco de Dados PostgreSQL

### Criar Banco de Dados

No Coolify, crie um serviço PostgreSQL:

1. **Projects** → **PostgreSQL** → **Create**
2. Configure:
   - **Database Name**: `fortunevegas`
   - **User**: `postgres` (ou outro)
   - **Password**: (defina uma senha forte)

3. **Copie a connection string** e use em `DATABASE_URL`

### Migrações Automáticas

O backend cria as tabelas automaticamente no primeiro startup (via `init_db()` no `main.py`).

Se preferir usar Alembic:
```bash
cd backend
alembic upgrade head
```

---

## ✅ Verificação Pós-Deploy

### 1. Verificar Saúde da API

```bash
curl https://seu-dominio.com/api/health
```

Deve retornar:
```json
{"status": "healthy"}
```

### 2. Verificar Banco de Dados

Acesse o PostgreSQL e verifique se as tabelas foram criadas:

```sql
\dt
```

Deve listar:
- `users`
- `media_assets`
- `deposits`
- `withdrawals`
- `ftds`
- `gateways`
- etc.

### 3. Testar Upload de Logo/Banner

Faça login no admin e teste o upload de imagens no painel de Branding.

---

## 🔒 Segurança

### Recomendações:

1. **SECRET_KEY**: Use uma chave forte e única em produção
2. **DATABASE_URL**: Não exponha em logs ou repositórios
3. **CORS**: Restrinja origens apenas aos domínios do frontend
4. **HTTPS**: Configure certificado SSL no Coolify

---

## 🐛 Troubleshooting

### Erro: "Could not connect to database"

- Verifique se `DATABASE_URL` está correto
- Confirme se o PostgreSQL está rodando
- Teste a conexão do container com o PostgreSQL

### Erro: "Permission denied" nos uploads

- Verifique permissões do volume: `chmod -R 755 uploads`
- Confirme que o volume está montado corretamente

### Imagens não aparecem

- Verifique se o volume está montado em `/app/uploads`
- Confirme que os arquivos foram salvos fisicamente
- Verifique a URL base da API (precisa ser acessível)

---

## 📚 Referências

- [Coolify Documentation](https://coolify.io/docs)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [PostgreSQL Docker](https://hub.docker.com/_/postgres)

---

## 🔄 Atualizações

Para atualizar a aplicação:

1. Faça commit/push no repositório
2. No Coolify, vá em **Redeploy** (ou configure auto-deploy)
3. Aguarde o build e restart

Os dados no PostgreSQL e os arquivos no volume persistente serão preservados.
