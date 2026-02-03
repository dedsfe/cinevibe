@echo off
echo =========================================
echo    FILFIL - Iniciar Servidor Local
echo =========================================
echo.

:: Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    echo Instale Python de https://python.org
    pause
    exit /b 1
)

:: Verificar/instalar dependencias
echo [1/3] Verificando dependencias...
if not exist backend\venv (
    echo Criando ambiente virtual...
    python -m venv backend\venv
)

call backend\venv\Scripts\activate.bat
pip install -q flask flask-cors gunicorn werkzeug requests

:: Iniciar backend
echo [2/3] Iniciando backend na porta 8080...
cd backend
start "Backend Server" cmd /c "python app.py"

:: Aguardar backend iniciar
echo [3/3] Aguardando servidor iniciar...
timeout /t 3 /nobreak >nul

:: Verificar se ngrok está instalado
where ngrok >nul 2>&1
if errorlevel 1 (
    echo.
    echo =========================================
    echo    NGROK NAO ENCONTRADO
    echo =========================================
    echo Para acesso externo (opcional):
    echo 1. Baixe ngrok de https://ngrok.com/download
    echo 2. Extraia ngrok.exe para esta pasta
    echo 3. Execute: ngrok config add-authtoken SEU_TOKEN
    echo 4. Rode: ngrok http 8080
    echo.
    echo Acesse localmente: http://localhost:8080
    echo =========================================
) else (
    echo.
    echo =========================================
    echo    INICIANDO NGROK...
    echo =========================================
    start "Ngrok Tunnel" cmd /c "ngrok http 8080"
    timeout /t 2 /nobreak >nul
)

echo.
echo =========================================
echo    SERVIDOR INICIADO!
echo =========================================
echo Local:    http://localhost:8080
echo Health:   http://localhost:8080/api/health
echo Catalog:  http://localhost:8080/api/catalog
echo.
echo Para parar: Feche as janelas do backend
echo =========================================

pause
