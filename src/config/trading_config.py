
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
    session_preference: str  # 'london', 'newyork', 'tokyo', 'all'
    min_spread: float = 0.0

@dataclass
class TimeframeConfig:
    code: str
    name: str
    minutes: int
    oanda_granularity: str
    confirmation_weight: float = 1.0

@dataclass
class SessionConfig:
    name: str
    start_hour: int
    end_hour: int
    timezone: str
    active: bool = True

class TradingConfig:
    # Expanded asset list - 30+ pairs
    PAIRS = {
        # Major Forex Pairs
        'EUR_USD': TradingPair('EUR_USD', 'EUR/USD', 0.0001, 4, 'forex', 'all', 1.5),
        'GBP_USD': TradingPair('GBP_USD', 'GBP/USD', 0.0001, 4, 'forex', 'london', 2.0),
        'USD_JPY': TradingPair('USD_JPY', 'USD/JPY', 0.01, 2, 'forex', 'tokyo', 1.8),
        'AUD_USD': TradingPair('AUD_USD', 'AUD/USD', 0.0001, 4, 'forex', 'all', 1.5),
        'NZD_USD': TradingPair('NZD_USD', 'NZD/USD', 0.0001, 4, 'forex', 'all', 2.0),
        'USD_CHF': TradingPair('USD_CHF', 'USD/CHF', 0.0001, 4, 'forex', 'all', 1.8),
        'USD_CAD': TradingPair('USD_CAD', 'USD/CAD', 0.0001, 4, 'forex', 'newyork', 1.5),
        
        # Minor Forex Pairs
        'EUR_JPY': TradingPair('EUR_JPY', 'EUR/JPY', 0.01, 2, 'forex', 'all', 2.5),
        'GBP_JPY': TradingPair('GBP_JPY', 'GBP/JPY', 0.01, 2, 'forex', 'all', 3.0),
        'AUD_JPY': TradingPair('AUD_JPY', 'AUD/JPY', 0.01, 2, 'forex', 'tokyo', 2.8),
        'NZD_JPY': TradingPair('NZD_JPY', 'NZD/JPY', 0.01, 2, 'forex', 'tokyo', 3.0),
        'CHF_JPY': TradingPair('CHF_JPY', 'CHF/JPY', 0.01, 2, 'forex', 'all', 2.8),
        'CAD_JPY': TradingPair('CAD_JPY', 'CAD/JPY', 0.01, 2, 'forex', 'all', 2.5),
        'EUR_GBP': TradingPair('EUR_GBP', 'EUR/GBP', 0.0001, 4, 'forex', 'london', 1.5),
        'EUR_CHF': TradingPair('EUR_CHF', 'EUR/CHF', 0.0001, 4, 'forex', 'all', 1.8),
        'EUR_CAD': TradingPair('EUR_CAD', 'EUR/CAD', 0.0001, 4, 'forex', 'all', 2.0),
        'EUR_AUD': TradingPair('EUR_AUD', 'EUR/AUD', 0.0001, 4, 'forex', 'all', 2.2),
        'GBP_CHF': TradingPair('GBP_CHF', 'GBP/CHF', 0.0001, 4, 'forex', 'london', 2.5),
        'GBP_CAD': TradingPair('GBP_CAD', 'GBP/CAD', 0.0001, 4, 'forex', 'all', 2.8),
        'GBP_AUD': TradingPair('GBP_AUD', 'GBP/AUD', 0.0001, 4, 'forex', 'all', 3.0),
        'AUD_CHF': TradingPair('AUD_CHF', 'AUD/CHF', 0.0001, 4, 'forex', 'all', 2.5),
        'AUD_CAD': TradingPair('AUD_CAD', 'AUD/CAD', 0.0001, 4, 'forex', 'all', 2.2),
        'NZD_CHF': TradingPair('NZD_CHF', 'NZD/CHF', 0.0001, 4, 'forex', 'all', 2.8),
        'NZD_CAD': TradingPair('NZD_CAD', 'NZD/CAD', 0.0001, 4, 'forex', 'all', 2.5),
        'CAD_CHF': TradingPair('CAD_CHF', 'CAD/CHF', 0.0001, 4, 'forex', 'all', 2.2),
        
        # Commodities
        'XAU_USD': TradingPair('XAU_USD', 'Gold/USD', 0.01, 2, 'commodity', 'all', 0.30),
        'XAG_USD': TradingPair('XAG_USD', 'Silver/USD', 0.001, 3, 'commodity', 'all', 0.02),
        'WTICO_USD': TradingPair('WTICO_USD', 'WTI Oil/USD', 0.01, 2, 'commodity', 'newyork', 0.05),
        'BCO_USD': TradingPair('BCO_USD', 'Brent Oil/USD', 0.01, 2, 'commodity', 'london', 0.05),
        
        # Cryptocurrencies
        'BTC_USD': TradingPair('BTC_USD', 'Bitcoin/USD', 1.0, 0, 'crypto', 'all', 50.0),
        'ETH_USD': TradingPair('ETH_USD', 'Ethereum/USD', 0.01, 2, 'crypto', 'all', 5.0),
        'LTC_USD': TradingPair('LTC_USD', 'Litecoin/USD', 0.01, 2, 'crypto', 'all', 1.0),
        'XRP_USD': TradingPair('XRP_USD', 'Ripple/USD', 0.0001, 4, 'crypto', 'all', 0.001),
        'ADA_USD': TradingPair('ADA_USD', 'Cardano/USD', 0.0001, 4, 'crypto', 'all', 0.005),
        'DOT_USD': TradingPair('DOT_USD', 'Polkadot/USD', 0.01, 2, 'crypto', 'all', 0.10),
    }
    
    # Enhanced timeframes with confirmation weights
    TIMEFRAMES = {
        'M15': TimeframeConfig('M15', '15 Minutes', 15, 'M15', 0.5),
        'M30': TimeframeConfig('M30', '30 Minutes', 30, 'M30', 0.7),
        'H1': TimeframeConfig('H1', '1 Hour', 60, 'H1', 1.0),
        'H4': TimeframeConfig('H4', '4 Hours', 240, 'H4', 1.5),
        'D1': TimeframeConfig('D1', 'Daily', 1440, 'D', 2.0),
        'W1': TimeframeConfig('W1', 'Weekly', 10080, 'W', 3.0),
    }
    
    # Trading sessions
    SESSIONS = {
        'tokyo': SessionConfig('Tokyo', 0, 9, 'Asia/Tokyo'),
        'london': SessionConfig('London', 8, 17, 'Europe/London'),
        'newyork': SessionConfig('New York', 13, 22, 'America/New_York'),
        'sydney': SessionConfig('Sydney', 22, 7, 'Australia/Sydney'),
    }
    
    # API Configuration
    OANDA_API_KEY = os.getenv('OANDA_API_KEY')
    OANDA_ACCOUNT_ID = os.getenv('OANDA_ACCOUNT_ID')
    OANDA_ENVIRONMENT = os.getenv('OANDA_ENVIRONMENT', 'practice')
    
    # Alternative API Keys
    TWELVE_DATA_API_KEY = os.getenv('TWELVE_DATA_API_KEY')
    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
    BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
    POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')
    
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    # Discord Configuration
    DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
    
    # Email Configuration
    EMAIL_SMTP_HOST = os.getenv('EMAIL_SMTP_HOST')
    EMAIL_SMTP_PORT = int(os.getenv('EMAIL_SMTP_PORT', 587))
    EMAIL_USERNAME = os.getenv('EMAIL_USERNAME')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    EMAIL_RECIPIENTS = os.getenv('EMAIL_RECIPIENTS', '').split(',')
    
    # Enhanced Technical Analysis Parameters
    RSI_PERIOD = 14
    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70
    
    MACD_FAST = 12
    MACD_SLOW = 26
    MACD_SIGNAL = 9
    
    SMA_FAST = 50
    SMA_SLOW = 200
    
    ATR_PERIOD = 14
    ATR_MULTIPLIER = 2.0
    ATR_MIN_THRESHOLD = 0.5  # Minimum ATR for signal validity
    
    # Volume indicators
    OBV_PERIOD = 20
    VWAP_PERIOD = 20
    
    # Multi-timeframe confirmation
    MTF_CONFIRMATION_ENABLED = os.getenv('MTF_CONFIRMATION_ENABLED', 'true').lower() == 'true'
    MTF_HIGHER_TIMEFRAMES = ['H4', 'D1']  # Confirm signals with these timeframes
    
    # Session filtering
    SESSION_FILTERING_ENABLED = os.getenv('SESSION_FILTERING_ENABLED', 'true').lower() == 'true'
    ACTIVE_SESSIONS = os.getenv('ACTIVE_SESSIONS', 'london,newyork,tokyo').split(',')
    
    # Risk Management
    DEFAULT_RISK_PERCENT = float(os.getenv('DEFAULT_RISK_PERCENT', 1.0))
    MAX_RISK_PERCENT = float(os.getenv('MAX_RISK_PERCENT', 5.0))
    MIN_RISK_PERCENT = float(os.getenv('MIN_RISK_PERCENT', 0.1))
    
    # Position sizing modes
    POSITION_SIZING_MODE = os.getenv('POSITION_SIZING_MODE', 'risk_percent')  # 'risk_percent' or 'fixed_lot'
    FIXED_LOT_SIZE = float(os.getenv('FIXED_LOT_SIZE', 0.01))
    
    # Signal filtering
    MIN_SIGNAL_STRENGTH = float(os.getenv('MIN_SIGNAL_STRENGTH', 0.6))
    MAX_SIGNALS_PER_PAIR_PER_DAY = int(os.getenv('MAX_SIGNALS_PER_PAIR_PER_DAY', 3))
    
    # Economic calendar integration
    ECONOMIC_CALENDAR_ENABLED = os.getenv('ECONOMIC_CALENDAR_ENABLED', 'false').lower() == 'true'
    ECONOMIC_CALENDAR_API_KEY = os.getenv('ECONOMIC_CALENDAR_API_KEY')
    
    # News impact filtering
    HIGH_IMPACT_NEWS_BUFFER_MINUTES = int(os.getenv('HIGH_IMPACT_NEWS_BUFFER_MINUTES', 30))
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///trading_signals.db')
    
    # API Settings
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', 8000))
    API_KEY = os.getenv('API_KEY', 'your_api_key_here')
    
    # Performance tracking
    PERFORMANCE_TRACKING_ENABLED = os.getenv('PERFORMANCE_TRACKING_ENABLED', 'true').lower() == 'true'
    BACKTEST_ENABLED = os.getenv('BACKTEST_ENABLED', 'true').lower() == 'true'
    
    @classmethod
    def validate_config(cls):
        """Enhanced configuration validation"""
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
        
        # Validate risk parameters
        if cls.DEFAULT_RISK_PERCENT < cls.MIN_RISK_PERCENT or cls.DEFAULT_RISK_PERCENT > cls.MAX_RISK_PERCENT:
            raise ValueError(f"Default risk percent must be between {cls.MIN_RISK_PERCENT}% and {cls.MAX_RISK_PERCENT}%")
        
        return True
    
    @classmethod
    def get_pair_config(cls, symbol: str) -> TradingPair:
        """Get configuration for a trading pair"""
        return cls.PAIRS.get(symbol)
    
    @classmethod
    def get_timeframe_config(cls, timeframe: str) -> TimeframeConfig:
        """Get configuration for a timeframe"""
        return cls.TIMEFRAMES.get(timeframe)
    
    @classmethod
    def get_session_config(cls, session: str) -> SessionConfig:
        """Get configuration for a trading session"""
        return cls.SESSIONS.get(session)
    
    @classmethod
    def get_active_pairs(cls) -> List[str]:
        """Get list of active trading pairs"""
        return list(cls.PAIRS.keys())
    
    @classmethod
    def get_pairs_by_category(cls, category: str) -> List[str]:
        """Get pairs filtered by category"""
        return [symbol for symbol, pair in cls.PAIRS.items() if pair.category == category]
    
    @classmethod
    def get_pairs_by_session(cls, session: str) -> List[str]:
        """Get pairs that are active during a specific session"""
        return [symbol for symbol, pair in cls.PAIRS.items() 
                if pair.session_preference == session or pair.session_preference == 'all']
