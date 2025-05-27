
# Trading Signals Pro - Setup Instructions

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)
```bash
python start_system.py
```

### Option 2: Manual Setup

#### 1. Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Start the backend API
cd src/backend
python integrated_api.py
```

#### 2. Frontend Setup
```bash
# Install Node.js dependencies
npm install

# Start the development server
npm run dev
```

## 📝 Configuration

### Environment Variables
Create a `.env` file in the root directory:

```env
# Oanda API (Required for live data)
OANDA_API_KEY=your_oanda_api_key_here
OANDA_ACCOUNT_ID=your_oanda_account_id_here
OANDA_ENVIRONMENT=practice

# Telegram Notifications (Optional)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Trading Configuration
CURRENCY_PAIR=EUR_USD
TIMEFRAME=H1
MAX_PIPS_DISTANCE=15.0

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

### Frontend Configuration
Update `.env.local`:

```env
VITE_API_URL=http://localhost:8000
VITE_DEFAULT_PROXIMITY_DISTANCE=15
VITE_AUTO_REFRESH_INTERVAL=30000
```

## 🔧 Features

### ✅ Implemented Features
- **Real-time Signal Generation**: Multi-timeframe technical analysis
- **Proximity Filtering**: Show only signals close to current market price
- **Live Market Data**: Real-time price feeds
- **Responsive UI**: Modern React interface with Tailwind CSS
- **System Health Monitoring**: API status and data freshness
- **Signal Notifications**: Toast notifications for new opportunities
- **Copy Trading Signals**: Easy signal sharing
- **Auto-refresh**: Configurable real-time updates

### 🎯 Signal Types
- **BUY/SELL Signals**: Based on technical indicators
- **Multiple Take Profits**: TP1, TP2, TP3 levels
- **Risk Management**: Stop loss calculations
- **Strength Rating**: Signal confidence percentage
- **Proximity Score**: Distance from entry price

### 📊 Technical Indicators
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- SMA (Simple Moving Averages)
- Bollinger Bands
- Stochastic Oscillator
- ATR (Average True Range)

### 🔄 Data Sources
- **Primary**: OANDA API (live forex data)
- **Fallback**: Mock data for demo/development
- **Alternative**: Twelve Data, Alpha Vantage (configurable)

## 🌐 API Endpoints

| Endpoint | Description | Parameters |
|----------|-------------|------------|
| `GET /` | API information | - |
| `GET /signals` | All active signals | - |
| `GET /proximity-signals` | Proximity filtered signals | `max_distance` (pips) |
| `GET /signal` | Latest signal | - |
| `GET /market-data` | Current market data | - |
| `GET /health` | System health check | - |

## 📱 User Interface

### Main Dashboard
- Signal statistics overview
- System status indicators
- Real-time data feeds
- Configuration controls

### Signal Tables
- Proximity-filtered signals
- All active signals
- Market data overview
- Interactive signal cards

### Features
- Copy signal details
- Configurable proximity distance
- Auto-refresh toggle
- Live status indicators
- Toast notifications

## 🔒 Security & Best Practices

### API Keys
- Store in `.env` file (not committed)
- Use practice accounts for testing
- Rotate keys regularly

### Development
- Backend runs on port 8000
- Frontend runs on port 5173
- CORS enabled for development
- Error handling and fallbacks

## 🚨 Troubleshooting

### Common Issues

#### Backend won't start
```bash
# Check if port 8000 is available
lsof -i :8000

# Install missing dependencies
pip install -r requirements.txt
```

#### Frontend connection issues
```bash
# Check if backend is running
curl http://localhost:8000/health

# Verify environment variables
cat .env.local
```

#### No real data
- Verify OANDA API credentials
- Check internet connection
- Review logs in terminal

### Mock Data Mode
The system automatically falls back to mock data if:
- API keys are not configured
- External APIs are unavailable
- Network issues occur

## 📈 System Architecture

```
Frontend (React + TypeScript)
     ↓ HTTP/REST
Backend (FastAPI + Python)
     ↓ WebSocket/REST
External APIs (OANDA, etc.)
     ↓ Market Data
Signal Generation Engine
     ↓ Filtered Signals
User Interface
```

## 🎯 Next Steps

1. **Configure your API keys** in `.env`
2. **Start the system** using `python start_system.py`
3. **Open the web interface** at http://localhost:5173
4. **Monitor signals** and adjust proximity settings
5. **Set up notifications** (Telegram integration)

## 💡 Tips

- Start with practice/demo accounts
- Test proximity filtering with different distances
- Monitor system health regularly
- Use notifications for important signals
- Keep API keys secure

---

🎉 **Your Trading Signals Pro system is now ready!**

For support or questions, check the logs or review the source code documentation.
```

## 🛠 Development

### Project Structure
```
├── src/
│   ├── components/         # React components
│   ├── hooks/             # Custom React hooks
│   ├── services/          # API services
│   ├── backend/           # Python backend
│   ├── data/             # Data fetchers
│   ├── signals/          # Signal management
│   └── filters/          # Signal filters
├── config/               # Configuration
├── .env                 # Environment variables
└── requirements.txt     # Python dependencies
```

### Code Quality
- TypeScript for type safety
- React Query for data management
- Tailwind CSS for styling
- FastAPI for backend
- Comprehensive error handling
