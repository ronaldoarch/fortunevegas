# 🌐 Guia Completo: Conectar Domínio Personalizado ao Site

## 📋 Visão Geral

Para conectar seu domínio ao site, você precisa:
1. Adicionar o domínio no Coolify
2. Configurar registros DNS no provedor do domínio
3. Atualizar variáveis de ambiente (CORS, VITE_API_URL)
4. Aguardar propagação DNS

---

## 1️⃣ Adicionar Domínio no Coolify

### Para o Backend (API):

1. No Coolify, abra sua aplicação **Backend**
2. Vá na aba **Domains** ou **Settings** → **Domains**
3. Clique em **Add Domain** ou **Custom Domain**
4. Adicione seu domínio/subdomínio, por exemplo:
   - `api.seudominio.com` (para API)
   - `backend.seudominio.com`
   - Ou o domínio principal se for único: `seudominio.com`

### Para o Frontend:

1. Abra sua aplicação **Frontend**
2. Vá em **Domains** → **Add Domain**
3. Adicione:
   - `seudominio.com` (domínio principal)
   - `www.seudominio.com` (opcional)

### Configuração SSL/TLS:

O Coolify geralmente configura SSL automaticamente via Let's Encrypt quando detecta o DNS correto.

---

## 2️⃣ Configurar DNS no Provedor do Domínio

### Opção A: Usando Registros A (Recomendado)

No painel do seu provedor de domínio (Registro.br, GoDaddy, Namecheap, etc.), adicione:

#### Para Backend (API):
```
Tipo: A
Nome: api (ou @ se for domínio principal)
Valor: [IP do servidor Coolify]
TTL: 3600 (ou padrão)
```

#### Para Frontend:
```
Tipo: A
Nome: @ (ou www)
Valor: [IP do servidor Coolify]
TTL: 3600 (ou padrão)
```

**Como descobrir o IP do servidor Coolify:**
- No Coolify, vá em **Settings** → **Servers**
- O IP será mostrado no servidor ativo
- Ou consulte a documentação do seu provedor Coolify

### Opção B: Usando CNAME (Subdomínios)

Se estiver usando subdomínios, pode usar CNAME:

#### Para Backend:
```
Tipo: CNAME
Nome: api
Valor: [subdomínio.coolify.app do backend]
TTL: 3600
```

#### Para Frontend:
```
Tipo: CNAME
Nome: www
Valor: [subdomínio.coolify.app do frontend]
TTL: 3600
```

**Exemplo:**
- Se o backend está em `backend-abc123.coolify.app`, use esse valor no CNAME de `api.seudominio.com`

---

## 3️⃣ Atualizar Variáveis de Ambiente

### Backend - Variável CORS_ORIGINS:

No Coolify, na aplicação **Backend**, vá em **Environment Variables** e atualize:

```env
CORS_ORIGINS=https://seudominio.com,https://www.seudominio.com,https://api.seudominio.com
```

Ou se o backend e frontend estão no mesmo domínio:
```env
CORS_ORIGINS=https://seudominio.com,https://www.seudominio.com
```

**Importante:** Se estiver usando subdomínios do `agenciamidas.com`, o código já está configurado para aceitar qualquer subdomínio via regex.

### Frontend - Variável VITE_API_URL:

Na aplicação **Frontend**, atualize:

```env
VITE_API_URL=https://api.seudominio.com
```

Ou se backend e frontend estão no mesmo domínio:
```env
VITE_API_URL=https://seudominio.com
```

**⚠️ ATENÇÃO:** Após alterar variáveis de ambiente, é necessário fazer **Redeploy** da aplicação!

---

## 4️⃣ Verificar Propagação DNS

### Verificar DNS no Terminal:

```bash
# Verificar registro A
dig seu-dominio.com
# ou
nslookup seu-dominio.com

# Verificar CNAME
dig api.seudominio.com CNAME
```

### Verificar Online:

