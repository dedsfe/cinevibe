# 📱 Assistir no Celular

Guia completo para acessar do celular quando rodar no Mac.

---

## 🥇 Opção 1: Mesma WiFi (Mais Fácil)

**Requisito:** Mac e celular na mesma rede WiFi

### No Mac:
```bash
cd ~/Desktop/filfil
chmod +x start-local-network.sh
./start-local-network.sh
```

### No celular:
1. Abra o navegador
2. Digite o IP que apareceu no terminal
3. Exemplo: `http://192.168.1.45:8080/api/catalog`

**Pronto!** ✅

---

## 🥈 Opção 2: Cloudflare Tunnel (Qualquer lugar)

**Funciona de qualquer lugar do mundo!**

### Instalação única:
```bash
brew install cloudflared
```

### Para usar:
```bash
cd ~/Desktop/filfil
chmod +x start-tunnel-mac.sh
./start-tunnel-mac.sh
```

### No celular:
1. Aguarde aparecer a URL (ex: `https://abc123.trycloudflare.com`)
2. Cole no navegador do celular

**URL muda a cada reinício** - normal no plano grátis

---

## 🥉 Opção 3: LocalTunnel (Alternativa)

**Também funciona de qualquer lugar!**

### Instalação única:
```bash
npm install -g localtunnel
```

### Para usar:
```bash
cd ~/Desktop/filfil
chmod +x start-ltunnel-mac.sh
./start-ltunnel-mac.sh
```

---

## 📋 Resumo

| Opção | Funciona onde? | Instalação | URL fixa? |
|-------|---------------|------------|-----------|
| **Mesma WiFi** | Só em casa | Nenhuma! | ✅ Sim (IP local) |
| **Cloudflare** | Qualquer lugar | `brew install cloudflared` | ❌ Muda |
| **LocalTunnel** | Qualquer lugar | `npm install -g localtunnel` | ❌ Muda |

---

## 🎯 Recomendação

- **Só vai usar em casa?** → Opção 1 (Mesma WiFi)
- **Quer acessar de fora?** → Opção 2 (Cloudflare)

---

## ❓ Problemas?

### "Não carrega no celular"
- Verifique se Mac e celular estão na mesma WiFi
- Tente desativar firewall do Mac: Preferências > Segurança > Firewall

### "Tunnel não conecta"
- Verifique se o backend está rodando: http://localhost:8080
- Tente a outra opção (Cloudflare ou LocalTunnel)

### "URL muito grande"
- Use um encurtador: https://bit.ly ou https://tinyurl.com

---

**Bom filme! 🍿**
