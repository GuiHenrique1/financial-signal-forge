
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import asyncio
import time
from typing import Optional, Dict, Any
import logging
from data_fetcher import data_fetcher
from strategy import strategy
from config import Config

# Configure logging
logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Trading Signals API",
    description="Real-time trading signals based on technical analysis",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache for signals
signal_cache = {
    'data': None,
    'timestamp': 0,
    'ttl': Config.CACHE_DURATION
}

@app.on_event("startup")
async def startup_event():
    """Initialize data fetcher and start background tasks"""
    try:
        # Validate configuration
        Config.validate()
        
        # Initial data fetch
        await data_fetcher.fetch_candles()
        logger.info("API startup completed successfully")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

async def update_data_background():
    """Background task to update market data"""
    while True:
        try:
            await data_fetcher.fetch_candles()
            # Clear cache when new data arrives
            signal_cache['timestamp'] = 0
            await asyncio.sleep(Config.DATA_FETCH_INTERVAL)
        except Exception as e:
            logger.error(f"Error in background data update: {e}")
            await asyncio.sleep(60)

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Trading Signals API",
        "version": "1.0.0",
        "endpoints": {
            "/signal": "Get latest trading signal",
            "/health": "Health check",
            "/status": "System status",
            "/docs": "API documentation"
        }
    }

@app.get("/signal")
async def get_signal():
    """
    Get latest trading signal
    
    Returns:
        JSON with signal information
    """
    try:
        # Check cache first
        current_time = time.time()
        if (signal_cache['data'] and 
            current_time - signal_cache['timestamp'] < signal_cache['ttl']):
            return signal_cache['data']
        
        # Get current market data
        df = data_fetcher.get_current_data()
        if df is None or df.empty:
            raise HTTPException(status_code=503, detail="No market data available")
        
        # Generate signal
        signal_data = strategy.get_latest_signal(df)
        
        if signal_data is None:
            response = {
                "pair": Config.CURRENCY_PAIR,
                "timeframe": Config.TIMEFRAME,
                "signal": None,
                "message": "No signal generated",
                "timestamp": current_time
            }
        else:
            response = {
                "pair": signal_data['pair'],
                "timeframe": signal_data['timeframe'],
                "signal": signal_data['signal'],
                "strength": round(signal_data['strength'], 3),
                "reason": signal_data['reason'],
                "price": round(signal_data['price'], 5),
                "indicators": {
                    "rsi": round(signal_data['rsi'], 2),
                    "macd": round(signal_data['macd'], 6),
                    "macd_signal": round(signal_data['macd_signal'], 6),
                    "macd_hist": round(signal_data['macd_hist'], 6)
                },
                "timestamp": signal_data['timestamp'].isoformat(),
                "generated_at": current_time
            }
        
        # Update cache
        signal_cache['data'] = response
        signal_cache['timestamp'] = current_time
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check if we have recent data
        df = data_fetcher.get_current_data()
        data_available = df is not None and not df.empty
        
        # Check latest data age
        latest_data_age = None
        if data_available:
            latest_time = df.index[-1]
            latest_data_age = (time.time() - latest_time.timestamp()) / 60  # minutes
        
        return {
            "status": "healthy" if data_available else "degraded",
            "data_available": data_available,
            "latest_data_age_minutes": round(latest_data_age, 2) if latest_data_age else None,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }

@app.get("/status")
async def get_status():
    """Get detailed system status"""
    try:
        df = data_fetcher.get_current_data()
        
        if df is None or df.empty:
            return {
                "status": "no_data",
                "message": "No market data available"
            }
        
        # Calculate basic statistics
        latest_price = df['close'].iloc[-1]
        price_change_24h = ((latest_price - df['close'].iloc[0]) / df['close'].iloc[0]) * 100
        
        return {
            "status": "active",
            "pair": Config.CURRENCY_PAIR,
            "timeframe": Config.TIMEFRAME,
            "data_points": len(df),
            "latest_price": round(latest_price, 5),
            "price_change_24h_pct": round(price_change_24h, 3),
            "data_range": {
                "start": df.index[0].isoformat(),
                "end": df.index[-1].isoformat()
            },
            "last_update": time.time()
        }
        
    except Exception as e:
        logger.error(f"Status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Simple web dashboard"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Trading Signals Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .signal-box { 
                padding: 20px; 
                border: 2px solid #ddd; 
                border-radius: 8px; 
                margin: 20px 0;
                background-color: #f9f9f9;
            }
            .signal-call { border-color: #4CAF50; background-color: #e8f5e8; }
            .signal-put { border-color: #f44336; background-color: #fde8e8; }
            .signal-none { border-color: #999; background-color: #f0f0f0; }
            .refresh-btn {
                background-color: #2196F3;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                margin: 10px 0;
            }
            .refresh-btn:hover { background-color: #1976D2; }
        </style>
        <script>
            async function refreshSignal() {
                try {
                    const response = await fetch('/signal');
                    const data = await response.json();
                    updateSignalDisplay(data);
                } catch (error) {
                    console.error('Error fetching signal:', error);
                }
            }
            
            function updateSignalDisplay(data) {
                const signalBox = document.getElementById('signal-box');
                const signalType = data.signal || 'none';
                
                signalBox.className = `signal-box signal-${signalType.toLowerCase()}`;
                
                document.getElementById('signal-content').innerHTML = `
                    <h2>Latest Signal: ${data.signal || 'No Signal'}</h2>
                    <p><strong>Pair:</strong> ${data.pair}</p>
                    <p><strong>Timeframe:</strong> ${data.timeframe}</p>
                    <p><strong>Price:</strong> ${data.price || 'N/A'}</p>
                    <p><strong>Strength:</strong> ${data.strength || 'N/A'}</p>
                    <p><strong>Reason:</strong> ${data.reason || 'N/A'}</p>
                    <p><strong>Timestamp:</strong> ${data.timestamp || new Date().toISOString()}</p>
                `;
            }
            
            // Auto-refresh every 30 seconds
            setInterval(refreshSignal, 30000);
            
            // Initial load
            window.onload = refreshSignal;
        </script>
    </head>
    <body>
        <div class="container">
            <h1>Trading Signals Dashboard</h1>
            <button class="refresh-btn" onclick="refreshSignal()">Refresh Signal</button>
            
            <div id="signal-box" class="signal-box">
                <div id="signal-content">
                    <p>Loading...</p>
                </div>
            </div>
            
            <div>
                <h3>API Endpoints:</h3>
                <ul>
                    <li><a href="/signal" target="_blank">/signal</a> - Get latest signal (JSON)</li>
                    <li><a href="/health" target="_blank">/health</a> - Health check</li>
                    <li><a href="/status" target="_blank">/status</a> - System status</li>
                    <li><a href="/docs" target="_blank">/docs</a> - API documentation</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    
    # Start background data update task
    asyncio.create_task(update_data_background())
    
    uvicorn.run(
        "api:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=True,
        log_level=Config.LOG_LEVEL.lower()
    )
