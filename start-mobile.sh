#!/bin/bash

clear
echo "═══════════════════════════════════════════════════════════"
echo "  🎬 FILFIL - MODO CELULAR (Acesse de qualquer lugar!)"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar se cloudflared está instalado
if ! command -v cloudflared &> /dev/null; then
    echo -e "${RED}❌ Cloudflare Tunnel não está instalado${NC}"
    echo ""
    echo "📥 INSTALAÇÃO RÁPIDA:"
    echo "   Cole no terminal e aperte Enter:"
    echo ""
    echo -e "${BLUE}   brew install cloudflared${NC}"
    echo ""
    echo "   Ou baixe em: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/"
    echo ""
    read -p "Pressione Enter para sair..."
    exit 1
fi

echo -e "${GREEN}✅ Cloudflare Tunnel instalado!${NC}"
echo ""

# Verificar/criar ambiente virtual
cd backend

if [ ! -d "venv" ]; then
    echo "🔧 Criando ambiente virtual..."
    python3 -m venv venv
fi

echo "🔧 Ativando ambiente virtual..."
source venv/bin/activate

echo "📦 Verificando dependências..."
pip install -q flask flask-cors gunicorn werkzeug requests 2>/dev/null

echo -e "${GREEN}✅ Tudo pronto!${NC}"
echo ""

# Iniciar backend em background
echo "🚀 Iniciando servidor..."
python3 app.py > /tmp/filfil-backend.log 2>&1 &
BACKEND_PID=$!

# Aguardar backend iniciar
echo "⏳ Aguardando servidor iniciar..."
for i in {1..10}; do
    if curl -s http://localhost:8080/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Servidor iniciado!${NC}"
        break
    fi
    sleep 1
    echo -n "."
done

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  🌐 INICIANDO TÚNEL PARA CELULAR..."
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "⏳ Aguarde a URL aparecer abaixo..."
echo ""

# Função para encerrar tudo ao sair
cleanup() {
    echo ""
    echo "🛑 Parando servidor..."
    kill $BACKEND_PID 2>/dev/null
    kill $TUNNEL_PID 2>/dev/null
    echo -e "${GREEN}✅ Servidor parado${NC}"
    exit 0
}

trap cleanup INT

# Iniciar tunnel e mostrar URL
cloudflared tunnel --url http://localhost:8080 2>&1 &
TUNNEL_PID=$!

# Aguardar e extrair URL
sleep 5

URL=""
while [ -z "$URL" ]; do
    URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' /tmp/filfil-backend.log 2>/dev/null | head -1)
    if [ -z "$URL" ]; then
        sleep 2
    fi
done

clear
echo "═══════════════════════════════════════════════════════════"
echo -e "  ${GREEN}🎉 SUCESSO! SEU FILFIL ESTÁ ONLINE!${NC}"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo -e "  📱 ${YELLOW}PARA ACESSAR DO CELULAR:${NC}"
echo ""
echo -e "  ${BLUE}$URL${NC}"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  📝 INSTRUÇÕES:"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "  1. Abra o navegador do seu celular"
echo "  2. Digite a URL acima ☝️"
echo "  3. Aproveite os filmes! 🍿"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  ⚠️  AVISOS:"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "  • Essa URL muda toda vez que reiniciar"
echo "  • Funciona enquanto esse Mac estiver ligado e conectado"
echo "  • Para parar: Pressione ${YELLOW}Ctrl+C${NC}"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""

# Manter rodando
wait
