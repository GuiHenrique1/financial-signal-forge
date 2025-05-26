
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategy import TradingStrategy

class TestTradingStrategy:
    """Test cases for trading strategy"""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample OHLCV data for testing"""
        dates = pd.date_range(start='2023-01-01', periods=100, freq='5T')
        
        # Generate realistic price data
        base_price = 1.0500
        price_changes = np.random.normal(0, 0.0001, 100)
        prices = [base_price]
        
        for change in price_changes[1:]:
            new_price = prices[-1] + change
            prices.append(max(new_price, 0.5))  # Ensure positive prices
        
        # Create OHLCV data
        data = []
        for i, (date, price) in enumerate(zip(dates, prices)):
            high = price + abs(np.random.normal(0, 0.00005))
            low = price - abs(np.random.normal(0, 0.00005))
            open_price = prices[i-1] if i > 0 else price
            close_price = price
            volume = np.random.randint(1000, 10000)
            
            data.append({
                'open': open_price,
                'high': high,
                'low': low,
                'close': close_price,
                'volume': volume
            })
        
        df = pd.DataFrame(data, index=dates)
        return df
    
    @pytest.fixture
    def strategy(self):
        """Create strategy instance"""
        return TradingStrategy()
    
    def test_calculate_indicators(self, strategy, sample_data):
        """Test indicator calculation"""
        result = strategy.calculate_indicators(sample_data)
        
        # Check that all expected indicators are present
        expected_indicators = [
            'rsi', 'macd', 'macd_signal', 'macd_hist',
            'sma_fast', 'sma_slow', 'bb_upper', 'bb_middle', 'bb_lower',
            'atr', 'stoch_k', 'stoch_d'
        ]
        
        for indicator in expected_indicators:
            assert indicator in result.columns, f"Missing indicator: {indicator}"
        
        # Check that indicators have reasonable values
        assert result['rsi'].max() <= 100, "RSI should not exceed 100"
        assert result['rsi'].min() >= 0, "RSI should not be below 0"
        
        # Check that we have non-null values (after initial period)
        assert not result['rsi'].iloc[-10:].isna().all(), "RSI should have values"
        assert not result['macd'].iloc[-10:].isna().all(), "MACD should have values"
    
    def test_detect_volatility(self, strategy, sample_data):
        """Test volatility detection"""
        data_with_indicators = strategy.calculate_indicators(sample_data)
        volatility = strategy.detect_volatility(data_with_indicators)
        
        assert isinstance(volatility, pd.Series), "Should return a pandas Series"
        assert len(volatility) == len(sample_data), "Should have same length as input"
        assert volatility.dtype == bool, "Should return boolean values"
    
    def test_generate_signals(self, strategy, sample_data):
        """Test signal generation"""
        result = strategy.generate_signals(sample_data)
        
        # Check that signal columns are added
        expected_columns = ['signal', 'signal_strength', 'signal_reason']
        for col in expected_columns:
            assert col in result.columns, f"Missing column: {col}"
        
        # Check signal values are valid
        valid_signals = [None, 'CALL', 'PUT']
        signal_values = result['signal'].dropna().unique()
        
        for signal in signal_values:
            assert signal in valid_signals, f"Invalid signal: {signal}"
        
        # Check signal strength is between 0 and 1
        strengths = result['signal_strength'].dropna()
        if not strengths.empty:
            assert strengths.min() >= 0, "Signal strength should be >= 0"
            assert strengths.max() <= 1, "Signal strength should be <= 1"
    
    def test_get_latest_signal(self, strategy, sample_data):
        """Test getting latest signal"""
        signal = strategy.get_latest_signal(sample_data)
        
        if signal is not None:
            # Check required fields
            required_fields = [
                'timestamp', 'pair', 'timeframe', 'signal', 
                'strength', 'reason', 'price', 'rsi', 'macd'
            ]
            
            for field in required_fields:
                assert field in signal, f"Missing field: {field}"
            
            # Check signal type
            assert signal['signal'] in ['CALL', 'PUT'], "Signal should be CALL or PUT"
            
            # Check strength
            assert 0 <= signal['strength'] <= 1, "Strength should be between 0 and 1"
    
    def test_evaluate_signal_conditions(self, strategy):
        """Test signal evaluation logic"""
        # Create test data for signal conditions
        current = pd.Series({
            'rsi': 25,  # Oversold
            'macd_hist': 0.1,  # Positive
            'close': 1.0520,
            'sma_fast': 1.0515,
            'sma_slow': 1.0510,
            'stoch_k': 15  # Oversold
        })
        
        previous = pd.Series({
            'rsi': 20,  # Was more oversold
            'macd_hist': -0.1,  # Was negative
            'stoch_k': 10  # Was more oversold
        })
        
        signal, strength, reason = strategy._evaluate_signal_conditions(current, previous)
        
        # Should generate CALL signal due to multiple bullish conditions
        assert signal == 'CALL', "Should generate CALL signal"
        assert strength > 0, "Should have positive strength"
        assert len(reason) > 0, "Should have reason text"
    
    def test_bullish_conditions(self, strategy):
        """Test specific bullish signal conditions"""
        # RSI oversold recovery
        current = pd.Series({
            'rsi': 35,
            'macd_hist': 0.05,
            'close': 1.0520,
            'sma_fast': 1.0515,
            'sma_slow': 1.0510,
            'stoch_k': 25
        })
        
        previous = pd.Series({
            'rsi': 25,  # Was oversold
            'macd_hist': -0.1,
            'stoch_k': 15
        })
        
        signal, strength, reason = strategy._evaluate_signal_conditions(current, previous)
        
        assert signal == 'CALL'
        assert 'RSI oversold recovery' in reason
    
    def test_bearish_conditions(self, strategy):
        """Test specific bearish signal conditions"""
        # RSI overbought decline
        current = pd.Series({
            'rsi': 75,
            'macd_hist': -0.05,
            'close': 1.0480,
            'sma_fast': 1.0485,
            'sma_slow': 1.0490,
            'stoch_k': 75
        })
        
        previous = pd.Series({
            'rsi': 80,  # Was overbought
            'macd_hist': 0.1,
            'stoch_k': 85
        })
        
        signal, strength, reason = strategy._evaluate_signal_conditions(current, previous)
        
        assert signal == 'PUT'
        assert 'RSI overbought decline' in reason
    
    def test_no_signal_conditions(self, strategy):
        """Test when no signal should be generated"""
        # Neutral conditions
        current = pd.Series({
            'rsi': 50,  # Neutral
            'macd_hist': 0.01,  # Minimal
            'close': 1.0500,
            'sma_fast': 1.0500,
            'sma_slow': 1.0500,
            'stoch_k': 50
        })
        
        previous = pd.Series({
            'rsi': 50,
            'macd_hist': 0.01,
            'stoch_k': 50
        })
        
        signal, strength, reason = strategy._evaluate_signal_conditions(current, previous)
        
        assert signal is None, "Should not generate signal in neutral conditions"
        assert strength == 0, "Strength should be 0"
        assert reason == "", "Reason should be empty"

if __name__ == "__main__":
    pytest.main([__file__])
