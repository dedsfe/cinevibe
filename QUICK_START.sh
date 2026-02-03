#!/bin/bash
echo "🎬 FILFIL - RÁPIDO"
echo "=================="
echo ""

# Verificar pasta
if [ ! -d "$HOME/Desktop/filfil" ]; then
    echo "📥 Clonando repositório..."
    cd ~/Desktop
    git clone https://github.com/dedsfe/cinevibe.git filfil
fi

cd ~/Desktop/filfil

# Verificar cloudflared
if ! command -v cloudflared &> /dev/null; then
    echo "📦 Instalando Cloudflare..."
    brew install cloudflared
fi

# Preparar ambiente
cd backend
source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
echo "📦 Instalando dependências..."
pip install -q -r requirements.txt beautifulsoup4 2>/dev/null

# Iniciar
echo ""
echo "🚀 Iniciando servidor..."
python3 app.py > /tmp/filfil.log 2>&1 &
PID=$!

# Aguardar iniciar
echo "⏳ Aguardando..."
sleep 5

# Verificar se iniciou
if curl -s http://localhost:8080/api/health > /dev/null 2>&1; then
    echo "✅ Servidor OK!"
else
    echo "⚠️  Aguardando mais um pouco..."
    sleep 3
fi

# Tunnel
echo ""
echo "🌐 Criando link público..."
echo ""
cloudflared tunnel --url http://localhost:8080 2>&1 | grep -m1 "trycloudflare.com" | sed 's/.*https:/https:/'

echo ""
echo "☝️ COLE ESSE LINK NO CELULAR"
echo "Para parar: Ctrl+C"
kill $PID 2>/dev/null
