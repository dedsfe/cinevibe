#!/bin/bash
echo "🎬 FILFIL - RÁPIDO"
echo "=================="
echo ""

cd ~/Desktop/filfil 2>/dev/null || cd ~/filfil 2>/dev/null

# Preparar ambiente
cd backend
source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
pip install -q flask flask-cors gunicorn werkzeug requests beautifulsoup4 2>/dev/null

# Iniciar servidor
echo "🚀 Iniciando servidor..."
python3 app.py > /tmp/filfil.log 2>&1 &
PID=$!
sleep 5

echo "✅ Servidor iniciado!"
echo ""
echo "🌐 Criando link público..."
echo "   (Aguarde 5-10 segundos...)"
echo ""

# Iniciar tunnel e mostrar tudo
cloudflared tunnel --url http://localhost:8080
