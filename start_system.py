
#!/usr/bin/env python3
"""
Trading Signals System Startup Script
=====================================

This script starts both the backend API and provides instructions for the frontend.
"""

import os
import sys
import subprocess
import time
import threading
import webbrowser
from pathlib import Path

def print_banner():
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                   Trading Signals Pro v2.0                    ║
║                  Real-time Signal Generation                  ║
╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_requirements():
    """Check if required packages are installed"""
    required_packages = [
        'fastapi', 'uvicorn', 'pandas', 'numpy', 'oandapyV20', 
        'pandas_ta', 'python-dotenv', 'asyncio'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Please install them using: pip install -r requirements.txt")
        return False
    
    print("✅ All required packages are installed")
    return True

def check_environment():
    """Check if environment variables are set"""
    required_env_vars = [
        'OANDA_API_KEY', 'OANDA_ACCOUNT_ID', 
        'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID'
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("Please set them in your .env file or environment")
        print("The system will run with mock data for demo purposes.")
        return False
    
    print("✅ Environment variables are configured")
    return True

def start_backend():
    """Start the FastAPI backend server"""
    print("\n🚀 Starting backend API server...")
    
    try:
        # Change to the src/backend directory
        backend_path = Path(__file__).parent / "src" / "backend"
        
        if backend_path.exists():
            os.chdir(backend_path)
            subprocess.run([
                sys.executable, "integrated_api.py"
            ], check=True)
        else:
            # Fallback to current directory
            subprocess.run([
                sys.executable, "-m", "uvicorn", 
                "src.backend.integrated_api:app",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--reload"
            ], check=True)
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start backend: {e}")
        return False
    except KeyboardInterrupt:
        print("\n🛑 Backend server stopped by user")
        return False

def wait_for_backend():
    """Wait for backend to be ready"""
    import requests
    import time
    
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ Backend is ready!")
                return True
        except:
            pass
        
        if attempt < max_attempts - 1:
            print(f"⏳ Waiting for backend... ({attempt + 1}/{max_attempts})")
            time.sleep(2)
    
    print("❌ Backend failed to start within expected time")
    return False

def print_frontend_instructions():
    """Print instructions for starting the frontend"""
    instructions = """
🌐 Frontend Setup Instructions:
================================

1. Open a new terminal window
2. Navigate to your project directory
3. Install frontend dependencies (if not done already):
   npm install

4. Start the development server:
   npm run dev

5. Open your browser to: http://localhost:5173

📊 API Endpoints Available:
===========================
• Health Check: http://localhost:8000/health
• All Signals: http://localhost:8000/signals
• Proximity Signals: http://localhost:8000/proximity-signals
• Latest Signal: http://localhost:8000/signal
• Market Data: http://localhost:8000/market-data
• API Docs: http://localhost:8000/docs

🔧 Configuration:
=================
• Edit .env file for API keys
• Adjust proximity distance in the UI
• Enable/disable auto-refresh in settings

📱 Features:
============
• Real-time signal generation
• Proximity-based filtering
• Multi-timeframe analysis
• Live market data
• Signal notifications
• Copy trading signals

✨ The system is now running with integrated backend and frontend!
    """
    print(instructions)

def main():
    """Main startup function"""
    print_banner()
    
    # Check system requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check environment configuration
    env_ok = check_environment()
    
    print(f"\n📍 Current directory: {os.getcwd()}")
    print(f"📁 Python path: {sys.executable}")
    
    try:
        # Start backend in a separate thread
        backend_thread = threading.Thread(target=start_backend, daemon=True)
        backend_thread.start()
        
        # Wait a moment for backend to start
        time.sleep(5)
        
        # Check if backend is responding
        if wait_for_backend():
            print_frontend_instructions()
            
            # Keep the script running
            print("\n🎯 Backend server is running...")
            print("Press Ctrl+C to stop the server")
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Shutting down gracefully...")
        else:
            print("❌ Backend failed to start properly")
            
    except Exception as e:
        print(f"❌ Error starting system: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
