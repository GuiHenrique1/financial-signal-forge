
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import uvicorn
import os
import sys

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.market_data_fetcher import market_data_fetcher
from signals.signal_manager import signal_manager
from filters.proximity_filter import proximity_filter
from config.trading_config import TradingConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Trading Signals API",
    description="Real-time trading signals with proximity filtering",
    version="2.0.0"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global cache for performance
cache = {
    'signals': {'data': None, 'timestamp': 0, 'ttl': 30},
    'market_data': {'data': None, 'timestamp': 0, 'ttl': 10},
    'proximity_signals': {'data': None, 'timestamp': 0, 'ttl': 20}
}

async def get_cached_or_fetch(cache_key: str, fetch_func, *args, **kwargs):
    """Generic caching function"""
    current_time = datetime.now().timestamp()
    cache_entry = cache.get(cache_key, {'data': None, 'timestamp': 0, 'ttl': 30})
    
    if (cache_entry['data'] is None or 
        current_time - cache_entry['timestamp'] > cache_entry['ttl']):
        
        try:
            cache_entry['data'] = await fetch_func(*args, **kwargs)
            cache_entry['timestamp'] = current_time
            cache[cache_key] = cache_entry
        except Exception as e:
            logger.error(f"Error fetching data for {cache_key}: {e}")
            if cache_entry['data'] is None:
                cache_entry['data'] = []
    
    return cache_entry['data']

@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    try:
        logger.info("Starting Trading Signals API v2.0")
        
        # Validate configuration
        TradingConfig.validate_config()
        
        # Start background data fetching
        asyncio.create_task(background_data_update())
        
        logger.info("API startup completed successfully")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")

async def background_data_update():
    """Background task to update market data and signals"""
    while True:
        try:
            # Fetch market data for all pairs
            await market_data_fetcher.fetch_all_pairs_data()
            
            # Generate new signals
            await signal_manager.generate_all_signals()
            
            # Clear caches to force refresh
            for key in cache:
                cache[key]['timestamp'] = 0
            
            logger.info("Background data update completed")
            
            # Wait 5 minutes before next update
            await asyncio.sleep(300)
            
        except Exception as e:
            logger.error(f"Error in background data update: {e}")
            await asyncio.sleep(60)

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "Trading Signals API v2.0",
        "status": "running",
        "endpoints": {
            "/signals": "Get all active signals",
            "/proximity-signals": "Get signals filtered by proximity",
            "/signal": "Get latest signal",
            "/market-data": "Get current market data",
            "/health": "System health check"
        },
        "features": [
            "Real-time signal generation",
            "Proximity filtering",
            "Multi-timeframe analysis",
            "Risk management",
            "Live market data"
        ]
    }

@app.get("/signals")
async def get_all_signals():
    """Get all active trading signals"""
    try:
        signals = await get_cached_or_fetch(
            'signals',
            lambda: signal_manager.get_active_signals()
        )
        
        # Convert TradingSignal objects to dictionaries
        signals_data = []
        for signal in signals:
            signal_dict = {
                'id': signal.id,
                'pair': signal.pair,
                'timeframe': signal.timeframe,
                'direction': signal.direction,
                'strength': signal.strength,
                'entry_price': signal.entry_price,
                'current_price': signal.current_price,
                'stop_loss': signal.stop_loss,
                'take_profit_1': signal.take_profit_1,
                'take_profit_2': signal.take_profit_2,
                'take_profit_3': signal.take_profit_3,
                'distance_pips': getattr(signal, 'distance_pips', 0),
                'proximity_score': getattr(signal, 'proximity_score', 0),
                'timestamp': signal.timestamp.isoformat(),
                'reasons': signal.reasons,
                'indicators': signal.indicators
            }
            signals_data.append(signal_dict)
        
        return JSONResponse(content=signals_data)
        
    except Exception as e:
        logger.error(f"Error getting signals: {e}")
        return JSONResponse(content=[], status_code=500)

