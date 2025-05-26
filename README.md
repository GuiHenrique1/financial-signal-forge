
# 🤖 Bot de Sinais Financeiros

Um sistema completo de análise técnica e alertas automáticos para trading, integrado com APIs de mercado financeiro e notificações via Telegram.

## 🌟 Características

- **Coleta de dados em tempo real** via API Oanda
- **Análise técnica avançada** com múltiplos indicadores (RSI, MACD, Médias Móveis, Bollinger Bands, Stochastic)
- **API REST** completa com FastAPI
- **Bot do Telegram** para alertas automáticos
- **Interface web** com dashboard interativo
- **Sistema de cache** inteligente
- **Testes automatizados** para garantir qualidade
- **Deploy com Docker** para facilitar instalação

## 📊 Indicadores Utilizados

### Estratégia de Sinais
O sistema gera sinais **CALL** (compra) e **PUT** (venda) baseado na convergência de múltiplos indicadores:

**Sinais CALL (📈):**
- RSI < 30 e em recuperação
- MACD cruzamento bullish (histograma > 0)
- Preço acima das médias móveis
- Stochastic oversold e recuperando

**Sinais PUT (📉):**
- RSI > 70 e em declínio
- MACD cruzamento bearish (histograma < 0)
- Preço abaixo das médias móveis
- Stochastic overbought e declinando

### Filtros de Qualidade
- **Filtro de volatilidade**: Evita sinais em períodos de alta volatilidade
- **Força do sinal**: Calcula a convergência dos indicadores (0-100%)
- **Intervalo mínimo**: Previne spam de sinais (15 minutos entre sinais similares)

## 🚀 Instalação Rápida

### 1. Clonar o Repositório
```bash
git clone <url-do-repositorio>
cd trading-signals-bot
```

### 2. Configurar Ambiente
```bash
# Copiar configuração
cp .env.example .env

# Editar com suas credenciais
nano .env
```

### 3. Executar com Docker (Recomendado)
```bash
# Configurar variáveis no .env
docker-compose up -d
```

### 4. Ou Executar Localmente
```bash
# Instalar dependências
pip install -r requirements.txt

# Executar script automatizado
chmod +x examples/run.sh
./examples/run.sh
```

## ⚙️ Configuração

### Variáveis Essenciais (.env)
```env
# API Oanda (obrigatório)
OANDA_API_KEY=your_api_key_here
OANDA_ACCOUNT_ID=your_account_id_here
OANDA_ENVIRONMENT=practice

# Telegram (obrigatório)
TELEGRAM_BOT_TOKEN=your_bot_token_here
SIGNAL_CHAT_ID=your_chat_id_here

# Trading (opcional)
CURRENCY_PAIR=EUR_USD
TIMEFRAME=M5
DATA_FETCH_INTERVAL=300
```

### Como Obter Credenciais

