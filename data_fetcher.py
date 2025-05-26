
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import pandas as pd
import oandapyV20
import oandapyV20.endpoints.instruments as instruments
from config import Config

logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

class OandaDataFetcher:
    """
    Fetches real-time market data from Oanda API
    """
    
    def __init__(self):
        self.api = oandapyV20.API(
            access_token=Config.OANDA_API_KEY,
            environment=Config.OANDA_ENVIRONMENT
        )
        self.current_data: Optional[pd.DataFrame] = None
        
    async def fetch_candles(self, count: int = None) -> pd.DataFrame:
        """
        Fetch OHLCV candles from Oanda API
        
        Args:
            count: Number of candles to fetch (default from config)
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            count = count or Config.MAX_CANDLES
            
            params = {
                "count": count,
                "granularity": Config.TIMEFRAME,
                "price": "M"  # Mid prices
            }
            
            request = instruments.InstrumentsCandles(
                instrument=Config.CURRENCY_PAIR,
                params=params
            )
            
            # Execute request in thread to avoid blocking
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
                        'time': pd.to_datetime(candle['time']),
                        'open': float(candle['mid']['o']),
                        'high': float(candle['mid']['h']),
                        'low': float(candle['mid']['l']),
                        'close': float(candle['mid']['c']),
                        'volume': int(candle['volume'])
                    })
            
            df = pd.DataFrame(candles_data)
            df.set_index('time', inplace=True)
            df.sort_index(inplace=True)
            
            self.current_data = df
            logger.info(f"Fetched {len(df)} candles for {Config.CURRENCY_PAIR}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching candles: {e}")
            raise
    
    async def get_latest_price(self) -> Dict[str, float]:
        """
        Get latest bid/ask prices
        
        Returns:
            Dictionary with current prices
        """
        try:
            request = instruments.InstrumentsPricing(
                accountID=Config.OANDA_ACCOUNT_ID,
                params={"instruments": Config.CURRENCY_PAIR}
            )
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.api.request(request)
            )
            
            price_data = response['prices'][0]
            
            return {
                'instrument': price_data['instrument'],
                'bid': float(price_data['bids'][0]['price']),
                'ask': float(price_data['asks'][0]['price']),
                'spread': float(price_data['asks'][0]['price']) - float(price_data['bids'][0]['price']),
                'timestamp': pd.to_datetime(price_data['time'])
            }
            
        except Exception as e:
            logger.error(f"Error fetching latest price: {e}")
            raise
    
    def get_current_data(self) -> Optional[pd.DataFrame]:
        """Get current stored data"""
        return self.current_data
    
    async def start_data_stream(self, callback=None):
        """
        Start continuous data fetching
        
        Args:
            callback: Function to call when new data is available
        """
        logger.info(f"Starting data stream for {Config.CURRENCY_PAIR} every {Config.DATA_FETCH_INTERVAL} seconds")
        
        while True:
            try:
                df = await self.fetch_candles()
                
                if callback and df is not None:
                    await callback(df)
                    
                await asyncio.sleep(Config.DATA_FETCH_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error in data stream: {e}")
                await asyncio.sleep(30)  # Wait 30 seconds before retry

# Singleton instance
data_fetcher = OandaDataFetcher()
