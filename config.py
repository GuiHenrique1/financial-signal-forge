
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Oanda API
    OANDA_API_KEY = os.getenv('OANDA_API_KEY')
    OANDA_ACCOUNT_ID = os.getenv('OANDA_ACCOUNT_ID')
    OANDA_ENVIRONMENT = os.getenv('OANDA_ENVIRONMENT', 'practice')
    
    # Trading
    CURRENCY_PAIR = os.getenv('CURRENCY_PAIR', 'EUR_USD')
    TIMEFRAME = os.getenv('TIMEFRAME', 'M5')
    DATA_FETCH_INTERVAL = int(os.getenv('DATA_FETCH_INTERVAL', 300))
    MAX_CANDLES = int(os.getenv('MAX_CANDLES', 500))
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    SIGNAL_CHAT_ID = os.getenv('SIGNAL_CHAT_ID')
    
    # Strategy
    RSI_PERIOD = int(os.getenv('RSI_PERIOD', 14))
    RSI_OVERSOLD = float(os.getenv('RSI_OVERSOLD', 30))
    RSI_OVERBOUGHT = float(os.getenv('RSI_OVERBOUGHT', 70))
    MACD_FAST = int(os.getenv('MACD_FAST', 12))
    MACD_SLOW = int(os.getenv('MACD_SLOW', 26))
    MACD_SIGNAL = int(os.getenv('MACD_SIGNAL', 9))
    SMA_FAST = int(os.getenv('SMA_FAST', 10))
    SMA_SLOW = int(os.getenv('SMA_SLOW', 20))
    
    # API
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', 8000))
    CACHE_DURATION = int(os.getenv('CACHE_DURATION', 5))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required_vars = [
            'OANDA_API_KEY',
            'OANDA_ACCOUNT_ID',
            'TELEGRAM_BOT_TOKEN',
            'SIGNAL_CHAT_ID'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True
