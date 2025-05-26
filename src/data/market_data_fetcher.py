
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import oandapyV20
import oandapyV20.endpoints.instruments as instruments
from src.config.trading_config import TradingConfig

logger = logging.getLogger(__name__)

class MarketDataFetcher:
    """Enhanced market data fetcher for multiple pairs and timeframes"""
    
    def __init__(self):
        self.api = oandapyV20.API(
            access_token=TradingConfig.OANDA_API_KEY,
            environment=TradingConfig.OANDA_ENVIRONMENT
        )
        self.data_cache: Dict[str, pd.DataFrame] = {}
        self.last_update: Dict[str, datetime] = {}
    
    def _get_cache_key(self, pair: str, timeframe: str) -> str:
        """Generate cache key for pair-timeframe combination"""
        return f"{pair}_{timeframe}"
    
    async def fetch_ohlcv_data(self, pair: str, timeframe: str, count: int = 500) -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV data for a specific pair and timeframe
        
        Args:
            pair: Trading pair symbol (e.g., 'EUR_USD')
            timeframe: Timeframe code (e.g., 'H1', 'H4', 'D1')
            count: Number of candles to fetch
            
        Returns:
            DataFrame with OHLCV data and timestamp index
        """
        try:
            timeframe_config = TradingConfig.get_timeframe_config(timeframe)
            if not timeframe_config:
                logger.error(f"Invalid timeframe: {timeframe}")
                return None
            
            params = {
                "count": count,
                "granularity": timeframe_config.oanda_granularity,
                "price": "M"  # Mid prices
            }
            
            request = instruments.InstrumentsCandles(
                instrument=pair,
                params=params
            )
            
            # Execute request asynchronously
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.api.request(request)
            )
            
            # Process candles data
            candles_data = []
            for candle in response['candles']:
                if candle['complete']:
                    candles_data.append({
                        'timestamp': pd.to_datetime(candle['time']),
                        'open': float(candle['mid']['o']),
                        'high': float(candle['mid']['h']),
                        'low': float(candle['mid']['l']),
                        'close': float(candle['mid']['c']),
                        'volume': int(candle['volume'])
                    })
            
            if not candles_data:
                logger.warning(f"No candle data received for {pair} {timeframe}")
                return None
            
            df = pd.DataFrame(candles_data)
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            
            # Cache the data
            cache_key = self._get_cache_key(pair, timeframe)
            self.data_cache[cache_key] = df
            self.last_update[cache_key] = datetime.now()
            
            logger.info(f"Fetched {len(df)} candles for {pair} {timeframe}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data for {pair} {timeframe}: {e}")
            return None
    
    async def fetch_all_pairs_data(self) -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        Fetch data for all configured pairs and timeframes
        
        Returns:
            Dictionary with structure: {pair: {timeframe: DataFrame}}
        """
        all_data = {}
        
        # Create tasks for all pair-timeframe combinations
        tasks = []
        for pair_symbol in TradingConfig.PAIRS.keys():
            all_data[pair_symbol] = {}
            for timeframe_code in TradingConfig.TIMEFRAMES.keys():
                task = self.fetch_ohlcv_data(pair_symbol, timeframe_code)
                tasks.append((pair_symbol, timeframe_code, task))
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*[task[2] for task in tasks], return_exceptions=True)
        
        # Process results
        for i, (pair_symbol, timeframe_code, _) in enumerate(tasks):
            result = results[i]
            if isinstance(result, pd.DataFrame):
                all_data[pair_symbol][timeframe_code] = result
            else:
                logger.error(f"Failed to fetch data for {pair_symbol} {timeframe_code}: {result}")
                all_data[pair_symbol][timeframe_code] = None
        
        return all_data
    
    def get_cached_data(self, pair: str, timeframe: str) -> Optional[pd.DataFrame]:
        """Get cached data for a pair-timeframe combination"""
        cache_key = self._get_cache_key(pair, timeframe)
        return self.data_cache.get(cache_key)
    
    def is_data_fresh(self, pair: str, timeframe: str, max_age_minutes: int = 5) -> bool:
        """Check if cached data is fresh enough"""
        cache_key = self._get_cache_key(pair, timeframe)
        last_update = self.last_update.get(cache_key)
        
        if not last_update:
            return False
        
        age = datetime.now() - last_update
        return age.total_seconds() < (max_age_minutes * 60)
    
    async def get_current_price(self, pair: str) -> Optional[Dict]:
        """Get current bid/ask prices for a pair"""
        try:
            request = instruments.InstrumentsPricing(
                accountID=TradingConfig.OANDA_ACCOUNT_ID,
                params={"instruments": pair}
            )
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.api.request(request)
            )
            
            if response['prices']:
                price_data = response['prices'][0]
                return {
                    'instrument': price_data['instrument'],
                    'bid': float(price_data['bids'][0]['price']),
                    'ask': float(price_data['asks'][0]['price']),
                    'mid': (float(price_data['bids'][0]['price']) + float(price_data['asks'][0]['price'])) / 2,
                    'spread': float(price_data['asks'][0]['price']) - float(price_data['bids'][0]['price']),
                    'timestamp': pd.to_datetime(price_data['time'])
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching current price for {pair}: {e}")
            return None

# Global instance
market_data_fetcher = MarketDataFetcher()
