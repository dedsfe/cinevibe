#!/bin/bash

echo "🚀 FILFIL + LocalTunnel (GRÁTIS!)"
echo "=================================="

# Verifica se lt está instalado
if ! command -v lt &> /dev/null; then
    echo ""
    echo "❌ LocalTunnel não instalado"
    echo ""
    echo "📥 Instalação RÁPIDA:"
    echo "   npm install -g localtunnel"
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
sleep 3

echo ""
echo "[2/3] Iniciando LocalTunnel..."
echo ""

# Inicia tunnel
lt --port 8080 &
LT_PID=$!

echo ""
echo "========================================"
echo "   🎉 TUNEL CRIADO!"
echo "========================================"
echo ""
echo "   A URL aparecerá acima ☝️"
echo "   (algo como: https://abc123.loca.lt)"
echo ""
echo "   📱 Cole essa URL no celular"
echo ""
echo "   ⚠️  Pode pedir um IP de verificação"
echo "      Acesse o link que aparecer no terminal"
echo "========================================"

# Quando parar, mata os processos
trap "kill $BACKEND_PID $LT_PID 2>/dev/null; exit" INT
wait
