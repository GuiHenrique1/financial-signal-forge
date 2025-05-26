
import pandas as pd
import numpy as np
import pandas_ta as ta
from typing import Optional, Dict, Any
import logging
from config import Config

logger = logging.getLogger(__name__)

class TradingStrategy:
    """
    Technical analysis strategy for generating trading signals
    """
    
    def __init__(self):
        self.last_signal_time = None
        self.min_signal_interval = 300  # 5 minutes minimum between signals
        
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators
        
        Args:
            df: OHLCV DataFrame
            
        Returns:
            DataFrame with indicators added
        """
        try:
            # Make a copy to avoid modifying original data
            data = df.copy()
            
            # RSI - Relative Strength Index
            data['rsi'] = ta.rsi(data['close'], length=Config.RSI_PERIOD)
            
            # MACD - Moving Average Convergence Divergence
            macd_data = ta.macd(
                data['close'],
                fast=Config.MACD_FAST,
                slow=Config.MACD_SLOW,
                signal=Config.MACD_SIGNAL
            )
            data['macd'] = macd_data[f'MACD_{Config.MACD_FAST}_{Config.MACD_SLOW}_{Config.MACD_SIGNAL}']
            data['macd_signal'] = macd_data[f'MACDs_{Config.MACD_FAST}_{Config.MACD_SLOW}_{Config.MACD_SIGNAL}']
            data['macd_hist'] = macd_data[f'MACDh_{Config.MACD_FAST}_{Config.MACD_SLOW}_{Config.MACD_SIGNAL}']
            
            # Simple Moving Averages
            data['sma_fast'] = ta.sma(data['close'], length=Config.SMA_FAST)
            data['sma_slow'] = ta.sma(data['close'], length=Config.SMA_SLOW)
            
            # Bollinger Bands
            bb_data = ta.bbands(data['close'], length=20, std=2)
            data['bb_upper'] = bb_data['BBU_20_2.0']
            data['bb_middle'] = bb_data['BBM_20_2.0']
            data['bb_lower'] = bb_data['BBL_20_2.0']
            
            # Average True Range (for volatility)
            data['atr'] = ta.atr(data['high'], data['low'], data['close'], length=14)
            
            # Stochastic Oscillator
            stoch_data = ta.stoch(data['high'], data['low'], data['close'])
            data['stoch_k'] = stoch_data['STOCHk_14_3_3']
            data['stoch_d'] = stoch_data['STOCHd_14_3_3']
            
            return data
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            raise
    
    def detect_volatility(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        Detect high volatility periods using price standard deviation
        
        Args:
            df: OHLCV DataFrame with indicators
            period: Period for volatility calculation
            
        Returns:
            Boolean series indicating high volatility periods
        """
        price_returns = df['close'].pct_change()
        volatility = price_returns.rolling(window=period).std()
        
        # High volatility threshold (top 20% of volatility values)
        volatility_threshold = volatility.quantile(0.8)
        
        return volatility > volatility_threshold
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on technical indicators
        
        Args:
            df: OHLCV DataFrame
            
        Returns:
            DataFrame with signals added
        """
        try:
            # Calculate indicators
            data = self.calculate_indicators(df)
            
            # Detect high volatility periods
            high_volatility = self.detect_volatility(data)
            
            # Initialize signal column
            data['signal'] = None
            data['signal_strength'] = 0.0
            data['signal_reason'] = ''
            
            # Generate signals for each row
            for i in range(len(data)):
                if i < max(Config.RSI_PERIOD, Config.MACD_SLOW, Config.SMA_SLOW):
                    continue  # Skip rows without enough data for indicators
                
                current = data.iloc[i]
                
                # Skip if in high volatility period (too risky)
                if high_volatility.iloc[i]:
                    continue
                
                signal, strength, reason = self._evaluate_signal_conditions(current, data.iloc[i-1])
                
                data.iloc[i, data.columns.get_loc('signal')] = signal
                data.iloc[i, data.columns.get_loc('signal_strength')] = strength
                data.iloc[i, data.columns.get_loc('signal_reason')] = reason
            
            return data
            
        except Exception as e:
            logger.error(f"Error generating signals: {e}")
            raise
    
    def _evaluate_signal_conditions(self, current: pd.Series, previous: pd.Series) -> tuple:
        """
        Evaluate signal conditions for current candle
        
        Args:
            current: Current candle data
            previous: Previous candle data
            
        Returns:
            Tuple of (signal, strength, reason)
        """
        signal = None
        strength = 0.0
        reasons = []
        
        # Check for CALL signal conditions
        call_conditions = 0
        call_reasons = []
        
        # RSI oversold and recovering
        if current['rsi'] < Config.RSI_OVERSOLD and current['rsi'] > previous['rsi']:
            call_conditions += 1
            call_reasons.append("RSI oversold recovery")
        
        # MACD bullish crossover
        if (current['macd_hist'] > 0 and previous['macd_hist'] <= 0):
            call_conditions += 1
            call_reasons.append("MACD bullish crossover")
        
        # Price above fast SMA and fast SMA above slow SMA
        if (current['close'] > current['sma_fast'] and 
            current['sma_fast'] > current['sma_slow']):
            call_conditions += 1
            call_reasons.append("Price above moving averages")
        
        # Stochastic oversold and recovering
        if current['stoch_k'] < 20 and current['stoch_k'] > previous['stoch_k']:
            call_conditions += 1
            call_reasons.append("Stochastic oversold recovery")
        
        # Check for PUT signal conditions
        put_conditions = 0
        put_reasons = []
        
        # RSI overbought and declining
        if current['rsi'] > Config.RSI_OVERBOUGHT and current['rsi'] < previous['rsi']:
            put_conditions += 1
            put_reasons.append("RSI overbought decline")
        
        # MACD bearish crossover
        if (current['macd_hist'] < 0 and previous['macd_hist'] >= 0):
            put_conditions += 1
            put_reasons.append("MACD bearish crossover")
        
        # Price below fast SMA and fast SMA below slow SMA
        if (current['close'] < current['sma_fast'] and 
            current['sma_fast'] < current['sma_slow']):
            put_conditions += 1
            put_reasons.append("Price below moving averages")
        
        # Stochastic overbought and declining
        if current['stoch_k'] > 80 and current['stoch_k'] < previous['stoch_k']:
            put_conditions += 1
            put_reasons.append("Stochastic overbought decline")
        
        # Determine signal based on conditions
        if call_conditions >= 2:  # At least 2 bullish conditions
            signal = "CALL"
            strength = min(call_conditions / 4.0, 1.0)  # Normalize to 0-1
            reasons = call_reasons
        elif put_conditions >= 2:  # At least 2 bearish conditions
            signal = "PUT"
            strength = min(put_conditions / 4.0, 1.0)  # Normalize to 0-1
            reasons = put_reasons
        
        reason_text = "; ".join(reasons) if reasons else ""
        
        return signal, strength, reason_text
    
    def get_latest_signal(self, df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Get the latest signal from the data
        
        Args:
            df: DataFrame with signals
            
        Returns:
            Latest signal information or None
        """
        try:
            data_with_signals = self.generate_signals(df)
            
            # Get the latest non-null signal
            latest_signals = data_with_signals[data_with_signals['signal'].notna()]
            
            if latest_signals.empty:
                return None
            
            latest = latest_signals.iloc[-1]
            
            return {
                'timestamp': latest.name,
                'pair': Config.CURRENCY_PAIR,
                'timeframe': Config.TIMEFRAME,
                'signal': latest['signal'],
                'strength': latest['signal_strength'],
                'reason': latest['signal_reason'],
                'price': latest['close'],
                'rsi': latest['rsi'],
                'macd': latest['macd'],
                'macd_signal': latest['macd_signal'],
                'macd_hist': latest['macd_hist']
            }
            
        except Exception as e:
            logger.error(f"Error getting latest signal: {e}")
            return None

# Singleton instance
strategy = TradingStrategy()
