
import os
from typing import Dict, List
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class TradingPair:
    symbol: str
    name: str
    pip_value: float
    pip_position: int
    category: str

@dataclass
class TimeframeConfig:
    code: str
    name: str
    minutes: int
    oanda_granularity: str

class TradingConfig:
    # Supported trading pairs
    PAIRS = {
        'EUR_USD': TradingPair('EUR_USD', 'EUR/USD', 0.0001, 4, 'forex'),
        'GBP_USD': TradingPair('GBP_USD', 'GBP/USD', 0.0001, 4, 'forex'),
        'USD_JPY': TradingPair('USD_JPY', 'USD/JPY', 0.01, 2, 'forex'),
        'AUD_USD': TradingPair('AUD_USD', 'AUD/USD', 0.0001, 4, 'forex'),
        'USD_CAD': TradingPair('USD_CAD', 'USD/CAD', 0.0001, 4, 'forex'),
        'XAU_USD': TradingPair('XAU_USD', 'Gold/USD', 0.01, 2, 'commodity'),
        'BTC_USD': TradingPair('BTC_USD', 'Bitcoin/USD', 1.0, 0, 'crypto'),
    }
    
    # Supported timeframes
    TIMEFRAMES = {
        'H1': TimeframeConfig('H1', '1 Hour', 60, 'H1'),
        'H4': TimeframeConfig('H4', '4 Hours', 240, 'H4'),
        'D1': TimeframeConfig('D1', 'Daily', 1440, 'D'),
    }
    
    # API Configuration
    OANDA_API_KEY = os.getenv('OANDA_API_KEY')
    OANDA_ACCOUNT_ID = os.getenv('OANDA_ACCOUNT_ID')
    OANDA_ENVIRONMENT = os.getenv('OANDA_ENVIRONMENT', 'practice')
    
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    # Trading Parameters
    RSI_PERIOD = 14
    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70
    
    MACD_FAST = 12
    MACD_SLOW = 26
    MACD_SIGNAL = 9
    
    SMA_FAST = 50
    SMA_SLOW = 200
    
    ATR_PERIOD = 14
    ATR_MULTIPLIER = 2.0  # For stop loss calculation
    
    # Risk Management
    DEFAULT_RISK_PERCENT = 1.0  # 1% of account
    MAX_RISK_PERCENT = 5.0      # Maximum 5% risk
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///trading_signals.db')
    
    # API Settings
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', 8000))
    API_KEY = os.getenv('API_KEY', 'your_api_key_here')
    
    @classmethod
    def validate_config(cls):
        """Validate required configuration"""
        required_vars = [
            'OANDA_API_KEY',
            'OANDA_ACCOUNT_ID',
            'TELEGRAM_BOT_TOKEN',
            'TELEGRAM_CHAT_ID'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True
    
    @classmethod
    def get_pair_config(cls, symbol: str) -> TradingPair:
        """Get configuration for a trading pair"""
        return cls.PAIRS.get(symbol)
    
    @classmethod
    def get_timeframe_config(cls, timeframe: str) -> TimeframeConfig:
        """Get configuration for a timeframe"""
        return cls.TIMEFRAMES.get(timeframe)
