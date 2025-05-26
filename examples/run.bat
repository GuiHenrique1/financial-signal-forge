
@echo off
REM Script para Windows - Iniciar o bot de sinais financeiros

echo 🚀 Iniciando Bot de Sinais Financeiros...

REM Verificar se o arquivo .env existe
if not exist .env (
    echo ❌ Arquivo .env não encontrado!
    echo Por favor, copie .env.example para .env e configure as variáveis.
    pause
    exit /b 1
)

REM Verificar se o ambiente virtual existe
if not exist venv (
    echo 📦 Criando ambiente virtual...
    python -m venv venv
)

REM Ativar ambiente virtual
echo 🔄 Ativando ambiente virtual...
call venv\Scripts\activate

REM Instalar dependências
echo 📚 Instalando dependências...
pip install -r requirements.txt

REM Verificar configuração
echo 🔍 Verificando configuração...
python -c "from config import Config; Config.validate(); print('✅ Configuração válida!')"
if errorlevel 1 (
    echo ❌ Erro na configuração. Verifique o arquivo .env
    pause
    exit /b 1
)

REM Criar diretórios necessários
if not exist logs mkdir logs
if not exist data mkdir data

echo 🌐 Iniciando API...
start "Trading API" cmd /k "uvicorn api:app --host 0.0.0.0 --port 8000 --log-level info"

echo ⏳ Aguardando API inicializar...
timeout /t 5 /nobreak > nul

echo 🤖 Iniciando Bot do Telegram...
start "Telegram Bot" cmd /k "python telegram_bot.py"

echo ✅ Sistema iniciado com sucesso!
echo.
echo 📊 Endpoints disponíveis:
echo   • API: http://localhost:8000
echo   • Dashboard: http://localhost:8000/dashboard
echo   • Documentação: http://localhost:8000/docs
echo   • Saúde: http://localhost:8000/health
echo.
echo 📝 Para parar os serviços, feche as janelas abertas
echo.

pause