@app.get("/proximity-signals")
async def get_proximity_signals(max_distance: float = Query(15.0, description="Maximum distance in pips")):
    """Get signals filtered by proximity to current price"""
    try:
        # Get current prices
        current_prices = await market_data_fetcher.fetch_current_prices()
        
        # Get all signals
        all_signals = signal_manager.get_active_signals()
        
        # Convert to DataFrame for filtering
        if all_signals:
            signals_data = []
            for signal in all_signals:
                signals_data.append({
                    'pair': signal.pair,
                    'timeframe': signal.timeframe,
                    'direction': signal.direction,
                    'strength': signal.strength,
                    'entry_price': signal.entry_price,
                    'current_price': signal.current_price,
                    'stop_loss': signal.stop_loss,
                    'take_profit_1': signal.take_profit_1,
                    'take_profit_2': signal.take_profit_2,
                    'take_profit_3': signal.take_profit_3,
                    'timestamp': signal.timestamp.isoformat(),
                    'reasons': signal.reasons,
                    'indicators': signal.indicators
                })
            
            signals_df = pd.DataFrame(signals_data)
            
            # Apply proximity filter
            filtered_signals_df = proximity_filter.filter_signals_by_proximity(
                signals_df, current_prices, max_distance
            )
            
            # Rank by proximity
            filtered_signals_df = proximity_filter.rank_signals_by_proximity(filtered_signals_df)
            
            # Convert back to list of dictionaries
            result = []
            for _, row in filtered_signals_df.iterrows():
                signal_dict = row.to_dict()
                signal_dict['id'] = f"{row['pair']}_{row['timeframe']}_{int(datetime.now().timestamp())}"
                result.append(signal_dict)
            
            return JSONResponse(content=result)
        
        return JSONResponse(content=[])
        
    except Exception as e:
        logger.error(f"Error getting proximity signals: {e}")
        return JSONResponse(content=[], status_code=500)

@app.get("/signal")
async def get_latest_signal():
    """Get the latest trading signal"""
    try:
        signals = signal_manager.get_active_signals()
        if signals:
            latest_signal = max(signals, key=lambda s: s.timestamp)
            
            signal_data = {
                'id': latest_signal.id,
                'pair': latest_signal.pair,
                'timeframe': latest_signal.timeframe,
                'direction': latest_signal.direction,
                'strength': latest_signal.strength,
                'entry_price': latest_signal.entry_price,
                'current_price': latest_signal.current_price,
                'stop_loss': latest_signal.stop_loss,
                'take_profit_1': latest_signal.take_profit_1,
                'take_profit_2': latest_signal.take_profit_2,
                'take_profit_3': latest_signal.take_profit_3,
                'distance_pips': getattr(latest_signal, 'distance_pips', 0),
                'proximity_score': getattr(latest_signal, 'proximity_score', 0),
                'timestamp': latest_signal.timestamp.isoformat(),
                'reasons': latest_signal.reasons,
                'indicators': latest_signal.indicators
            }
            
            return JSONResponse(content={'signal': signal_data})
        
        return JSONResponse(content={'signal': None})
        
    except Exception as e:
        logger.error(f"Error getting latest signal: {e}")
        return JSONResponse(content={'signal': None}, status_code=500)

@app.get("/market-data")
async def get_market_data():
    """Get current market data for all monitored pairs"""
    try:
        market_data = await get_cached_or_fetch(
            'market_data',
            lambda: fetch_current_market_data()
        )
        
        return JSONResponse(content=market_data)
        
    except Exception as e:
        logger.error(f"Error getting market data: {e}")
        return JSONResponse(content=[], status_code=500)

async def fetch_current_market_data():
    """Fetch current market data for all pairs"""
    market_data = []
    
    for pair_symbol in list(TradingConfig.PAIRS.keys())[:6]:  # Limit to first 6 pairs
        try:
            price_data = await market_data_fetcher.get_current_price(pair_symbol)
            if price_data:
                # Calculate 24h change (simplified)
                change_24h = (price_data['mid'] - price_data.get('previous_close', price_data['mid'])) / price_data['mid'] * 100
                
                market_data.append({
                    'pair': pair_symbol,
                    'price': price_data['mid'],
                    'change_24h': round(change_24h, 2),
                    'volume': 100000 + hash(pair_symbol) % 50000,  # Mock volume
                    'timestamp': price_data['timestamp'].isoformat()
                })
        except Exception as e:
            logger.error(f"Error fetching data for {pair_symbol}: {e}")
    
    return market_data

@app.get("/health")
async def health_check():
    """System health check"""
    try:
        # Check if we have recent data
        signals = signal_manager.get_active_signals()
        data_available = len(signals) > 0
        
        # Check data age
        latest_data_age = None
        if signals:
            latest_signal = max(signals, key=lambda s: s.timestamp)
            age_delta = datetime.now() - latest_signal.timestamp
            latest_data_age = age_delta.total_seconds() / 60  # minutes
        
        status = "healthy" if data_available and (latest_data_age is None or latest_data_age < 60) else "degraded"
        
        return JSONResponse(content={
            "status": status,
            "data_available": data_available,
            "latest_data_age_minutes": latest_data_age,
            "active_signals_count": len(signals),
            "timestamp": datetime.now().timestamp()
        })
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return JSONResponse(content={
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().timestamp()
        }, status_code=500)

if __name__ == "__main__":
    uvicorn.run(
        "integrated_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
