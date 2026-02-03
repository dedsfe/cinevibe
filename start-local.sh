#!/bin/bash

echo "========================================="
echo "   FILFIL - Iniciar Servidor Local"
echo "========================================="
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "[ERRO] Python3 não encontrado!"
    echo "Instale Python de https://python.org"
    exit 1
fi

# Verificar/instalar dependencias
echo "[1/3] Verificando dependencias..."
cd backend

if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q flask flask-cors gunicorn werkzeug requests 2>/dev/null

# Iniciar backend
echo "[2/3] Iniciando backend na porta 8080..."
python app.py &
BACKEND_PID=$!

# Aguardar iniciar
sleep 3

echo ""
echo "========================================="
echo "   SERVIDOR INICIADO!"
echo "========================================="
echo "Local:    http://localhost:8080"
echo "Health:   http://localhost:8080/api/health"
echo "Catalog:  http://localhost:8080/api/catalog"
echo ""

# Verificar ngrok
if command -v ngrok &> /dev/null; then
    echo "Ngrok encontrado! Iniciando túnel..."
    ngrok http 8080 &
    NGROK_PID=$!
    sleep 2
    echo ""
    echo "Acesse o URL do ngrok acima ☝️"
else
    echo "Para acesso externo (opcional):"
    echo "1. Instale ngrok: brew install ngrok (Mac) ou baixe de ngrok.com (Windows)"
    echo "2. Configure: ngrok config add-authtoken SEU_TOKEN"
    echo "3. Rode: ngrok http 8080"
fi

echo ""
echo "Para parar: Pressione Ctrl+C"
echo "========================================="

# Aguardar
wait $BACKEND_PID
