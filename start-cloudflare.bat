@echo off
echo =========================================
echo    FILFIL + CLOUDFLARE TUNNEL (GRATIS!)
echo =========================================
echo.

:: Verificar se cloudflared está instalado
where cloudflared >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Cloudflare Tunnel nao encontrado!
    echo.
    echo =========================================
    echo    INSTALACAO RAPIDA:
    echo =========================================
    echo 1. Acesse: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
    echo 2. Baixe o .exe para Windows
    echo 3. Extraia cloudflared.exe para esta pasta
    echo.
    echo Ou via Chocolatey:
    echo    choco install cloudflared
    echo.
    pause
    exit /b 1
)

:: Iniciar backend
echo [1/3] Iniciando backend...
cd backend
if not exist venv (
    echo Criando ambiente virtual...
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install -q flask flask-cors gunicorn werkzeug requests

start "Backend Server" cmd /c "python app.py"
timeout /t 3 /nobreak >nul

:: Iniciar tunnel
echo [2/3] Iniciando Cloudflare Tunnel...
echo    (Isso criara uma URL publica gratuita!)
echo.
start "Cloudflare Tunnel" cmd /c "cloudflared tunnel --url http://localhost:8080"

:: Aguardar
timeout /t 5 /nobreak >nul

echo.
echo =========================================
echo    TUNNEL INICIADO!
echo =========================================
echo.
echo A URL publica vai aparecer na janela do Cloudflare
echo (algo como: https://xxxx.trycloudflare.com)
echo.
echo 1. Copie essa URL
echo 2. Cole no Vercel: Settings ^> Environment Variables
echo 3. Nome: VITE_API_URL
echo 4. Valor: https://xxxx.trycloudflare.com/api
echo.
pause
