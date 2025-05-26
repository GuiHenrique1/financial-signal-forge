
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
import pytz
from src.config.trading_config import TradingConfig

logger = logging.getLogger(__name__)

class SessionVolatilityFilter:
    """Filter signals based on trading sessions, volatility, and market conditions"""
    
    def __init__(self):
        self.session_timezones = {
            'tokyo': pytz.timezone('Asia/Tokyo'),
            'london': pytz.timezone('Europe/London'),
            'newyork': pytz.timezone('America/New_York'),
            'sydney': pytz.timezone('Australia/Sydney')
        }
    
    def is_session_active(self, pair: str, current_time: datetime = None) -> Tuple[bool, str]:
        """
        Check if current time is within active trading session for the pair
        
        Args:
            pair: Trading pair symbol
            current_time: Current datetime (UTC), defaults to now
            
        Returns:
            Tuple of (is_active, active_session_name)
        """
        if not TradingConfig.SESSION_FILTERING_ENABLED:
            return True, 'all'
        
        if current_time is None:
            current_time = datetime.utcnow()
        
        pair_config = TradingConfig.get_pair_config(pair)
        if not pair_config:
            return False, 'none'
        
        # If pair prefers all sessions, check if any session is active
        if pair_config.session_preference == 'all':
            for session_name in TradingConfig.ACTIVE_SESSIONS:
                if self._is_specific_session_active(session_name, current_time):
                    return True, session_name
            return False, 'none'
        
        # Check specific session preference
        if pair_config.session_preference in TradingConfig.ACTIVE_SESSIONS:
            is_active = self._is_specific_session_active(
                pair_config.session_preference, current_time
            )
            return is_active, pair_config.session_preference if is_active else 'none'
        
        return False, 'none'
    
    def _is_specific_session_active(self, session_name: str, current_time: datetime) -> bool:
        """Check if a specific session is currently active"""
        session_config = TradingConfig.get_session_config(session_name)
        if not session_config or not session_config.active:
            return False
        
        # Convert UTC time to session timezone
        session_tz = self.session_timezones.get(session_name)
        if not session_tz:
            return False
        
        utc_time = current_time.replace(tzinfo=pytz.UTC)
        session_time = utc_time.astimezone(session_tz)
        current_hour = session_time.hour
        
        start_hour = session_config.start_hour
        end_hour = session_config.end_hour
        
        # Handle sessions that cross midnight
        if start_hour <= end_hour:
            return start_hour <= current_hour < end_hour
        else:
            return current_hour >= start_hour or current_hour < end_hour
    
    def check_volatility_conditions(self, df: pd.DataFrame, pair: str) -> Dict:
        """
        Check volatility conditions for signal generation
        
        Args:
            df: OHLCV DataFrame with indicators
            pair: Trading pair symbol
            
        Returns:
            Dictionary with volatility analysis results
        """
        if len(df) < 20:
            return {
                'sufficient_volatility': False,
                'atr_value': 0,
                'atr_threshold': 0,
                'volatility_percentile': 0,
                'reason': 'Insufficient data for volatility analysis'
            }
        
        latest = df.iloc[-1]
        atr_current = latest.get('atr', 0)
        
        # Calculate ATR percentiles over last 100 periods
        atr_series = df['atr'].dropna().tail(100)
        atr_percentile = (atr_series <= atr_current).mean() * 100
        
        # Get pair-specific ATR threshold
        pair_config = TradingConfig.get_pair_config(pair)
        if pair_config:
            # Use minimum spread as base threshold, scaled by ATR multiplier
            base_threshold = pair_config.min_spread * TradingConfig.ATR_MULTIPLIER
            atr_threshold = max(base_threshold, TradingConfig.ATR_MIN_THRESHOLD)
        else:
            atr_threshold = TradingConfig.ATR_MIN_THRESHOLD
        
        # Check conditions
        sufficient_volatility = (
            atr_current >= atr_threshold and 
            atr_percentile >= 20  # At least 20th percentile
        )
        
        reason = ""
        if atr_current < atr_threshold:
            reason = f"ATR too low: {atr_current:.5f} < {atr_threshold:.5f}"
        elif atr_percentile < 20:
            reason = f"ATR percentile too low: {atr_percentile:.1f}% < 20%"
        else:
            reason = f"Sufficient volatility: ATR {atr_current:.5f} ({atr_percentile:.1f}th percentile)"
        
        return {
            'sufficient_volatility': sufficient_volatility,
            'atr_value': atr_current,
            'atr_threshold': atr_threshold,
            'atr_percentile': atr_percentile,
            'reason': reason
        }
    
    def check_spread_conditions(self, current_price_data: Dict, pair: str) -> Dict:
        """
        Check if spread conditions are acceptable for trading
        
        Args:
            current_price_data: Dictionary with bid, ask, spread information
            pair: Trading pair symbol
            
        Returns:
            Dictionary with spread analysis results
        """
        if not current_price_data:
            return {
                'acceptable_spread': False,
                'current_spread': 0,
                'max_spread': 0,
                'spread_ratio': 0,
                'reason': 'No current price data available'
            }
        
        current_spread = current_price_data.get('spread', 0)
        pair_config = TradingConfig.get_pair_config(pair)
        
        if not pair_config:
            return {
                'acceptable_spread': False,
                'current_spread': current_spread,
                'max_spread': 0,
                'spread_ratio': 0,
                'reason': 'Unknown pair configuration'
            }
        
        # Maximum acceptable spread (3x normal spread)
        max_spread = pair_config.min_spread * 3
        spread_ratio = current_spread / pair_config.min_spread if pair_config.min_spread > 0 else 0
        
        acceptable_spread = current_spread <= max_spread
        
        reason = (
            f"Spread acceptable: {current_spread:.5f} <= {max_spread:.5f}"
            if acceptable_spread
            else f"Spread too wide: {current_spread:.5f} > {max_spread:.5f}"
        )
        
        return {
            'acceptable_spread': acceptable_spread,
            'current_spread': current_spread,
            'max_spread': max_spread,
            'spread_ratio': spread_ratio,
            'reason': reason
        }
    
    def is_major_news_time(self, current_time: datetime = None) -> Dict:
        """
        Check if current time is during major news events
        
        Args:
            current_time: Current datetime (UTC), defaults to now
            
        Returns:
            Dictionary with news time analysis
        """
        if not TradingConfig.ECONOMIC_CALENDAR_ENABLED:
            return {
                'is_news_time': False,
                'reason': 'Economic calendar not enabled'
            }
        
        if current_time is None:
            current_time = datetime.utcnow()
        
        # Check for common high-impact news times (simplified)
        # This would typically integrate with an economic calendar API
        
        # NFP (first Friday of month at 8:30 EST)
        # FOMC meetings
        # ECB meetings
        # BOJ meetings
        # GDP releases
        
        # For now, implement basic time-based filtering
        # Avoid trading 30 minutes before and after major session opens
        utc_hour = current_time.hour
        utc_minute = current_time.minute
        
        # London open: 8:00 UTC
        if (utc_hour == 7 and utc_minute >= 30) or (utc_hour == 8 and utc_minute <= 30):
            return {
                'is_news_time': True,
                'reason': 'London session opening volatility'
            }
        
        # New York open: 13:00 UTC
        if (utc_hour == 12 and utc_minute >= 30) or (utc_hour == 13 and utc_minute <= 30):
            return {
                'is_news_time': True,
                'reason': 'New York session opening volatility'
            }
        
        # Check if it's Friday during NFP time (usually 13:30 UTC)
        if (current_time.weekday() == 4 and  # Friday
            utc_hour == 13 and 30 <= utc_minute <= 45):
            return {
                'is_news_time': True,
                'reason': 'Potential NFP release time'
            }
        
        return {
            'is_news_time': False,
            'reason': 'No major news events detected'
        }
    
    def filter_signals(
        self, 
        signals: Dict[str, Dict[str, Dict]], 
        market_data: Dict[str, Dict[str, pd.DataFrame]],
        current_prices: Dict[str, Dict] = None
    ) -> Dict[str, Dict[str, Dict]]:
        """
        Apply all filters to signals
        
        Args:
            signals: Generated signals {pair: {timeframe: signal_data}}
            market_data: Market data {pair: {timeframe: DataFrame}}
            current_prices: Current price data {pair: price_info}
            
        Returns:
            Filtered signals
        """
        filtered_signals = {}
        current_time = datetime.utcnow()
        
        # Check for major news time
        news_check = self.is_major_news_time(current_time)
        if news_check['is_news_time']:
            logger.warning(f"Major news time detected: {news_check['reason']} - No signals will be generated")
            return {}
        
        for pair, timeframe_signals in signals.items():
            # Check session activity
            session_active, active_session = self.is_session_active(pair, current_time)
            if not session_active:
                logger.info(f"Skipping {pair} - session not active")
                continue
            
            filtered_pair_signals = {}
            
            for timeframe, signal_data in timeframe_signals.items():
                # Get market data for this pair and timeframe
                pair_data = market_data.get(pair, {})
                df = pair_data.get(timeframe)
                
                if df is None or len(df) == 0:
                    continue
                
                # Check volatility conditions
                volatility_check = self.check_volatility_conditions(df, pair)
                if not volatility_check['sufficient_volatility']:
                    logger.info(
                        f"Skipping {pair} {timeframe} signal - {volatility_check['reason']}"
                    )
                    continue
                
                # Check spread conditions if current prices available
                if current_prices and pair in current_prices:
                    spread_check = self.check_spread_conditions(current_prices[pair], pair)
                    if not spread_check['acceptable_spread']:
                        logger.info(
                            f"Skipping {pair} {timeframe} signal - {spread_check['reason']}"
                        )
                        continue
                    
                    # Add spread info to signal
                    signal_data['spread_info'] = spread_check
                
                # Add session and volatility info to signal
                signal_data['session_info'] = {
                    'active_session': active_session,
                    'session_active': session_active
                }
                signal_data['volatility_info'] = volatility_check
                
                filtered_pair_signals[timeframe] = signal_data
                logger.info(
                    f"Signal passed filters: {pair} {timeframe} {signal_data['direction']} "
                    f"(Session: {active_session}, ATR: {volatility_check['atr_percentile']:.1f}%)"
                )
            
            if filtered_pair_signals:
                filtered_signals[pair] = filtered_pair_signals
        
        return filtered_signals

# Global instance
session_volatility_filter = SessionVolatilityFilter()
