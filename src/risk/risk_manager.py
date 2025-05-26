
from typing import Dict, Optional
import logging
from src.config.trading_config import TradingConfig

logger = logging.getLogger(__name__)

class RiskManager:
    """Advanced risk management and position sizing calculator"""
    
    def __init__(self):
        self.default_risk_percent = TradingConfig.DEFAULT_RISK_PERCENT
        self.max_risk_percent = TradingConfig.MAX_RISK_PERCENT
    
    def calculate_position_size(
        self,
        account_balance: float,
        risk_percent: float,
        entry_price: float,
        stop_loss: float,
        pair: str
    ) -> Dict:
        """
        Calculate optimal position size based on risk management
        
        Args:
            account_balance: Current account balance in USD
            risk_percent: Percentage of account to risk (1-5%)
            entry_price: Entry price for the trade
            stop_loss: Stop loss price
            pair: Trading pair symbol
            
        Returns:
            Dictionary with position sizing information
        """
        try:
            # Validate inputs
            if risk_percent <= 0 or risk_percent > self.max_risk_percent:
                risk_percent = self.default_risk_percent
                logger.warning(f"Invalid risk percent, using default: {self.default_risk_percent}%")
            
            if account_balance <= 0:
                raise ValueError("Account balance must be positive")
            
            # Get pair configuration
            pair_config = TradingConfig.get_pair_config(pair)
            if not pair_config:
                raise ValueError(f"Unsupported trading pair: {pair}")
            
            # Calculate risk amount in USD
            risk_amount = account_balance * (risk_percent / 100)
            
            # Calculate distance to stop loss in pips
            price_distance = abs(entry_price - stop_loss)
            pips_distance = price_distance / pair_config.pip_value
            
            # Calculate position size
            if pair_config.category == 'forex':
                # For forex pairs, calculate lot size
                pip_value_per_lot = self._get_pip_value_per_lot(pair, account_balance)
                lot_size = risk_amount / (pips_distance * pip_value_per_lot)
                
                # Round to appropriate lot size
                lot_size = self._round_lot_size(lot_size)
                
                return {
                    'pair': pair,
                    'account_balance': account_balance,
                    'risk_percent': risk_percent,
                    'risk_amount': round(risk_amount, 2),
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'pips_distance': round(pips_distance, 1),
                    'lot_size': lot_size,
                    'units': int(lot_size * 100000),  # Convert lots to units
                    'pip_value': round(pip_value_per_lot, 2),
                    'max_loss': round(lot_size * pips_distance * pip_value_per_lot, 2),
                    'position_value': round(lot_size * 100000 * entry_price, 2),
                    'category': pair_config.category
                }
                
            elif pair_config.category == 'commodity':
                # For gold (XAU/USD)
                units = risk_amount / price_distance
                units = round(units, 0)  # Round to whole units
                
                return {
                    'pair': pair,
                    'account_balance': account_balance,
                    'risk_percent': risk_percent,
                    'risk_amount': round(risk_amount, 2),
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'price_distance': round(price_distance, 2),
                    'units': int(units),
                    'max_loss': round(units * price_distance, 2),
                    'position_value': round(units * entry_price, 2),
                    'category': pair_config.category
                }
                
            elif pair_config.category == 'crypto':
                # For cryptocurrency
                units = risk_amount / price_distance
                units = round(units, 6)  # Crypto can have fractional units
                
                return {
                    'pair': pair,
                    'account_balance': account_balance,
                    'risk_percent': risk_percent,
                    'risk_amount': round(risk_amount, 2),
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'price_distance': round(price_distance, 2),
                    'units': units,
                    'max_loss': round(units * price_distance, 2),
                    'position_value': round(units * entry_price, 2),
                    'category': pair_config.category
                }
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return {
                'error': str(e),
                'pair': pair,
                'account_balance': account_balance,
                'risk_percent': risk_percent
            }
    
    def _get_pip_value_per_lot(self, pair: str, account_balance: float) -> float:
        """
        Calculate pip value per standard lot for forex pairs
        
        For most major pairs against USD, 1 pip = $10 per standard lot
        For JPY pairs, 1 pip = $10 per standard lot (adjusted for pip size)
        """
        pair_config = TradingConfig.get_pair_config(pair)
        
        if 'JPY' in pair:
            # JPY pairs have different pip calculation
            return 10.0  # $10 per lot for 0.01 movement
        else:
            # Most major pairs
            return 10.0  # $10 per lot for 0.0001 movement
    
    def _round_lot_size(self, lot_size: float) -> float:
        """Round lot size to appropriate increment"""
        if lot_size >= 1.0:
            return round(lot_size, 2)
        elif lot_size >= 0.1:
            return round(lot_size, 3)
        else:
            return round(lot_size, 4)
    
    def calculate_multiple_risk_scenarios(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss: float,
        pair: str
    ) -> Dict:
        """
        Calculate position sizes for multiple risk scenarios
        
        Returns:
            Dictionary with calculations for 1%, 2%, 3% risk
        """
        scenarios = {}
        risk_levels = [1.0, 2.0, 3.0]
        
        for risk in risk_levels:
            scenarios[f'{risk}%'] = self.calculate_position_size(
                account_balance, risk, entry_price, stop_loss, pair
            )
        
        return scenarios
    
    def validate_trade_parameters(
        self,
        entry_price: float,
        stop_loss: float,
        take_profits: list,
        pair: str
    ) -> Dict:
        """
        Validate trade parameters for consistency
        
        Returns:
            Dictionary with validation results
        """
        issues = []
        warnings = []
        
        pair_config = TradingConfig.get_pair_config(pair)
        if not pair_config:
            issues.append(f"Unsupported trading pair: {pair}")
            return {'valid': False, 'issues': issues, 'warnings': warnings}
        
        # Check if stop loss is in correct direction
        if entry_price == stop_loss:
            issues.append("Entry price and stop loss cannot be the same")
        
        # Check take profit levels
        for i, tp in enumerate(take_profits, 1):
            if entry_price > stop_loss:  # Long trade
                if tp <= entry_price:
                    issues.append(f"Take profit {i} must be above entry price for long trades")
            else:  # Short trade
                if tp >= entry_price:
                    issues.append(f"Take profit {i} must be below entry price for short trades")
        
        # Check risk-reward ratios
        risk = abs(entry_price - stop_loss)
        for i, tp in enumerate(take_profits, 1):
            reward = abs(tp - entry_price)
            rr_ratio = reward / risk if risk > 0 else 0
            
            if rr_ratio < 0.5:
                warnings.append(f"Take profit {i} has poor risk-reward ratio: 1:{rr_ratio:.1f}")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings
        }

# Global instance
risk_manager = RiskManager()
