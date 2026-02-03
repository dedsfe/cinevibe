#!/bin/bash

echo "🌐 FILFIL - Acesso na Rede Local"
echo "================================"

# Pega o IP do Mac
IP=$(ipconfig getifaddr en0 || ipconfig getifaddr en1 || hostname -I | awk '{print $1}')

echo ""
echo "📱 Para acessar do celular:"
echo "   1. Certifique-se que celular e Mac estão na mesma WiFi"
echo "   2. No celular, acesse:"
echo ""
echo "   🎯 http://$IP:8080/api/catalog"
echo ""
echo "   Ou use o frontend Vercel com essa URL"
echo ""
echo "⚠️  Se não funcionar, pode ser firewall do Mac"
echo "   Vá em: Preferências do Sistema > Segurança > Firewall"
echo ""

cd backend
source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
pip install -q flask flask-cors gunicorn werkzeug requests 2>/dev/null

echo "🚀 Iniciando servidor..."
echo "   Aguardando conexões na rede local..."
echo ""
python3 app.py
