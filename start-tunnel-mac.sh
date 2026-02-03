#!/bin/bash

echo "🚀 FILFIL + Cloudflare Tunnel (GRÁTIS!)"
echo "========================================"

# Verifica se cloudflared está instalado
if ! command -v cloudflared &> /dev/null; then
    echo ""
    echo "❌ Cloudflare Tunnel não instalado"
    echo ""
    echo "📥 Instalação RÁPIDA:"
    echo "   brew install cloudflared"
    echo ""
    echo "Ou visite: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/"
    echo ""
    read -p "Pressione Enter para sair..."
    exit 1
fi

echo ""
echo "[1/3] Iniciando backend..."
cd backend
source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
pip install -q flask flask-cors gunicorn werkzeug requests 2>/dev/null

# Inicia backend em background
python3 app.py &
BACKEND_PID=$!

# Aguarda iniciar
sleep 3

echo ""
echo "[2/3] Iniciando Cloudflare Tunnel..."
echo "   (Isso cria uma URL pública gratuita!)"
echo ""

# Inicia tunnel e captura URL
cloudflared tunnel --url http://localhost:8080 2>&1 | while read line; do
    echo "$line"
    
    # Detecta quando a URL aparece
    if echo "$line" | grep -q "trycloudflare.com"; then
        URL=$(echo "$line" | grep -o 'https://[^[:space:]]*\.trycloudflare\.com')
        echo ""
        echo "========================================"
        echo "   🎉 URL PÚBLICA CRIADA!"
        echo "========================================"
        echo ""
        echo "   📱 Para acessar do celular:"
        echo "   $URL"
        echo ""
        echo "   📋 Ou use no Vercel:"
        echo "   VITE_API_URL = $URL/api"
        echo ""
        echo "   ⚠️  Essa URL muda toda vez que reiniciar"
        echo "========================================"
    fi
done

# Quando parar, mata o backend
trap "kill $BACKEND_PID 2>/dev/null; exit" INT
wait
