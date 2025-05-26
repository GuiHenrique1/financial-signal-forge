
# Guia de Uso - Bot de Sinais Financeiros

## 📋 Índice
1. [Instalação](#instalação)
2. [Configuração](#configuração)
3. [Execução](#execução)
4. [Uso da API](#uso-da-api)
5. [Bot do Telegram](#bot-do-telegram)
6. [Monitoramento](#monitoramento)
7. [Solução de Problemas](#solução-de-problemas)

## 🚀 Instalação

### Pré-requisitos
- Python 3.9 ou superior
- Conta na Oanda (demo ou real)
- Bot do Telegram criado via @BotFather

### 1. Clone ou baixe o projeto
```bash
git clone <url-do-repositorio>
cd trading-signals-bot
```

### 2. Instale as dependências
```bash
# Criar ambiente virtual (recomendado)
python -m venv venv

# Ativar ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 3. Instalar TA-Lib (se necessário)
**No Windows:**
- Baixe o wheel apropriado de: https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
- Instale: `pip install TA_Lib-0.4.XX-cpXX-cpXXm-win_amd64.whl`

**No Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt-get install libta-lib-dev

# macOS
brew install ta-lib
```

## ⚙️ Configuração

### 1. Criar arquivo de configuração
```bash
cp .env.example .env
```

### 2. Editar o arquivo .env
```env
# Configuração da Oanda
OANDA_API_KEY=seu_api_key_aqui
OANDA_ACCOUNT_ID=seu_account_id_aqui
OANDA_ENVIRONMENT=practice  # ou 'live' para conta real

# Configuração de Trading
CURRENCY_PAIR=EUR_USD
TIMEFRAME=M5
DATA_FETCH_INTERVAL=300

# Configuração do Telegram
TELEGRAM_BOT_TOKEN=seu_bot_token_aqui
SIGNAL_CHAT_ID=seu_chat_id_aqui

# Parâmetros da Estratégia
RSI_PERIOD=14
RSI_OVERSOLD=30
RSI_OVERBOUGHT=70
```

### 3. Obter credenciais necessárias

**API da Oanda:**
1. Acesse [Oanda Developer Portal](https://developer.oanda.com/)
2. Crie uma aplicação
3. Copie o API Key e Account ID

**Bot do Telegram:**
1. Converse com @BotFather no Telegram
2. Use `/newbot` para criar um novo bot
3. Copie o token fornecido
4. Para o CHAT_ID, use @userinfobot para obter seu ID

## 🎯 Execução

### Método 1: Execução individual

**1. Iniciar API:**
```bash
python api.py
# ou
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

**2. Iniciar Bot do Telegram (em outro terminal):**
```bash
python telegram_bot.py
```

### Método 2: Script automatizado
```bash
# Linux/Mac
chmod +x examples/run.sh
./examples/run.sh

# Windows
examples\run.bat
```

### Método 3: Docker
```bash
# Construir imagem
docker build -t trading-bot .

# Executar com docker-compose
docker-compose up -d
```

## 📡 Uso da API

### Endpoints disponíveis:

**GET /** - Informações da API
```bash
curl http://localhost:8000/
```

**GET /signal** - Obter último sinal
```bash
curl http://localhost:8000/signal
```

**GET /health** - Status de saúde
```bash
curl http://localhost:8000/health
```

**GET /status** - Status detalhado
```bash
curl http://localhost:8000/status
```

**GET /dashboard** - Interface web
```
http://localhost:8000/dashboard
```

**GET /docs** - Documentação Swagger
```
http://localhost:8000/docs
```

### Exemplo de resposta da API:
```json
{
  "pair": "EUR_USD",
  "timeframe": "M5",
  "signal": "CALL",
  "strength": 0.75,
  "reason": "RSI oversold recovery; MACD bullish crossover",
  "price": 1.0523,
  "indicators": {
    "rsi": 32.5,
    "macd": 0.000123,
    "macd_signal": 0.000089,
    "macd_hist": 0.000034
  },
  "timestamp": "2023-01-01T12:30:00",
  "generated_at": 1672574200.123
}
```

## 🤖 Bot do Telegram

### Comandos disponíveis:

- `/start` - Iniciar o bot e receber boas-vindas
- `/help` - Mostrar ajuda e comandos
- `/status` - Verificar status do sistema
- `/signal` - Obter último sinal manualmente
- `/stop` - Parar alertas automáticos

### Tipos de sinais:
- 📈 **CALL** - Sinal de compra
- 📉 **PUT** - Sinal de venda
- ⏸️ **No Signal** - Aguardar melhor oportunidade

### Configuração do chat:
1. Adicione o bot ao grupo/canal desejado
2. Torne o bot administrador (para enviar mensagens)
3. Use o ID do chat no arquivo .env

## 📊 Monitoramento

### Logs
Os logs são gerados automaticamente e mostram:
- Conexões com APIs
- Sinais gerados
- Erros e avisos
- Performance do sistema

### Métricas importantes:
- **Data Age**: Idade dos dados (deve ser < 10 minutos)
- **Signal Frequency**: Frequência de sinais (normal: 2-5 por hora)
- **API Response Time**: Tempo de resposta (deve ser < 2 segundos)

### Dashboard Web
Acesse `http://localhost:8000/dashboard` para:
- Ver último sinal gerado
- Verificar status em tempo real
- Atualização automática a cada 30 segundos

## 🔧 Solução de Problemas

### Problemas comuns:

**1. Erro de conexão com Oanda**
```
Solução:
- Verificar API_KEY e ACCOUNT_ID
- Confirmar que o ambiente está correto (practice/live)
- Verificar conexão com internet
```

**2. Bot do Telegram não responde**
```
Solução:
- Verificar TELEGRAM_BOT_TOKEN
- Confirmar que o bot foi iniciado com /start
- Verificar se o chat_id está correto
```

**3. Sinais não são gerados**
```
Solução:
- Verificar se há dados suficientes (>50 candles)
- Ajustar parâmetros da estratégia
- Verificar logs para erros específicos
```

**4. API retorna erro 503**
```
Solução:
- Aguardar alguns minutos para coleta de dados
- Verificar conexão com Oanda
- Reiniciar o serviço se necessário
```

### Comandos úteis:

**Verificar logs:**
```bash
tail -f logs/trading_bot.log
```

**Testar conexão Oanda:**
```bash
python -c "from data_fetcher import data_fetcher; import asyncio; asyncio.run(data_fetcher.fetch_candles(10))"
```

**Testar estratégia:**
```bash
python -m pytest tests/test_strategy.py -v
```

**Verificar saúde da API:**
```bash
curl http://localhost:8000/health
```

## 📈 Personalização

### Ajustar estratégia:
Edite `strategy.py` para modificar:
- Condições de entrada
- Indicadores utilizados
- Força mínima do sinal
- Filtros de volatilidade

### Adicionar novos indicadores:
```python
# Em strategy.py, método calculate_indicators()
data['meu_indicador'] = ta.meu_indicador(data['close'])
```

### Configurar alertas personalizados:
```python
# Em telegram_bot.py, método format_signal_message()
# Personalize a formatação das mensagens
```

## 🛡️ Segurança

### Melhores práticas:
1. **Nunca** compartilhe suas chaves de API
2. Use sempre ambiente "practice" para testes
3. Mantenha o arquivo .env seguro (não commite no git)
4. Monitore regularmente os logs
5. Configure alertas de segurança na Oanda

### Backup:
- Faça backup regular do arquivo .env
- Salve configurações personalizadas
- Documente mudanças na estratégia

## 📞 Suporte

Para problemas técnicos:
1. Consulte os logs primeiro
2. Verifique a documentação da API
3. Execute os testes automatizados
4. Consulte a comunidade ou suporte técnico

**Disclaimer**: Este bot é para fins educacionais. Sempre faça sua própria análise antes de operar. O trading envolve riscos significativos.
