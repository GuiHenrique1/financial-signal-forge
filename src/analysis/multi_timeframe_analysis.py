
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
from src.config.trading_config import TradingConfig
from src.analysis.technical_analysis import technical_analysis

logger = logging.getLogger(__name__)

class MultiTimeframeAnalysis:
    """Enhanced multi-timeframe analysis with confirmation logic"""
    
    def __init__(self):
        self.timeframe_hierarchy = ['M15', 'M30', 'H1', 'H4', 'D1', 'W1']
        self.confirmation_rules = {
            'M15': ['M30', 'H1'],
            'M30': ['H1', 'H4'],
            'H1': ['H4', 'D1'],
            'H4': ['D1', 'W1'],
            'D1': ['W1'],
            'W1': []
        }
    
    def analyze_multiple_timeframes(
        self, 
        pair_data: Dict[str, pd.DataFrame], 
        pair: str
    ) -> Dict[str, Dict]:
        """
        Analyze multiple timeframes for a single pair
        
        Args:
            pair_data: Dictionary with timeframe as key and DataFrame as value
            pair: Trading pair symbol
            
        Returns:
            Dictionary with analysis results for each timeframe
        """
        results = {}
        
        for timeframe, df in pair_data.items():
            if df is not None and len(df) > 0:
                # Calculate indicators for this timeframe
                df_with_indicators = technical_analysis.calculate_indicators(df)
                
                # Generate signal for this timeframe
                signal_data = technical_analysis.generate_signal(
                    df_with_indicators, pair, timeframe
                )
                
                if signal_data:
                    # Add multi-timeframe confirmation
                    confirmation_data = self._get_timeframe_confirmation(
                        signal_data, pair_data, timeframe, signal_data['direction']
                    )
                    
                    signal_data.update(confirmation_data)
                    results[timeframe] = signal_data
        
        return results
    
    def _get_timeframe_confirmation(
        self,
        signal_data: Dict,
        pair_data: Dict[str, pd.DataFrame],
        current_timeframe: str,
        signal_direction: str
    ) -> Dict:
        """
        Get confirmation from higher timeframes
        
        Args:
            signal_data: Current signal data
            pair_data: All timeframe data for the pair
            current_timeframe: Current timeframe being analyzed
            signal_direction: Direction of the signal (BUY/SELL)
            
        Returns:
            Dictionary with confirmation data
        """
        confirmation_score = 0.0
        confirmation_details = []
        higher_timeframes = self.confirmation_rules.get(current_timeframe, [])
        
        for higher_tf in higher_timeframes:
            if higher_tf in pair_data and pair_data[higher_tf] is not None:
                df_higher = technical_analysis.calculate_indicators(pair_data[higher_tf])
                
                if len(df_higher) > 0:
                    latest = df_higher.iloc[-1]
                    
                    # Check trend confirmation
                    trend_confirmation = self._check_trend_confirmation(
                        latest, signal_direction
                    )
                    
                    if trend_confirmation['confirmed']:
                        weight = TradingConfig.TIMEFRAMES[higher_tf].confirmation_weight
                        confirmation_score += weight
                        confirmation_details.append(
                            f"{higher_tf}: {trend_confirmation['reason']}"
                        )
        
        # Calculate final confirmation percentage
        max_possible_score = sum(
            TradingConfig.TIMEFRAMES[tf].confirmation_weight 
            for tf in higher_timeframes 
            if tf in pair_data and pair_data[tf] is not None
        )
        
        confirmation_percentage = (
            (confirmation_score / max_possible_score * 100) 
            if max_possible_score > 0 else 0
        )
        
        return {
            'mtf_confirmation_score': confirmation_score,
            'mtf_confirmation_percentage': confirmation_percentage,
            'mtf_confirmation_details': confirmation_details,
            'mtf_confirmed': confirmation_percentage >= 60  # 60% threshold
        }
    
    def _check_trend_confirmation(self, latest_data: pd.Series, signal_direction: str) -> Dict:
        """
        Check if higher timeframe confirms the signal direction
        
        Args:
            latest_data: Latest candle data from higher timeframe
            signal_direction: Signal direction to confirm
            
        Returns:
            Dictionary with confirmation result and reason
        """
        price = latest_data['close']
        sma_fast = latest_data.get('sma_fast')
        sma_slow = latest_data.get('sma_slow')
        macd_hist = latest_data.get('macd_hist')
        
        if signal_direction == 'BUY':
            # For BUY signals, check bullish conditions on higher timeframe
            if (price > sma_fast > sma_slow and macd_hist > 0):
                return {
                    'confirmed': True,
                    'reason': 'Strong bullish trend (price > fast MA > slow MA, MACD positive)'
                }
            elif price > sma_slow:
                return {
                    'confirmed': True,
                    'reason': 'Bullish bias (price above long-term MA)'
                }
            else:
                return {
                    'confirmed': False,
                    'reason': 'Bearish or sideways trend'
                }
        
        elif signal_direction == 'SELL':
            # For SELL signals, check bearish conditions on higher timeframe
            if (price < sma_fast < sma_slow and macd_hist < 0):
                return {
                    'confirmed': True,
                    'reason': 'Strong bearish trend (price < fast MA < slow MA, MACD negative)'
                }
            elif price < sma_slow:
                return {
                    'confirmed': True,
                    'reason': 'Bearish bias (price below long-term MA)'
                }
            else:
                return {
                    'confirmed': False,
                    'reason': 'Bullish or sideways trend'
                }
        
        return {'confirmed': False, 'reason': 'Invalid signal direction'}
    
    def filter_signals_by_confirmation(
        self, 
        all_signals: Dict[str, Dict[str, Dict]]
    ) -> Dict[str, Dict[str, Dict]]:
        """
        Filter signals based on multi-timeframe confirmation
        
        Args:
            all_signals: All generated signals {pair: {timeframe: signal_data}}
            
        Returns:
            Filtered signals that meet confirmation criteria
        """
        filtered_signals = {}
        
        for pair, timeframe_signals in all_signals.items():
            filtered_pair_signals = {}
            
            for timeframe, signal_data in timeframe_signals.items():
                if TradingConfig.MTF_CONFIRMATION_ENABLED:
                    # Only include signals with sufficient confirmation
                    if signal_data.get('mtf_confirmed', False):
                        filtered_pair_signals[timeframe] = signal_data
                        logger.info(
                            f"Signal confirmed: {pair} {timeframe} {signal_data['direction']} "
                            f"(MTF: {signal_data['mtf_confirmation_percentage']:.1f}%)"
                        )
                else:
                    # Include all signals if MTF confirmation is disabled
                    filtered_pair_signals[timeframe] = signal_data
            
            if filtered_pair_signals:
                filtered_signals[pair] = filtered_pair_signals
        
        return filtered_signals
    
    def get_best_signals(
        self, 
        all_signals: Dict[str, Dict[str, Dict]], 
        max_signals: int = 10
    ) -> List[Dict]:
        """
        Get the best signals across all pairs and timeframes
        
        Args:
            all_signals: All generated signals
            max_signals: Maximum number of signals to return
            
        Returns:
            List of best signals sorted by quality score
        """
        signal_list = []
        
        for pair, timeframe_signals in all_signals.items():
            for timeframe, signal_data in timeframe_signals.items():
                # Calculate quality score
                quality_score = self._calculate_signal_quality_score(signal_data)
                signal_data['quality_score'] = quality_score
                signal_data['pair'] = pair
                signal_data['timeframe'] = timeframe
                signal_list.append(signal_data)
        
        # Sort by quality score and return top signals
        signal_list.sort(key=lambda x: x['quality_score'], reverse=True)
        return signal_list[:max_signals]
    
    def _calculate_signal_quality_score(self, signal_data: Dict) -> float:
        """
        Calculate a quality score for a signal based on multiple factors
        
        Args:
            signal_data: Signal data dictionary
            
        Returns:
            Quality score (0-100)
        """
        score = 0.0
        
        # Base signal strength (30% weight)
        score += signal_data.get('strength', 0) * 30
        
        # Multi-timeframe confirmation (40% weight)
        mtf_percentage = signal_data.get('mtf_confirmation_percentage', 0)
        score += (mtf_percentage / 100) * 40
        
        # Risk-reward ratio (20% weight)
        rr_score = min(signal_data.get('risk_reward_3', 0) / 3.0, 1.0) * 20
        score += rr_score
        
        # Timeframe weight (10% weight)
        timeframe = signal_data.get('timeframe', 'H1')
        tf_config = TradingConfig.get_timeframe_config(timeframe)
        if tf_config:
            tf_weight = min(tf_config.confirmation_weight / 3.0, 1.0) * 10
            score += tf_weight
        
        return min(score, 100.0)

# Global instance
multi_timeframe_analysis = MultiTimeframeAnalysis()
