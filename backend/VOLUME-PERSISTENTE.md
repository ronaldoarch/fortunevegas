# 📦 Configuração de Volume Persistente para Banners e Logos

Este guia explica como configurar armazenamento persistente no Coolify para que os banners e logos não desapareçam após cada deploy.

## 🎯 Objetivo

Garantir que os arquivos de upload (banners, logos, promoções) sejam preservados mesmo após:
- Deploy de nova versão
- Restart do container
- Rebuild da aplicação

## 📍 Diretórios que Precisam de Persistência

No container Docker, os uploads são salvos em:
- `/app/uploads/banners/` - Banners do site
- `/app/uploads/logos/` - Logos do site  
- `/app/uploads/promotions/` - Imagens de promoções

## 🔧 Configuração no Coolify

### Passo 1: Acessar a Configuração de Volumes

1. No Coolify, vá até sua aplicação **Fortune Vegas Backend**
2. No menu lateral, clique em **Persistent Storage** (ou **Volumes**)
3. Clique no botão **Add Volume Mount** (ou **+ Add**)

### Passo 2: Configurar o Volume Mount

No diálogo "Add Volume Mount", preencha:

#### **Name** (Nome do Volume)
```
fortunevegas-uploads
```
*Nome descritivo para identificar o volume*

#### **Source Path** (Caminho no Host)
```
/root/fortunevegas-uploads
```
ou
```
/data/fortunevegas-uploads
```
*Caminho no servidor onde os arquivos serão armazenados permanentemente*

**Nota**: O caminho exato pode variar dependendo da configuração do seu servidor Coolify. Alguns exemplos:
- `/root/volumes/fortunevegas-uploads`
- `/data/fortunevegas-uploads`
- `/var/lib/coolify/volumes/fortunevegas-uploads`

#### **Destination Path** (Caminho no Container) ⚠️ **OBRIGATÓRIO**
```
/app/uploads
```
*Este é o caminho DENTRO do container onde os uploads são salvos*

### Passo 3: Salvar e Aplicar

1. Clique em **Add** para criar o volume mount
2. O Coolify irá criar o diretório no host (se não existir)
3. O volume será montado automaticamente no próximo deploy/restart

## ✅ Verificação

### 1. Verificar se o Volume está Montado

Após o deploy, você pode verificar executando um comando no container:

```bash
# No Coolify, vá em "Execute Command" ou use SSH
ls -la /app/uploads
```

Deve mostrar:
```
drwxr-xr-x banners/
drwxr-xr-x logos/
drwxr-xr-x promotions/
```

### 2. Testar Persistência

1. Faça upload de um banner no painel admin
2. Verifique se o arquivo existe em `/app/uploads/banners/` dentro do container
3. Faça um redeploy da aplicação
4. Verifique novamente - o arquivo deve ainda estar lá!

### 3. Verificar no Host

Se você tem acesso SSH ao servidor, pode verificar diretamente:

```bash
ls -la /root/fortunevegas-uploads
# ou o caminho que você configurou em Source Path
```

## 🔄 Migração de Arquivos Existentes

Se você já tem banners/logos salvos e quer migrá-los para o volume persistente:

### Opção 1: Via Coolify (Recomendado)

1. Configure o volume mount primeiro
2. Faça um redeploy
3. Os arquivos novos serão salvos no volume persistente
4. Para arquivos antigos, você pode fazer upload novamente ou copiar manualmente

### Opção 2: Via SSH/Comandos

```bash
# 1. Acesse o container antigo (antes do volume)
docker exec -it <container-id> ls /app/uploads

# 2. Copie os arquivos para o volume no host
docker cp <container-id>:/app/uploads /root/fortunevegas-uploads

# 3. Configure o volume mount no Coolify
# 4. Faça redeploy - os arquivos estarão disponíveis
```

## 📝 Estrutura de Diretórios

Após configurar o volume, a estrutura será:

```
Host (Servidor):
/root/fortunevegas-uploads/
├── banners/
│   ├── 1769115012-1d682836.png
│   └── 1769114224-a1bf0c39.png
├── logos/
│   └── logo-123456.png
└── promotions/
    └── promo-789.png

Container:
/app/uploads/  (montado do host)
├── banners/   (mesmos arquivos)
├── logos/     (mesmos arquivos)
└── promotions/ (mesmos arquivos)
```

## ⚠️ Importante

1. **Backup**: Mesmo com volume persistente, faça backups regulares dos uploads
2. **Permissões**: O Coolify geralmente gerencia permissões automaticamente, mas se houver problemas:
   ```bash
   chmod -R 755 /root/fortunevegas-uploads
   chown -R root:root /root/fortunevegas-uploads
   ```
3. **Espaço em Disco**: Monitore o espaço em disco do servidor, especialmente se houver muitos uploads

## 🐛 Troubleshooting

### Problema: Arquivos não aparecem após deploy

**Solução:**
- Verifique se o volume mount está configurado corretamente
- Confirme que o **Destination Path** é exatamente `/app/uploads`
- Verifique os logs do container para erros de permissão

### Problema: Erro de permissão ao fazer upload

**Solução:**
```bash
# No servidor host
chmod -R 777 /root/fortunevegas-uploads
```

### Problema: Volume não está montado

**Solução:**
- Verifique se o volume mount está ativo no Coolify
- Faça um redeploy completo (não apenas restart)
- Verifique os logs do deploy para erros relacionados a volumes

## 📚 Referências

- [Coolify Volume Documentation](https://coolify.io/docs/volumes)
- [Docker Volumes](https://docs.docker.com/storage/volumes/)

---

**Última atualização**: 2026-02-05