**Oanda API:**
1. Acesse [developer.oanda.com](https://developer.oanda.com)
2. Crie uma aplicação
3. Copie API Key e Account ID

**Telegram Bot:**
1. Converse com [@BotFather](https://t.me/BotFather)
2. Use `/newbot` para criar um bot
3. Obtenha o token
4. Use [@userinfobot](https://t.me/userinfobot) para seu Chat ID

## 📡 API Endpoints

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/` | GET | Informações da API |
| `/signal` | GET | Último sinal gerado |
| `/health` | GET | Status de saúde |
| `/status` | GET | Status detalhado do sistema |
| `/dashboard` | GET | Interface web |
| `/docs` | GET | Documentação Swagger |

### Exemplo de Resposta
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

### Comandos Disponíveis
- `/start` - Inicializar bot
- `/help` - Mostrar ajuda
- `/status` - Status do sistema
- `/signal` - Obter último sinal
- `/stop` - Parar alertas automáticos

### Formato dos Alertas
```
📈 EUR/USD — CALL

🕒 M5 — válido por 15 minutos
💰 Preço: 1.05234
📊 Força: 75.0%

Indicadores:
• RSI: 32.5
• MACD: 0.000123

Razão: RSI oversold recovery; MACD bullish crossover

⏰ 14:30:15

⚠️ Risco próprio - Analise antes de operar
```

## 🧪 Testes

### Executar Testes
```bash
# Todos os testes
pytest

# Testes específicos
pytest tests/test_strategy.py -v
pytest tests/test_api.py -v

# Com cobertura
pytest --cov=. tests/
```

### Testes Incluídos
- ✅ Cálculo de indicadores técnicos
- ✅ Geração de sinais
- ✅ Endpoints da API
- ✅ Lógica de cache
- ✅ Validação de dados

## 🐳 Docker

### Estrutura do Docker
```yaml
# docker-compose.yml inclui:
- trading-api      # API principal
- telegram-bot     # Bot do Telegram  
- nginx           # Proxy reverso (opcional)
```

### Comandos Docker
```bash
# Construir e executar
docker-compose up -d

# Ver logs
docker-compose logs -f

# Parar serviços
docker-compose down

# Rebuild
docker-compose up -d --build
```

## 📁 Estrutura do Projeto

```
trading-signals-bot/
├── 📁 docs/                 # Documentação
│   └── USO.md              # Guia detalhado de uso
├── 📁 examples/             # Scripts de exemplo
│   ├── run.sh              # Script Linux/Mac
│   └── run.bat             # Script Windows
├── 📁 tests/                # Testes automatizados
│   ├── test_strategy.py    # Testes da estratégia
│   └── test_api.py         # Testes da API
├── 📄 config.py             # Configurações centralizadas
├── 📄 data_fetcher.py       # Coleta de dados Oanda
├── 📄 strategy.py           # Lógica de análise técnica
├── 📄 api.py                # API REST FastAPI
├── 📄 telegram_bot.py       # Bot do Telegram
├── 📄 requirements.txt      # Dependências Python
├── 📄 Dockerfile            # Configuração Docker
├── 📄 docker-compose.yml    # Orquestração Docker
├── 📄 .env.example          # Modelo de configuração
└── 📄 README.md             # Este arquivo
```

## 🔧 Personalização

### Modificar Estratégia
```python
# Em strategy.py - Adicionar novo indicador
def calculate_indicators(self, df):
    # ... indicadores existentes ...
    data['novo_indicador'] = ta.novo_indicador(data['close'])
    return data

# Modificar condições de sinal
def _evaluate_signal_conditions(self, current, previous):
    # Suas condições personalizadas aqui
    pass
```

### Adicionar Novos Pares
```env
# No .env
CURRENCY_PAIR=GBP_USD  # ou qualquer par suportado pela Oanda
```

### Ajustar Timeframes
```env
# Timeframes suportados: M1, M5, M15, M30, H1, H4, D
TIMEFRAME=M15
```

## 📈 Monitoramento

### Dashboard Web
Acesse `http://localhost:8000/dashboard` para:
- ✅ Último sinal gerado
- ✅ Status em tempo real
- ✅ Atualização automática
- ✅ Links para API

### Logs
```bash
# Ver logs em tempo real
tail -f logs/api.log
tail -f logs/bot.log

# Com Docker
docker-compose logs -f trading-api
docker-compose logs -f telegram-bot
```

### Métricas Importantes
- **Latência da API**: < 2 segundos
- **Idade dos dados**: < 10 minutos
- **Frequência de sinais**: 2-5 por hora (normal)
- **Taxa de sucesso**: Varia com mercado

## ⚠️ Disclaimers

### Riscos
- ⚠️ **Trading envolve riscos significativos**
- ⚠️ **Este sistema é para fins educacionais**
- ⚠️ **Sempre faça sua própria análise**
- ⚠️ **Use conta demo para testes**
- ⚠️ **Não invista mais do que pode perder**

### Limitações
- Sinais baseados apenas em análise técnica
- Não considera fundamentals ou notícias
- Performance passada não garante resultados futuros
- Mercado pode mudar e invalidar estratégias

## 🤝 Contribuindo

### Como Contribuir
1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Faça commit das mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

### Áreas para Contribuição
- 🔄 Novos indicadores técnicos
- 📊 Melhorias na interface web
- 🧪 Mais testes automatizados
- 📚 Documentação adicional
- 🐛 Correção de bugs
- ⚡ Otimizações de performance

## 📞 Suporte

### Problemas Comuns
Consulte [docs/USO.md](docs/USO.md) para solução de problemas detalhada.

### Reportar Bugs
1. Verifique se já não foi reportado
2. Inclua logs relevantes
3. Descreva passos para reproduzir
4. Especifique ambiente (OS, Python version, etc.)

### Recursos Úteis
- 📖 [Documentação Oanda](https://developer.oanda.com/rest-live-v20/introduction/)
- 📖 [Documentação Telegram Bot](https://core.telegram.org/bots/api)
- 📖 [TA-Lib Documentation](https://ta-lib.org/)
- 📖 [FastAPI Documentation](https://fastapi.tiangolo.com/)

## 📜 Licença

Este projeto é licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

**⭐ Se este projeto foi útil, considere dar uma estrela!**

**💡 Sugestões e melhorias são sempre bem-vindas!**
