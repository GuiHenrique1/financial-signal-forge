
#!/bin/bash

# Script para iniciar o bot de sinais financeiros
# Uso: ./run.sh

echo "🚀 Iniciando Bot de Sinais Financeiros..."

# Verificar se o arquivo .env existe
if [ ! -f .env ]; then
    echo "❌ Arquivo .env não encontrado!"
    echo "Por favor, copie .env.example para .env e configure as variáveis."
    exit 1
fi

# Verificar se o ambiente virtual existe
if [ ! -d "venv" ]; then
    echo "📦 Criando ambiente virtual..."
    python -m venv venv
fi

# Ativar ambiente virtual
echo "🔄 Ativando ambiente virtual..."
source venv/bin/activate

# Instalar dependências
echo "📚 Instalando dependências..."
pip install -r requirements.txt

# Verificar configuração
echo "🔍 Verificando configuração..."
python -c "
from config import Config
try:
    Config.validate()
    print('✅ Configuração válida!')
except Exception as e:
    print(f'❌ Erro na configuração: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Erro na configuração. Verifique o arquivo .env"
    exit 1
fi

# Criar diretórios necessários
mkdir -p logs
mkdir -p data

# Função para cleanup
cleanup() {
    echo "🛑 Parando serviços..."
    kill $API_PID 2>/dev/null
    kill $BOT_PID 2>/dev/null
    echo "✅ Serviços parados."
    exit 0
}

# Configurar trap para cleanup
trap cleanup SIGINT SIGTERM

# Iniciar API em background
echo "🌐 Iniciando API..."
uvicorn api:app --host 0.0.0.0 --port 8000 --log-level info > logs/api.log 2>&1 &
API_PID=$!

# Aguardar API inicializar
echo "⏳ Aguardando API inicializar..."
sleep 5

# Verificar se API está rodando
if ! curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Erro ao iniciar API. Verificar logs/api.log"
    kill $API_PID 2>/dev/null
    exit 1
fi

echo "✅ API iniciada com sucesso!"

# Iniciar Bot do Telegram
echo "🤖 Iniciando Bot do Telegram..."
python telegram_bot.py > logs/bot.log 2>&1 &
BOT_PID=$!

echo "✅ Bot do Telegram iniciado!"

# Mostrar status
echo ""
echo "🎉 Sistema iniciado com sucesso!"
echo ""
echo "📊 Endpoints disponíveis:"
echo "  • API: http://localhost:8000"
echo "  • Dashboard: http://localhost:8000/dashboard"
echo "  • Documentação: http://localhost:8000/docs"
echo "  • Saúde: http://localhost:8000/health"
echo ""
echo "📝 Logs:"
echo "  • API: logs/api.log"
echo "  • Bot: logs/bot.log"
echo ""
echo "⌨️  Para parar os serviços, pressione Ctrl+C"
echo ""

# Monitorar serviços
while true; do
    # Verificar se processos ainda estão rodando
    if ! kill -0 $API_PID 2>/dev/null; then
        echo "❌ API parou inesperadamente!"
        break
    fi
    
    if ! kill -0 $BOT_PID 2>/dev/null; then
        echo "❌ Bot parou inesperadamente!"
        break
    fi
    
    # Mostrar status a cada 30 segundos
    sleep 30
    
    # Verificar saúde da API
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ $(date): Sistema rodando normalmente"
    else
        echo "⚠️  $(date): API com problemas"
    fi
done

# Cleanup
cleanup
