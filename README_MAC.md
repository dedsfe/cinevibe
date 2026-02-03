# 🍎 Filfil no Mac (Local - Sem Deploy!)

Roda tudo no seu Mac, sem precisar de Railway, Render ou qualquer deploy!

---

## 🚀 Passo a Passo

### 1. Clone o repositório

```bash
cd ~/Desktop  # ou onde quiser
git clone https://github.com/dedsfe/cinevibe.git filfil
cd filfil
```

### 2. Inicie o servidor

```bash
chmod +x start-mac.sh
./start-mac.sh
```

**Pronto!** O servidor vai iniciar em http://localhost:8080

---

## 🎬 Como assistir os filmes

### Opção A: Direto pelo backend (mais rápido)

1. Abra no navegador: http://localhost:8080/api/catalog
2. Você verá a lista de filmes em JSON
3. Copie o `embedUrl` de algum filme
4. Cole no navegador para assistir!

### Opção B: Usar o frontend bonito (Vercel)

1. O frontend já está no ar: https://front-end-videos-omega.vercel.app
2. Mas ele precisa apontar pro seu backend local
3. **Temporariamente**, edite o arquivo `src/config.js`:

```javascript
// Mude isso:
export const API_BASE_URL = 'http://localhost:8080/api';
```

4. Rode o frontend localmente:
```bash
npm install
npm run dev
```

5. Acesse: http://localhost:5173

---

## 📁 O que vem no clone?

```
filfil/
├── backend/
│   ├── app.py          ← Servidor Flask
│   ├── links.db        ← Banco com 200+ filmes!
│   └── ...
├── src/                ← Frontend React
├── start-mac.sh        ← Script para iniciar
└── ...
```

**O banco `links.db` já tem todos os filmes!** Não precisa fazer nada.

---

## 🔧 Comandos úteis

### Ver filmes no banco:
```bash
cd backend
sqlite3 links.db "SELECT title FROM links LIMIT 10;"
```

### Verificar se está rodando:
```bash
curl http://localhost:8080/api/health
```

### Parar o servidor:
Pressione `Ctrl+C` no terminal

---

## ❓ Problemas comuns

### "Permission denied"
```bash
chmod +x start-mac.sh
```

### "Python não encontrado"
```bash
brew install python3
```

### "Porta 8080 em uso"
```bash
# Mate o processo na porta 8080
lsof -ti:8080 | xargs kill -9
```

### Banco parece vazio?
```bash
# Verifique se o arquivo existe
ls -lh backend/links.db

# Se estiver vazio, restaure do backup
cp backend/links.db.backup backend/links.db
```

---

## ✅ Resumo

| O que você quer | Comando |
|----------------|---------|
| Rodar backend | `./start-mac.sh` |
| Ver filmes direto | http://localhost:8080/api/catalog |
| Rodar frontend | `npm install && npm run dev` |

---

**Dúvidas?** Me avise! 🎬
