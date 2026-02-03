# 📱 Acessar do Celular (Fora de Casa)

Guia super simples para assistir filmes no celular de qualquer lugar!

---

## 🚀 MODO SUPER FÁCIL

### 1. Instale o Cloudflare (só uma vez!)

Abra o Terminal do Mac e cole:

```bash
brew install cloudflared
```

**Pronto!** Nunca mais precisa instalar.

---

### 2. Inicie o servidor

No Terminal, vá até a pasta do filfil:

```bash
cd ~/Desktop/filfil
```

Execute:

```bash
./start-mobile.sh
```

---

### 3. Aguarde a URL

O script vai mostrar algo assim:

```
═══════════════════════════════════════════════════════════
  🎉 SUCESSO! SEU FILFIL ESTÁ ONLINE!
═══════════════════════════════════════════════════════════

  📱 PARA ACESSAR DO CELULAR:

  https://abc123.trycloudflare.com

═══════════════════════════════════════════════════════════
```

---

### 4. No celular

1. Abra o navegador (Safari, Chrome)
2. Digite a URL que apareceu (ex: `https://abc123.trycloudflare.com`)
3. **Pronto!** 🍿

---

## ⚠️ Importante

| Situação | O que fazer |
|----------|-------------|
| URL mudou | Normal! Rode `./start-mobile.sh` de novo |
| Mac desligou | Precisa rodar o script novamente |
| Não carrega | Verifique se o Mac tem internet |

---

## 🛑 Para parar

No Terminal, aperte: `Ctrl + C`

Isso para o servidor e o túnel.

---

## ❓ Problemas?

### "brew: command not found"
Instale o Homebrew primeiro:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### "Permission denied"
De permissão:
```bash
chmod +x start-mobile.sh
```

### "cloudflared: command not found"
Reabra o Terminal ou rode:
```bash
export PATH="/opt/homebrew/bin:$PATH"
```

---

## 🎯 Resumo

```bash
# 1. Instale (só uma vez)
brew install cloudflared

# 2. Execute sempre que quiser assistir
cd ~/Desktop/filfil
./start-mobile.sh

# 3. Cole a URL no celular
```

**Bom filme!** 🎬
