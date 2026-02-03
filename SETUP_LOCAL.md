# 🎬 Filfil - Setup Local (Sem Railway!)

Rode tudo no seu PC - muito mais fácil e funciona 100%!

---

## 🚀 Opção 1: Só Local (Mais Fácil)

### Windows:
1. **Clone o repo:**
   ```bash
   git clone https://github.com/dedsfe/cinevibe.git
   cd cinevibe
   ```

2. **Execute:**
   ```
   start-local.bat
   ```

3. **Acesse:** http://localhost:8080

### Mac/Linux:
```bash
git clone https://github.com/dedsfe/cinevibe.git
cd cinevibe
chmod +x start-local.sh
./start-local.sh
```

Acesse: http://localhost:8080

---

## 🌐 Opção 2: Local + Acesso Externo (Ngrok)

Se quiser acessar de qualquer lugar (celular, etc):

1. **Instale ngrok:**
   - Windows: Baixe de https://ngrok.com/download
   - Mac: `brew install ngrok`
   - Linux: `snap install ngrok`

2. **Configure (grátis):**
   ```bash
   ngrok config add-authtoken 2uxxxx  # seu token
   ```

3. **Inicie:**
   ```bash
   # Terminal 1 - Backend
   cd cinevibe/backend
   python app.py
   
   # Terminal 2 - Ngrok
   ngrok http 8080
   ```

4. **Copie a URL do ngrok** (ex: `https://abc123.ngrok.io`)

5. **Atualize o frontend:**
   - Vá em https://vercel.com/dashboard
   - Selecione seu projeto
   - Settings > Environment Variables
   - Adicione: `VITE_API_URL` = `https://abc123.ngrok.io/api`
   - Redeploy

---

## 📁 Estrutura do Projeto

```
cinevibe/
├── backend/           ← Flask API + SQLite
│   ├── app.py        ← Servidor
│   ├── links.db      ← Banco de dados (filmes)
│   └── ...
├── src/              ← Frontend React
│   └── config.js     ← URL da API
├── start-local.bat   ← Windows
├── start-local.sh    ← Mac/Linux
└── dist/             ← Build para Vercel
```

---

## ⚡ Comandos Úteis

### Ver se está rodando:
```bash
curl http://localhost:8080/api/health
```

### Ver filmes no banco:
```bash
# Windows
sqlite3 backend/links.db "SELECT title FROM links LIMIT 5;"

# Mac/Linux  
sqlite3 backend/links.db "SELECT title FROM links LIMIT 5;"
```

---

## 🛠️ Problemas Comuns

### "Python não encontrado"
- Instale: https://python.org
- Marque "Add to PATH" na instalação

### "Porta 8080 em uso"
```bash
# Mac/Linux
lsof -ti:8080 | xargs kill -9

# Windows
netstat -ano | findstr :8080
taskkill /PID <PID> /F
```

### Banco vazio?
O banco `links.db` já tem 200+ filmes. Se estiver vazio, copie do backup:
```bash
cp backend/links.db.backup backend/links.db
```

---

## ✅ Pronto!

Agora é só acessar o frontend Vercel que ele vai buscar os filmes do seu PC!

Qualquer problema, me avise.
