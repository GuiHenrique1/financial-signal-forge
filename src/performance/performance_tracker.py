
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
import json
from dataclasses import dataclass, asdict
from src.config.trading_config import TradingConfig

logger = logging.getLogger(__name__)

@dataclass
class TradeResult:
    """Data class for individual trade results"""
    signal_id: str
    pair: str
    timeframe: str
    direction: str
    entry_price: float
    exit_price: float
    exit_type: str  # 'tp1', 'tp2', 'tp3', 'sl', 'manual'
    pips_result: float
    dollar_result: float
    risk_reward_ratio: float
    entry_time: datetime
    exit_time: datetime
    duration_minutes: int
    lot_size: float
    signal_strength: float
    mtf_confirmation: bool
    session: str
    volatility_percentile: float

@dataclass
class PerformanceMetrics:
    """Data class for performance metrics"""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pips: float
    total_profit: float
    average_win: float
    average_loss: float
    largest_win: float
    largest_loss: float
    profit_factor: float
    risk_reward_ratio: float
    max_drawdown: float
    max_drawdown_percent: float
    sharpe_ratio: float
    calmar_ratio: float
    recovery_factor: float
    expectancy: float

class PerformanceTracker:
    """Track and analyze trading performance"""
    
    def __init__(self):
        self.trades: List[TradeResult] = []
        self.equity_curve: List[Dict] = []
        self.daily_results: Dict[str, float] = {}
        self.pair_performance: Dict[str, PerformanceMetrics] = {}
        self.timeframe_performance: Dict[str, PerformanceMetrics] = {}
        
    def add_trade_result(self, trade_result: TradeResult):
        """Add a completed trade result"""
        self.trades.append(trade_result)
        
        # Update equity curve
        current_equity = (
            self.equity_curve[-1]['equity'] + trade_result.dollar_result
            if self.equity_curve
            else 10000 + trade_result.dollar_result  # Start with $10,000
        )
        
        self.equity_curve.append({
            'timestamp': trade_result.exit_time,
            'equity': current_equity,
            'trade_result': trade_result.dollar_result,
            'cumulative_pips': sum(t.pips_result for t in self.trades)
        })
        
        # Update daily results
        date_str = trade_result.exit_time.strftime('%Y-%m-%d')
        if date_str not in self.daily_results:
            self.daily_results[date_str] = 0
        self.daily_results[date_str] += trade_result.dollar_result
        
        # Update performance metrics
        self._update_performance_metrics()
        
        logger.info(
            f"Trade completed: {trade_result.pair} {trade_result.direction} "
            f"{trade_result.exit_type.upper()} {trade_result.pips_result:+.1f} pips "
            f"${trade_result.dollar_result:+.2f}"
        )
    
    def _update_performance_metrics(self):
        """Update all performance metrics"""
        if not self.trades:
            return
        
        # Update overall performance
        self.overall_performance = self._calculate_performance_metrics(self.trades)
        
        # Update per-pair performance
        self.pair_performance = {}
        for pair in set(t.pair for t in self.trades):
            pair_trades = [t for t in self.trades if t.pair == pair]
            if len(pair_trades) >= 5:  # Minimum trades for meaningful statistics
                self.pair_performance[pair] = self._calculate_performance_metrics(pair_trades)
        
        # Update per-timeframe performance
        self.timeframe_performance = {}
        for timeframe in set(t.timeframe for t in self.trades):
            tf_trades = [t for t in self.trades if t.timeframe == timeframe]
            if len(tf_trades) >= 5:
                self.timeframe_performance[timeframe] = self._calculate_performance_metrics(tf_trades)
    
    def _calculate_performance_metrics(self, trades: List[TradeResult]) -> PerformanceMetrics:
        """Calculate performance metrics for a list of trades"""
        if not trades:
            return PerformanceMetrics(
                total_trades=0, winning_trades=0, losing_trades=0, win_rate=0,
                total_pips=0, total_profit=0, average_win=0, average_loss=0,
                largest_win=0, largest_loss=0, profit_factor=0, risk_reward_ratio=0,
                max_drawdown=0, max_drawdown_percent=0, sharpe_ratio=0,
                calmar_ratio=0, recovery_factor=0, expectancy=0
            )
        
        # Basic metrics
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.dollar_result > 0])
        losing_trades = len([t for t in trades if t.dollar_result < 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Profit/Loss metrics
        total_pips = sum(t.pips_result for t in trades)
        total_profit = sum(t.dollar_result for t in trades)
        
        winning_amounts = [t.dollar_result for t in trades if t.dollar_result > 0]
        losing_amounts = [abs(t.dollar_result) for t in trades if t.dollar_result < 0]
        
        average_win = np.mean(winning_amounts) if winning_amounts else 0
        average_loss = np.mean(losing_amounts) if losing_amounts else 0
        largest_win = max(winning_amounts) if winning_amounts else 0
        largest_loss = max(losing_amounts) if losing_amounts else 0
        
        # Profit factor
        gross_profit = sum(winning_amounts)
        gross_loss = sum(losing_amounts)
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0
        
        # Risk-reward ratio
        risk_reward_ratio = (average_win / average_loss) if average_loss > 0 else 0
        
        # Drawdown calculation
        max_drawdown, max_drawdown_percent = self._calculate_drawdown(trades)
        
        # Sharpe ratio (simplified)
        returns = [t.dollar_result for t in trades]
        if len(returns) > 1:
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe_ratio = (avg_return / std_return) if std_return > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Calmar ratio
        annual_return = self._calculate_annual_return(trades)
        calmar_ratio = (annual_return / max_drawdown_percent) if max_drawdown_percent > 0 else 0
        
        # Recovery factor
        recovery_factor = (total_profit / abs(max_drawdown)) if max_drawdown != 0 else 0
        
        # Expectancy
        expectancy = (win_rate/100 * average_win) - ((100-win_rate)/100 * average_loss)
        
        return PerformanceMetrics(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_pips=total_pips,
            total_profit=total_profit,
            average_win=average_win,
            average_loss=average_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            profit_factor=profit_factor,
            risk_reward_ratio=risk_reward_ratio,
            max_drawdown=max_drawdown,
            max_drawdown_percent=max_drawdown_percent,
            sharpe_ratio=sharpe_ratio,
            calmar_ratio=calmar_ratio,
            recovery_factor=recovery_factor,
            expectancy=expectancy
        )
    
    def _calculate_drawdown(self, trades: List[TradeResult]) -> Tuple[float, float]:
        """Calculate maximum drawdown"""
        if not trades:
            return 0, 0
        
        # Create equity curve
        equity = 10000  # Starting equity
        peak_equity = equity
        max_drawdown_dollar = 0
        max_drawdown_percent = 0
        
        for trade in trades:
            equity += trade.dollar_result
            
            if equity > peak_equity:
                peak_equity = equity
            
            drawdown_dollar = peak_equity - equity
            drawdown_percent = (drawdown_dollar / peak_equity * 100) if peak_equity > 0 else 0
            
            if drawdown_dollar > max_drawdown_dollar:
                max_drawdown_dollar = drawdown_dollar
            
            if drawdown_percent > max_drawdown_percent:
                max_drawdown_percent = drawdown_percent
        
        return max_drawdown_dollar, max_drawdown_percent
    
    def _calculate_annual_return(self, trades: List[TradeResult]) -> float:
        """Calculate annualized return percentage"""
        if not trades or len(trades) < 2:
            return 0
        
        start_date = min(t.entry_time for t in trades)
        end_date = max(t.exit_time for t in trades)
        days = (end_date - start_date).days
        
        if days == 0:
            return 0
        
        total_return = sum(t.dollar_result for t in trades)
        initial_equity = 10000
        
        years = days / 365.25
        annual_return = ((total_return / initial_equity) / years) * 100
        
        return annual_return
    
    def get_performance_summary(self) -> Dict:
        """Get comprehensive performance summary"""
        if not self.trades:
            return {'message': 'No trades recorded yet'}
        
        summary = {
            'overall': asdict(self.overall_performance),
            'by_pair': {pair: asdict(metrics) for pair, metrics in self.pair_performance.items()},
            'by_timeframe': {tf: asdict(metrics) for tf, metrics in self.timeframe_performance.items()},
            'recent_trades': [asdict(t) for t in self.trades[-10:]],  # Last 10 trades
            'monthly_results': self._get_monthly_results(),
            'weekly_results': self._get_weekly_results(),
            'equity_curve': self.equity_curve[-100:],  # Last 100 equity points
        }
        
        return summary
    
    def _get_monthly_results(self) -> Dict[str, float]:
        """Get monthly profit/loss results"""
        monthly_results = {}
        
        for trade in self.trades:
            month_key = trade.exit_time.strftime('%Y-%m')
            if month_key not in monthly_results:
                monthly_results[month_key] = 0
            monthly_results[month_key] += trade.dollar_result
        
        return monthly_results
    
    def _get_weekly_results(self) -> Dict[str, float]:
        """Get weekly profit/loss results"""
        weekly_results = {}
        
        for trade in self.trades:
            # Get start of week (Monday)
            week_start = trade.exit_time - timedelta(days=trade.exit_time.weekday())
            week_key = week_start.strftime('%Y-W%U')
            
            if week_key not in weekly_results:
                weekly_results[week_key] = 0
            weekly_results[week_key] += trade.dollar_result
        
        return weekly_results
    
    def get_signal_analysis(self) -> Dict:
        """Analyze signal performance patterns"""
        if not self.trades:
            return {}
        
        analysis = {
            'by_signal_strength': self._analyze_by_signal_strength(),
            'by_mtf_confirmation': self._analyze_by_mtf_confirmation(),
            'by_session': self._analyze_by_session(),
            'by_exit_type': self._analyze_by_exit_type(),
            'by_direction': self._analyze_by_direction(),
        }
        
        return analysis
    
    def _analyze_by_signal_strength(self) -> Dict:
        """Analyze performance by signal strength ranges"""
        ranges = {
            'weak': (0, 0.6),
            'medium': (0.6, 0.8),
            'strong': (0.8, 1.0)
        }
        
        results = {}
        for range_name, (min_val, max_val) in ranges.items():
            range_trades = [
                t for t in self.trades 
                if min_val <= t.signal_strength < max_val
            ]
            if range_trades:
                results[range_name] = {
                    'count': len(range_trades),
                    'win_rate': len([t for t in range_trades if t.dollar_result > 0]) / len(range_trades) * 100,
                    'avg_result': np.mean([t.dollar_result for t in range_trades]),
                    'total_pips': sum(t.pips_result for t in range_trades)
                }
        
        return results
    
    def _analyze_by_mtf_confirmation(self) -> Dict:
        """Analyze performance by multi-timeframe confirmation"""
        confirmed_trades = [t for t in self.trades if t.mtf_confirmation]
        unconfirmed_trades = [t for t in self.trades if not t.mtf_confirmation]
        
        results = {}
        
        if confirmed_trades:
            results['confirmed'] = {
                'count': len(confirmed_trades),
                'win_rate': len([t for t in confirmed_trades if t.dollar_result > 0]) / len(confirmed_trades) * 100,
                'avg_result': np.mean([t.dollar_result for t in confirmed_trades]),
                'total_pips': sum(t.pips_result for t in confirmed_trades)
            }
        
        if unconfirmed_trades:
            results['unconfirmed'] = {
                'count': len(unconfirmed_trades),
                'win_rate': len([t for t in unconfirmed_trades if t.dollar_result > 0]) / len(unconfirmed_trades) * 100,
                'avg_result': np.mean([t.dollar_result for t in unconfirmed_trades]),
                'total_pips': sum(t.pips_result for t in unconfirmed_trades)
            }
        
        return results
    
    def _analyze_by_session(self) -> Dict:
        """Analyze performance by trading session"""
        sessions = {}
        
        for trade in self.trades:
            session = trade.session
            if session not in sessions:
                sessions[session] = []
            sessions[session].append(trade)
        
        results = {}
        for session, trades in sessions.items():
            if trades:
                results[session] = {
                    'count': len(trades),
                    'win_rate': len([t for t in trades if t.dollar_result > 0]) / len(trades) * 100,
                    'avg_result': np.mean([t.dollar_result for t in trades]),
                    'total_pips': sum(t.pips_result for t in trades)
                }
        
        return results
    
    def _analyze_by_exit_type(self) -> Dict:
        """Analyze performance by exit type"""
        exit_types = {}
        
        for trade in self.trades:
            exit_type = trade.exit_type
            if exit_type not in exit_types:
                exit_types[exit_type] = []
            exit_types[exit_type].append(trade)
        
        results = {}
        for exit_type, trades in exit_types.items():
            if trades:
                results[exit_type] = {
                    'count': len(trades),
                    'avg_result': np.mean([t.dollar_result for t in trades]),
                    'total_pips': sum(t.pips_result for t in trades),
                    'avg_duration': np.mean([t.duration_minutes for t in trades])
                }
        
        return results
    
    def _analyze_by_direction(self) -> Dict:
        """Analyze performance by trade direction"""
        buy_trades = [t for t in self.trades if t.direction == 'BUY']
        sell_trades = [t for t in self.trades if t.direction == 'SELL']
        
        results = {}
        
        if buy_trades:
            results['BUY'] = {
                'count': len(buy_trades),
                'win_rate': len([t for t in buy_trades if t.dollar_result > 0]) / len(buy_trades) * 100,
                'avg_result': np.mean([t.dollar_result for t in buy_trades]),
                'total_pips': sum(t.pips_result for t in buy_trades)
            }
        
        if sell_trades:
            results['SELL'] = {
                'count': len(sell_trades),
                'win_rate': len([t for t in sell_trades if t.dollar_result > 0]) / len(sell_trades) * 100,
                'avg_result': np.mean([t.dollar_result for t in sell_trades]),
                'total_pips': sum(t.pips_result for t in sell_trades)
            }
        
        return results
    
    def export_performance_report(self, format: str = 'json') -> str:
        """Export comprehensive performance report"""
        report_data = {
            'generated_at': datetime.now().isoformat(),
            'performance_summary': self.get_performance_summary(),
            'signal_analysis': self.get_signal_analysis(),
            'configuration': {
                'risk_percent': TradingConfig.DEFAULT_RISK_PERCENT,
                'mtf_enabled': TradingConfig.MTF_CONFIRMATION_ENABLED,
                'session_filtering': TradingConfig.SESSION_FILTERING_ENABLED,
                'active_sessions': TradingConfig.ACTIVE_SESSIONS,
                'min_signal_strength': TradingConfig.MIN_SIGNAL_STRENGTH
            }
        }
        
        if format.lower() == 'json':
            return json.dumps(report_data, indent=2, default=str)
        else:
            # Could add CSV, Excel formats here
            return json.dumps(report_data, indent=2, default=str)

# Global instance
performance_tracker = PerformanceTracker()
