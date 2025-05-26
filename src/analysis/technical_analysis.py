
import pandas as pd
import numpy as np
import pandas_ta as ta
from typing import Dict, List, Optional, Tuple
import logging
from src.config.trading_config import TradingConfig

logger = logging.getLogger(__name__)

class TechnicalAnalysis:
    """Advanced technical analysis for signal generation"""
    
    def __init__(self):
        self.required_periods = max(
            TradingConfig.RSI_PERIOD,
            TradingConfig.MACD_SLOW,
            TradingConfig.SMA_SLOW,
            TradingConfig.ATR_PERIOD
        ) + 50  # Extra buffer for calculations
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all technical indicators
        
        Args:
            df: OHLCV DataFrame
            
        Returns:
            DataFrame with technical indicators added
        """
        try:
            if len(df) < self.required_periods:
                logger.warning(f"Insufficient data: {len(df)} candles, need at least {self.required_periods}")
                return df
            
            data = df.copy()
            
            # RSI - Relative Strength Index
            data['rsi'] = ta.rsi(data['close'], length=TradingConfig.RSI_PERIOD)
            
            # MACD - Moving Average Convergence Divergence
            macd_data = ta.macd(
                data['close'],
                fast=TradingConfig.MACD_FAST,
                slow=TradingConfig.MACD_SLOW,
                signal=TradingConfig.MACD_SIGNAL
            )
            data['macd'] = macd_data[f'MACD_{TradingConfig.MACD_FAST}_{TradingConfig.MACD_SLOW}_{TradingConfig.MACD_SIGNAL}']
            data['macd_signal'] = macd_data[f'MACDs_{TradingConfig.MACD_FAST}_{TradingConfig.MACD_SLOW}_{TradingConfig.MACD_SIGNAL}']
            data['macd_hist'] = macd_data[f'MACDh_{TradingConfig.MACD_FAST}_{TradingConfig.MACD_SLOW}_{TradingConfig.MACD_SIGNAL}']
            
            # Simple Moving Averages
            data['sma_fast'] = ta.sma(data['close'], length=TradingConfig.SMA_FAST)
            data['sma_slow'] = ta.sma(data['close'], length=TradingConfig.SMA_SLOW)
            
            # Bollinger Bands
            bb_data = ta.bbands(data['close'], length=20, std=2)
            data['bb_upper'] = bb_data['BBU_20_2.0']
            data['bb_middle'] = bb_data['BBM_20_2.0']
            data['bb_lower'] = bb_data['BBL_20_2.0']
            
            # Average True Range (for volatility and stop loss)
            data['atr'] = ta.atr(data['high'], data['low'], data['close'], length=TradingConfig.ATR_PERIOD)
            
            # Stochastic Oscillator
            stoch_data = ta.stoch(data['high'], data['low'], data['close'])
            data['stoch_k'] = stoch_data['STOCHk_14_3_3']
            data['stoch_d'] = stoch_data['STOCHd_14_3_3']
            
            # Support and Resistance levels
            data = self._calculate_support_resistance(data)
            
            # Trend detection
            data['trend'] = self._detect_trend(data)
            
            return data
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return df
    
    def _calculate_support_resistance(self, df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """Calculate dynamic support and resistance levels"""
        data = df.copy()
        
        # Rolling highs and lows
        data['resistance'] = data['high'].rolling(window=window).max()
        data['support'] = data['low'].rolling(window=window).min()
        
        return data
    
    def _detect_trend(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect trend based on moving averages
        
        Returns:
            Series with trend values: 1 (bullish), -1 (bearish), 0 (sideways)
        """
        conditions = [
            (df['sma_fast'] > df['sma_slow']) & (df['close'] > df['sma_fast']),
            (df['sma_fast'] < df['sma_slow']) & (df['close'] < df['sma_fast'])
        ]
        choices = [1, -1]
        
        return pd.Series(np.select(conditions, choices, default=0), index=df.index)
    
    def detect_candlestick_patterns(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        Detect important candlestick patterns
        
        Returns:
            Dictionary with pattern names and boolean series
        """
        patterns = {}
        
        # Doji
        body_size = abs(df['close'] - df['open'])
        candle_range = df['high'] - df['low']
        patterns['doji'] = body_size <= (candle_range * 0.1)
        
        # Hammer and Hanging Man
        lower_shadow = df[['open', 'close']].min(axis=1) - df['low']
        upper_shadow = df['high'] - df[['open', 'close']].max(axis=1)
        patterns['hammer'] = (lower_shadow >= 2 * body_size) & (upper_shadow <= body_size)
        
        # Engulfing patterns
        prev_body = abs(df['close'].shift(1) - df['open'].shift(1))
        curr_body = abs(df['close'] - df['open'])
        
        bullish_engulfing = (
            (df['close'].shift(1) < df['open'].shift(1)) &  # Previous red candle
            (df['close'] > df['open']) &  # Current green candle
            (df['open'] < df['close'].shift(1)) &  # Current open below previous close
            (df['close'] > df['open'].shift(1)) &  # Current close above previous open
            (curr_body > prev_body)  # Current body larger than previous
        )
        
        bearish_engulfing = (
            (df['close'].shift(1) > df['open'].shift(1)) &  # Previous green candle
            (df['close'] < df['open']) &  # Current red candle
            (df['open'] > df['close'].shift(1)) &  # Current open above previous close
            (df['close'] < df['open'].shift(1)) &  # Current close below previous open
            (curr_body > prev_body)  # Current body larger than previous
        )
        
        patterns['bullish_engulfing'] = bullish_engulfing
        patterns['bearish_engulfing'] = bearish_engulfing
        
        return patterns
    
    def generate_signal(self, df: pd.DataFrame, pair: str, timeframe: str) -> Optional[Dict]:
        """
        Generate trading signal based on technical analysis
        
        Args:
            df: DataFrame with OHLCV data and indicators
            pair: Trading pair symbol
            timeframe: Timeframe code
            
        Returns:
            Signal dictionary or None if no signal
        """
        try:
            if len(df) < self.required_periods:
                return None
            
            # Get latest data point
            latest = df.iloc[-1]
            previous = df.iloc[-2]
            
            # Calculate signal strength and direction
            signal_data = self._evaluate_signal_conditions(latest, previous, df)
            
            if signal_data['direction'] == 'NONE':
                return None
            
            # Calculate entry, stop loss, and take profits
            entry_data = self._calculate_entry_points(latest, signal_data['direction'], pair)
            
            return {
                'pair': pair,
                'timeframe': timeframe,
                'direction': signal_data['direction'],
                'strength': signal_data['strength'],
                'reasons': signal_data['reasons'],
                'entry_price': entry_data['entry'],
                'stop_loss': entry_data['stop_loss'],
                'take_profit_1': entry_data['tp1'],
                'take_profit_2': entry_data['tp2'],
                'take_profit_3': entry_data['tp3'],
                'risk_reward_1': entry_data['rr1'],
                'risk_reward_2': entry_data['rr2'],
                'risk_reward_3': entry_data['rr3'],
                'timestamp': latest.name,
                'current_price': latest['close'],
                'indicators': {
                    'rsi': latest['rsi'],
                    'macd': latest['macd'],
                    'macd_signal': latest['macd_signal'],
                    'macd_hist': latest['macd_hist'],
                    'sma_fast': latest['sma_fast'],
                    'sma_slow': latest['sma_slow'],
                    'atr': latest['atr']
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating signal for {pair} {timeframe}: {e}")
            return None
    
    def _evaluate_signal_conditions(self, current: pd.Series, previous: pd.Series, df: pd.DataFrame) -> Dict:
        """
        Evaluate all signal conditions and calculate strength
        
        Returns:
            Dictionary with direction, strength, and reasons
        """
        bullish_score = 0
        bearish_score = 0
        reasons = []
        
        # RSI conditions
        if current['rsi'] < TradingConfig.RSI_OVERSOLD and current['rsi'] > previous['rsi']:
            bullish_score += 2
            reasons.append("RSI oversold recovery")
        elif current['rsi'] > TradingConfig.RSI_OVERBOUGHT and current['rsi'] < previous['rsi']:
            bearish_score += 2
            reasons.append("RSI overbought decline")
        
        # MACD conditions
        if current['macd_hist'] > 0 and previous['macd_hist'] <= 0:
            bullish_score += 2
            reasons.append("MACD bullish crossover")
        elif current['macd_hist'] < 0 and previous['macd_hist'] >= 0:
            bearish_score += 2
            reasons.append("MACD bearish crossover")
        
        # Moving average conditions
        if (current['close'] > current['sma_fast'] and 
            current['sma_fast'] > current['sma_slow'] and
            previous['sma_fast'] <= previous['sma_slow']):
            bullish_score += 3
            reasons.append("Golden Cross + price above MAs")
        elif (current['close'] < current['sma_fast'] and 
              current['sma_fast'] < current['sma_slow'] and
              previous['sma_fast'] >= previous['sma_slow']):
            bearish_score += 3
            reasons.append("Death Cross + price below MAs")
        
        # Bollinger Bands conditions
        if current['close'] <= current['bb_lower'] and current['close'] > previous['close']:
            bullish_score += 1
            reasons.append("Bounce from lower Bollinger Band")
        elif current['close'] >= current['bb_upper'] and current['close'] < previous['close']:
            bearish_score += 1
            reasons.append("Rejection from upper Bollinger Band")
        
        # Stochastic conditions
        if current['stoch_k'] < 20 and current['stoch_k'] > current['stoch_d']:
            bullish_score += 1
            reasons.append("Stochastic bullish crossover in oversold")
        elif current['stoch_k'] > 80 and current['stoch_k'] < current['stoch_d']:
            bearish_score += 1
            reasons.append("Stochastic bearish crossover in overbought")
        
        # Determine direction and strength
        if bullish_score >= 3 and bullish_score > bearish_score:
            direction = 'BUY'
            strength = min(bullish_score / 8.0, 1.0)  # Normalize to 0-1
        elif bearish_score >= 3 and bearish_score > bullish_score:
            direction = 'SELL'
            strength = min(bearish_score / 8.0, 1.0)  # Normalize to 0-1
        else:
            direction = 'NONE'
            strength = 0.0
        
        return {
            'direction': direction,
            'strength': strength,
            'reasons': reasons
        }
    
    def _calculate_entry_points(self, latest: pd.Series, direction: str, pair: str) -> Dict:
        """
        Calculate entry, stop loss, and take profit levels
        
        Args:
            latest: Latest candle data
            direction: Signal direction ('BUY' or 'SELL')
            pair: Trading pair symbol
            
        Returns:
            Dictionary with entry points and risk-reward ratios
        """
        pair_config = TradingConfig.get_pair_config(pair)
        atr = latest['atr']
        current_price = latest['close']
        
        if direction == 'BUY':
            entry = current_price
            stop_loss = current_price - (atr * TradingConfig.ATR_MULTIPLIER)
            
            # Calculate risk (distance to stop loss)
            risk = entry - stop_loss
            
            # Calculate take profits
            tp1 = entry + (risk * 1.0)  # 1:1 R:R
            tp2 = entry + (risk * 2.0)  # 1:2 R:R
            tp3 = entry + (risk * 3.0)  # 1:3 R:R
            
        else:  # SELL
            entry = current_price
            stop_loss = current_price + (atr * TradingConfig.ATR_MULTIPLIER)
            
            # Calculate risk (distance to stop loss)
            risk = stop_loss - entry
            
            # Calculate take profits
            tp1 = entry - (risk * 1.0)  # 1:1 R:R
            tp2 = entry - (risk * 2.0)  # 1:2 R:R
            tp3 = entry - (risk * 3.0)  # 1:3 R:R
        
        # Round to appropriate decimal places
        pip_position = pair_config.pip_position if pair_config else 4
        
        return {
            'entry': round(entry, pip_position),
            'stop_loss': round(stop_loss, pip_position),
            'tp1': round(tp1, pip_position),
            'tp2': round(tp2, pip_position),
            'tp3': round(tp3, pip_position),
            'rr1': 1.0,
            'rr2': 2.0,
            'rr3': 3.0,
            'risk_pips': round(risk / pair_config.pip_value if pair_config else risk, 1)
        }

# Global instance
technical_analysis = TechnicalAnalysis()
