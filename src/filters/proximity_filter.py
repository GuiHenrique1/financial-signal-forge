
import pandas as pd
import logging
from typing import Dict, Optional
from src.config.trading_config import TradingConfig

logger = logging.getLogger(__name__)

class ProximityFilter:
    """Filter signals based on proximity to current market price"""
    
    def __init__(self, max_pips_distance: float = 10.0):
        self.max_pips_distance = max_pips_distance
    
    def get_pip_value(self, pair: str) -> float:
        """Get pip value for a trading pair"""
        pair_config = TradingConfig.get_pair_config(pair)
        return pair_config.pip_value if pair_config else 0.0001
    
    def calculate_distance_in_pips(self, entry_price: float, current_price: float, pair: str) -> float:
        """Calculate distance between entry and current price in pips"""
        pip_value = self.get_pip_value(pair)
        distance = abs(entry_price - current_price) / pip_value
        return distance
    
    def filter_signals_by_proximity(
        self, 
        signals_df: pd.DataFrame, 
        current_prices: Dict[str, float], 
        threshold_pips: Optional[float] = None
    ) -> pd.DataFrame:
        """
        Filter signals that are within threshold distance from current price
        
        Args:
            signals_df: DataFrame with trading signals
            current_prices: Dictionary with current prices {pair: price}
            threshold_pips: Maximum distance in pips (uses default if None)
            
        Returns:
            Filtered DataFrame with only relevant signals
        """
        if signals_df.empty:
            return signals_df
        
        threshold = threshold_pips or self.max_pips_distance
        filtered_signals = []
        
        for idx, signal in signals_df.iterrows():
            pair = signal.get('pair', '')
            entry_price = signal.get('entry_price', 0)
            current_price = current_prices.get(pair, 0)
            
            if current_price == 0:
                logger.warning(f"No current price available for {pair}")
                continue
            
            # Calculate distance in pips
            distance_pips = self.calculate_distance_in_pips(entry_price, current_price, pair)
            
            # Keep signal if within threshold
            if distance_pips <= threshold:
                # Add proximity info to signal
                signal_dict = signal.to_dict()
                signal_dict['distance_pips'] = round(distance_pips, 1)
                signal_dict['current_price'] = current_price
                signal_dict['proximity_score'] = max(0, (threshold - distance_pips) / threshold)
                filtered_signals.append(signal_dict)
                
                logger.info(f"Signal kept: {pair} - Distance: {distance_pips:.1f} pips")
            else:
                logger.debug(f"Signal filtered out: {pair} - Distance: {distance_pips:.1f} pips (threshold: {threshold})")
        
        if filtered_signals:
            return pd.DataFrame(filtered_signals)
        else:
            return pd.DataFrame()
    
    def rank_signals_by_proximity(self, signals_df: pd.DataFrame) -> pd.DataFrame:
        """Rank signals by proximity score (closer = better)"""
        if signals_df.empty or 'proximity_score' not in signals_df.columns:
            return signals_df
        
        return signals_df.sort_values('proximity_score', ascending=False)

# Global instance
proximity_filter = ProximityFilter()
