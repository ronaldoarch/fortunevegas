# ⚡ Configuração Rápida - Volume Persistente

## 🎯 Configuração no Coolify (3 passos)

### 1️⃣ Acesse Persistent Storage
- Vá na sua aplicação **Fortune Vegas Backend**
- Menu lateral → **Persistent Storage**
- Clique em **Add Volume Mount**

### 2️⃣ Preencha os Campos

| Campo | Valor |
|-------|-------|
| **Name** | `fortunevegas-uploads` |
| **Source Path** | `/root/fortunevegas-uploads` |
| **Destination Path** | `/app/uploads` ⚠️ |

### 3️⃣ Salve e Faça Redeploy
- Clique em **Add**
- Faça um **Redeploy** da aplicação

## ✅ Pronto!

Agora seus banners e logos serão preservados após cada deploy.

---

📖 **Guia Completo**: [VOLUME-PERSISTENTE.md](./VOLUME-PERSISTENTE.md)
