
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import json
from src.data.market_data_fetcher import market_data_fetcher
from src.analysis.technical_analysis import technical_analysis
from src.risk.risk_manager import risk_manager
from src.config.trading_config import TradingConfig

logger = logging.getLogger(__name__)

@dataclass
class TradingSignal:
    """Data class for trading signals"""
    id: str
    pair: str
    timeframe: str
    direction: str
    strength: float
    reasons: List[str]
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    risk_reward_1: float
    risk_reward_2: float
    risk_reward_3: float
    timestamp: datetime
    current_price: float
    indicators: Dict
    status: str = 'ACTIVE'
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp.replace('Z', '+00:00'))

class SignalManager:
    """Manages signal generation, storage, and distribution"""
    
    def __init__(self):
        self.active_signals: Dict[str, TradingSignal] = {}
        self.signal_history: List[TradingSignal] = []
        self.last_signal_time: Dict[str, datetime] = {}
        self.min_signal_interval = timedelta(minutes=15)  # Minimum time between signals for same pair-timeframe
    
    async def generate_all_signals(self) -> Dict[str, List[TradingSignal]]:
        """
        Generate signals for all configured pairs and timeframes
        
        Returns:
            Dictionary with structure: {pair: [signals]}
        """
        try:
            # Fetch data for all pairs and timeframes
            all_data = await market_data_fetcher.fetch_all_pairs_data()
            
            all_signals = {}
            new_signals = []
            
            # Generate signals for each pair and timeframe
            for pair_symbol, timeframe_data in all_data.items():
                pair_signals = []
                
                for timeframe, df in timeframe_data.items():
                    if df is not None and len(df) > 0:
                        # Add technical indicators
                        df_with_indicators = technical_analysis.calculate_indicators(df)
                        
                        # Generate signal
                        signal_data = technical_analysis.generate_signal(
                            df_with_indicators, pair_symbol, timeframe
                        )
                        
                        if signal_data:
                            # Check if this is a new signal
                            signal_key = f"{pair_symbol}_{timeframe}"
                            
                            if self._is_new_signal(signal_key, signal_data):
                                # Create TradingSignal object
                                signal = TradingSignal(
                                    id=f"{pair_symbol}_{timeframe}_{int(datetime.now().timestamp())}",
                                    **signal_data
                                )
                                
                                pair_signals.append(signal)
                                new_signals.append(signal)
                                
                                # Update tracking
                                self.active_signals[signal_key] = signal
                                self.last_signal_time[signal_key] = datetime.now()
                                
                                logger.info(f"New signal generated: {signal.pair} {signal.timeframe} {signal.direction}")
                
                if pair_signals:
                    all_signals[pair_symbol] = pair_signals
            
            # Add new signals to history
            self.signal_history.extend(new_signals)
            
            # Clean up old signals
            self._cleanup_old_signals()
            
            return all_signals
            
        except Exception as e:
            logger.error(f"Error generating signals: {e}")
            return {}
    
    def _is_new_signal(self, signal_key: str, signal_data: Dict) -> bool:
        """
        Check if this is a new signal that should be sent
        
        Args:
            signal_key: Unique key for pair-timeframe combination
            signal_data: Signal data dictionary
            
        Returns:
            True if this is a new signal
        """
        # Check if enough time has passed since last signal
        last_time = self.last_signal_time.get(signal_key)
        if last_time and datetime.now() - last_time < self.min_signal_interval:
            return False
        
        # Check if we have an active signal for this pair-timeframe
        active_signal = self.active_signals.get(signal_key)
        if active_signal:
            # Check if direction changed
            if active_signal.direction != signal_data['direction']:
                return True
            
            # Check if signal strength significantly improved
            strength_improvement = signal_data['strength'] - active_signal.strength
            if strength_improvement > 0.2:  # 20% improvement
                return True
            
            return False
        
        return True
    
    def get_active_signals(self) -> List[TradingSignal]:
        """Get all active signals"""
        return list(self.active_signals.values())
    
    def get_signals_by_pair(self, pair: str) -> List[TradingSignal]:
        """Get active signals for a specific pair"""
        return [signal for signal in self.active_signals.values() if signal.pair == pair]
    
    def get_signals_by_timeframe(self, timeframe: str) -> List[TradingSignal]:
        """Get active signals for a specific timeframe"""
        return [signal for signal in self.active_signals.values() if signal.timeframe == timeframe]
    
    def get_signal_history(self, limit: int = 50) -> List[TradingSignal]:
        """Get recent signal history"""
        return sorted(self.signal_history, key=lambda x: x.created_at, reverse=True)[:limit]
    
    def get_best_signals(self, min_strength: float = 0.6) -> List[TradingSignal]:
        """Get signals with strength above threshold"""
        return [
            signal for signal in self.active_signals.values()
            if signal.strength >= min_strength
        ]
    
    def calculate_position_sizing(
        self,
        signal: TradingSignal,
        account_balance: float,
        risk_percent: float = None
    ) -> Dict:
        """
        Calculate position sizing for a signal
        
        Args:
            signal: TradingSignal object
            account_balance: Account balance in USD
            risk_percent: Risk percentage (default from config)
            
        Returns:
            Position sizing information
        """
        if risk_percent is None:
            risk_percent = TradingConfig.DEFAULT_RISK_PERCENT
        
        return risk_manager.calculate_position_size(
            account_balance=account_balance,
            risk_percent=risk_percent,
            entry_price=signal.entry_price,
            stop_loss=signal.stop_loss,
            pair=signal.pair
        )
    
    def format_signal_for_telegram(self, signal: TradingSignal, account_balance: float = None) -> str:
        """
        Format signal for Telegram message
        
        Args:
            signal: TradingSignal object
            account_balance: Optional account balance for position sizing
            
        Returns:
            Formatted message string
        """
        direction_emoji = "🟢" if signal.direction == "BUY" else "🔴"
        
        message = f"""
{direction_emoji} **{signal.pair.replace('_', '/')} — {signal.direction}**

🕐 **Timeframe:** {signal.timeframe}
📊 **Força:** {signal.strength:.1%}
⭐ **Entry:** {signal.entry_price}
🛑 **Stop Loss:** {signal.stop_loss}

**Take Profits:**
🎯 **TP1:** {signal.take_profit_1} (R:R 1:{signal.risk_reward_1})
🎯 **TP2:** {signal.take_profit_2} (R:R 1:{signal.risk_reward_2})
🎯 **TP3:** {signal.take_profit_3} (R:R 1:{signal.risk_reward_3})

**Indicadores:**
• RSI: {signal.indicators.get('rsi', 0):.1f}
• MACD: {signal.indicators.get('macd', 0):.6f}

**Razão:** {'; '.join(signal.reasons)}
        """
        
        # Add position sizing if account balance provided
        if account_balance:
            position_data = self.calculate_position_sizing(signal, account_balance)
            if 'error' not in position_data:
                message += f"""
**Position Sizing (1% risk):**
💰 **Lote:** {position_data.get('lot_size', position_data.get('units', 'N/A'))}
📉 **Risco Máximo:** ${position_data.get('max_loss', 0):.2f}
                """
        
        message += f"""
⏰ **Gerado:** {signal.timestamp.strftime('%d/%m %H:%M')}

⚠️ *Analise antes de operar - Risco próprio*
        """
        
        return message.strip()
    
    def _cleanup_old_signals(self):
        """Remove old signals from active list"""
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        # Remove old active signals
        keys_to_remove = []
        for key, signal in self.active_signals.items():
            if signal.created_at < cutoff_time:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.active_signals[key]
        
        # Keep only last 1000 signals in history
        if len(self.signal_history) > 1000:
            self.signal_history = self.signal_history[-1000:]
    
    def export_signals_json(self) -> str:
        """Export signals to JSON format"""
        data = {
            'active_signals': [asdict(signal) for signal in self.active_signals.values()],
            'signal_history': [asdict(signal) for signal in self.get_signal_history()],
            'export_time': datetime.now().isoformat()
        }
        
        # Convert datetime objects to strings
        def convert_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj
        
        return json.dumps(data, default=convert_datetime, indent=2)

# Global instance
signal_manager = SignalManager()