- [https://dnschecker.org](https://dnschecker.org) - Verifica propagação global
- [https://www.whatsmydns.net](https://www.whatsmydns.net) - Verifica DNS

**Tempo de propagação:** Geralmente de 5 minutos a 48 horas (normalmente 1-2 horas)

---

## 5️⃣ Verificar SSL/HTTPS

Após a propagação DNS:

1. O Coolify detectará automaticamente o domínio
2. Solicitará certificado SSL via Let's Encrypt
3. Em alguns minutos, o HTTPS estará ativo

### Verificar SSL:

```bash
curl -I https://seu-dominio.com
# Deve retornar 200 OK com certificado válido
```

Ou acesse diretamente no navegador - deve aparecer o cadeado verde.

---

## 6️⃣ Testar Aplicação

### Testar Backend:

```bash
# Health check
curl https://api.seudominio.com/api/health

# Deve retornar:
# {"status": "healthy"}
```

### Testar Frontend:

1. Acesse `https://seudominio.com` no navegador
2. Verifique no console do navegador (F12) se não há erros de CORS
3. Teste fazer login/registro para verificar conexão com API

---

## ⚠️ IMPORTANTE: Desativar Hosting na Hostinger

Se você está usando Coolify, **NÃO precisa** do serviço de hosting da Hostinger. Ter ambos ativos pode causar conflitos.

### Como Desativar Hosting na Hostinger:

1. **Acesse o painel da Hostinger:**
   - Faça login em [hpanel.hostinger.com](https://hpanel.hostinger.com)
   - Vá em **Sites** → `fortunevegas.site`

2. **Desative o serviço de hosting:**
   - Procure pelo card **"Hospedagem" ou "Hosting"**
   - Clique nele
   - Procure opções como:
     - **"Desativar"**
     - **"Remover site"**
     - **"Cancelar hosting"**
     - Ou entre em contato com suporte para desativar

3. **Alternativa - Desconectar domínio:**
   - Se não conseguir desativar, clique em **"Conectar domínio"**
   - E depois desconecte/remova o domínio do site

4. **Limpar cache da Hostinger:**
   - No painel da Hostinger, clique em **"Limpar cache"**
   - Isso remove qualquer cache que possa estar interferindo

5. **Aguardar propagação:**
   - Após desativar, aguarde 10-15 minutos
   - O DNS deve apontar diretamente para o Coolify

**Por que isso é importante?**
- O hosting da Hostinger pode interceptar requisições antes de chegar ao Coolify
- Isso impede que o certificado SSL do Coolify funcione corretamente
- Pode causar conflitos de DNS e redirecionamentos

---

## 🔧 Troubleshooting

### ❌ Erro: "DNS não resolve"

**Soluções:**
1. Aguarde mais tempo (pode levar até 48h)
2. Verifique se os registros DNS estão corretos
3. Limpe cache DNS do seu computador:
   ```bash
   # Windows
   ipconfig /flushdns
   
   # Mac/Linux
   sudo dscacheutil -flushcache
   ```

### ❌ Erro: CORS bloqueado

**Soluções:**
1. Verifique se `CORS_ORIGINS` inclui o domínio correto (com https://)
2. Faça redeploy do backend após alterar variável
3. Verifique se o frontend está usando o domínio correto na variável `VITE_API_URL`

### ❌ Certificado SSL não gera ou mostra "Não seguro"

**Sintomas:**
- Site carrega mas mostra "Não seguro" no navegador
- Aviso de "Sua conexão com esse site não é segura"
- Certificado não é reconhecido pelo navegador

**Soluções:**

1. **Verificar se o domínio está adicionado no Coolify:**
   - No Coolify, abra sua aplicação **Frontend**
   - Vá em **Domains** ou **Settings** → **Domains**
   - Certifique-se de que `fortunevegas.site` está listado
   - Se não estiver, adicione o domínio

2. **Forçar geração do certificado SSL:**
   - No Coolify, na aplicação **Frontend**
   - Vá em **Domains** → clique no domínio `fortunevegas.site`
   - Procure por opções como:
     - **"Generate SSL Certificate"**
     - **"Request Certificate"**
     - **"Enable SSL"**
     - Ou um botão de refresh/regenerar certificado
   - Clique para forçar a geração

3. **Verificar propagação DNS completa:**
   ```bash
   # Verificar se DNS está propagado globalmente
   dig fortunevegas.site
   # Deve retornar o IP do Coolify (147.93.147.33)
   ```
   - Use [https://dnschecker.org](https://dnschecker.org) para verificar propagação global
   - O certificado SSL só será gerado quando o DNS estiver 100% propagado

4. **Aguardar geração automática:**
   - O Coolify usa Let's Encrypt que pode levar 5-15 minutos após DNS propagado
   - Aguarde e verifique novamente

5. **Verificar logs do Coolify:**
   - No Coolify, vá em **Logs** da aplicação Frontend
   - Procure por erros relacionados a SSL/Let's Encrypt
   - Erros comuns: "DNS challenge failed", "Domain not reachable"

6. **Verificar se há serviço de hosting ativo na Hostinger:**
   - Se houver hosting ativo na Hostinger, ele pode interferir
   - Desative o serviço de hosting na Hostinger (veja seção abaixo)

7. **Limpar cache do navegador:**
   - Limpe cache e cookies do navegador
   - Tente em modo anônimo/privado
   - Ou use outro navegador para testar

### ❌ Frontend não conecta com Backend

**Soluções:**
1. Verifique se `VITE_API_URL` está correta
2. Faça redeploy do frontend após alterar variável
3. Verifique no console do navegador (F12 → Network) qual URL está sendo usada
4. Teste acessar a URL do backend diretamente: `https://api.seudominio.com/api/health`

---

## 📊 Exemplo Completo de Configuração

### Cenário: Domínio `exemplo.com`

#### 1. Registros DNS:

```
Tipo: A
Nome: @
Valor: 123.456.789.012  (IP do Coolify)
TTL: 3600

Tipo: A
Nome: api
Valor: 123.456.789.012  (mesmo IP)
TTL: 3600

Tipo: A (ou CNAME)
Nome: www
Valor: 123.456.789.012  (ou exemplo.coolify.app)
TTL: 3600
```

#### 2. Variáveis de Ambiente - Backend:

```env
DATABASE_URL=postgresql://...
SECRET_KEY=...
CORS_ORIGINS=https://exemplo.com,https://www.exemplo.com
```

#### 3. Variáveis de Ambiente - Frontend:

```env
VITE_API_URL=https://api.exemplo.com
```

#### 4. Resultado:

- Frontend: `https://exemplo.com`
- Backend: `https://api.exemplo.com`
- Admin: `https://exemplo.com/admin/login`

---

## 🎯 Checklist Final

- [ ] Domínio adicionado no Coolify (Backend)
- [ ] Domínio adicionado no Coolify (Frontend)
- [ ] Registros DNS configurados no provedor
- [ ] Aguardou propagação DNS (verificou com dig/nslookup)
- [ ] SSL/HTTPS funcionando (cadeado verde no navegador)
- [ ] Variável `CORS_ORIGINS` atualizada no Backend
- [ ] Variável `VITE_API_URL` atualizada no Frontend
- [ ] Redeploy feito após alterar variáveis
- [ ] Backend responde em `https://api.seudominio.com/api/health`
- [ ] Frontend carrega em `https://seudominio.com`
- [ ] Login/registro funcionando (testado no navegador)

---

## 📝 Notas Importantes

1. **Propagação DNS:** Pode levar de 5 minutos a 48 horas (normalmente 1-2h)
2. **SSL Automático:** Coolify geralmente configura SSL automaticamente via Let's Encrypt
3. **Redeploy Necessário:** Sempre faça redeploy após alterar variáveis de ambiente
4. **Teste Localmente:** Use `https://dnschecker.org` para verificar propagação global
5. **Backup:** Antes de alterar DNS, anote os valores antigos

---

## 🆘 Precisa de Ajuda?

Se encontrar problemas:

1. Verifique os logs do Coolify (Backend e Frontend)
2. Teste com `curl` se a API está respondendo
3. Verifique console do navegador (F12) para erros
4. Confirme se todos os DNS estão propagados

---

**Última atualização:** 2026-01-19