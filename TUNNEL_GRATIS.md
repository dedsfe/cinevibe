# 🆓 Túnel Gratuito para Acesso Externo

Opções **100% gratuitas** para acessar seu backend de qualquer lugar!

---

## 🥇 Opção 1: Cloudflare Tunnel (Recomendado)

**Totalmente grátis, sem limite de uso!**

### Instalação:

**Windows:**
```powershell
# Via Chocolatey (recomendado)
choco install cloudflared

# Ou baixe manual:
# https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
```

**Mac:**
```bash
brew install cloudflared
```

**Linux:**
```bash
# Debian/Ubuntu
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb
```

### Uso:
```bash
# 1. Inicie seu backend
python backend/app.py

# 2. Em outro terminal, rode:
cloudflared tunnel --url http://localhost:8080
```

**Pronto!** A URL (ex: `https://abcd.trycloudflare.com`) aparece no terminal.

---

## 🥈 Opção 2: LocalTunnel (Mais Simples)

**Gratuito, sem instalação complicada!**

### Instalação:

**Precisa ter Node.js instalado:** https://nodejs.org

```bash
npm install -g localtunnel
```

### Uso:
```bash
# 1. Inicie seu backend
python backend/app.py

# 2. Em outro terminal:
lt --port 8080
```

A URL (ex: `https://abcd.loca.lt`) aparece!

---

## 🥉 Opção 3: Expose (PHP)

**Se tiver PHP instalado:**

```bash
# Instale
composer global require beyondcode/expose

# Rode
expose share http://localhost:8080
```

---

## 🔄 Opção 4: Serveo (SSH - Sem Instalar Nada!)

**Se tiver SSH (Git Bash no Windows funciona):**

```bash
ssh -R 80:localhost:8080 serveo.net
```

A URL aparece no terminal!

---

## ⚙️ Configurar no Vercel

Depois de ter a URL do túnel:

1. Vá em: https://vercel.com/dashboard
2. Selecione seu projeto
3. **Settings** → **Environment Variables**
4. Adicione:
   - **Name:** `VITE_API_URL`
   - **Value:** `https://xxxx.trycloudflare.com/api` (sua URL + `/api`)
5. Clique **Save**
6. Vá em **Deployments** → Clique nos **3 pontos** do último deploy → **Redeploy**

---

## 📋 Resumo

| Ferramenta | Grátis? | Instalação | Duração |
|------------|---------|------------|---------|
| **Cloudflare** | ✅ Sim | Fácil | Temporário (reinicia muda) |
| **LocalTunnel** | ✅ Sim | Muito fácil | Temporário |
| **Serveo** | ✅ Sim | Nenhuma! | Temporário |
| **Ngrok** | ⚠️ Limitado | Fácil | Precisa de conta |

---

## 💡 Dica Pro

Crie um arquivo `start-tunnel.bat` (Windows) ou `start-tunnel.sh` (Mac/Linux) para iniciar tudo de uma vez!

### Exemplo Windows (`start-tunnel.bat`):
```batch
@echo off
start "Backend" python backend/app.py
timeout /t 3
cloudflared tunnel --url http://localhost:8080
```

---

## ❓ Problemas?

**"Comando não encontrado"**
- Adicione à PATH ou use o caminho completo do executável

**"Tunnel não conecta"**
- Verifique se o backend está rodando: http://localhost:8080/api/health
- Tente outra ferramenta (LocalTunnel, Serveo)

**"URL muda toda vez"**
- Isso é normal nos planos gratuitos
- Para URL fixa, precisa pagar (Cloudflare pago ou ngrok pago)

---

**Recomendo começar com Cloudflare Tunnel ou LocalTunnel!** 🚀
