#!/bin/bash

echo "🎬 FILFIL - Iniciar no Mac"
echo "================================"

# Verificar se está na pasta certa
if [ ! -f "backend/app.py" ]; then
    echo "❌ ERRO: Não encontrei backend/app.py"
    echo "💡 Dica: Rode isso da pasta raiz do projeto"
    exit 1
fi

echo ""
echo "[1/3] Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não encontrado!"
    echo "📥 Instale: https://python.org ou 'brew install python3'"
    exit 1
fi
python3 --version

echo ""
echo "[2/3] Instalando dependências..."
cd backend

# Criar ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo "   Criando ambiente virtual..."
    python3 -m venv venv
fi

# Ativar ambiente
source venv/bin/activate

# Instalar dependências
pip install -q flask flask-cors gunicorn werkzeug requests 2>/dev/null
echo "   ✅ Dependências OK"

echo ""
echo "[3/3] Iniciando servidor..."
echo ""
echo "🚀 Backend iniciando em http://localhost:8080"
echo ""
echo "📋 Endpoints disponíveis:"
echo "   • http://localhost:8080/api/health"
echo "   • http://localhost:8080/api/catalog"
echo "   • http://localhost:8080/api/series"
echo ""
echo "🌐 Para ver no navegador:"
echo "   1. Abra: http://localhost:8080"
echo "   2. Ou use o frontend Vercel com URL local"
echo ""
echo "⚠️  Para parar: Pressione Ctrl+C"
echo "================================"
echo ""

# Iniciar o servidor
python3 app.py
