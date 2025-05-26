
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from data_fetcher import data_fetcher
from strategy import strategy
from config import Config

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, Config.LOG_LEVEL)
)
logger = logging.getLogger(__name__)

class TradingBot:
    """
    Telegram bot for sending trading signals and alerts
    """
    
    def __init__(self):
        self.bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
        self.application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        self.last_signal_time = None
        self.last_signal_data = None
        self.is_running = False
        
        # Setup command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("signal", self.signal_command))
        self.application.add_handler(CommandHandler("stop", self.stop_command))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = f"""
🤖 **Trading Signals Bot**

Welcome! I'll send you real-time trading signals for {Config.CURRENCY_PAIR}.

**Available Commands:**
/help - Show this help message
/status - Check system status  
/signal - Get latest signal
/stop - Stop signal alerts

**Signal Types:**
📈 CALL - Buy signal
📉 PUT - Sell signal  
⏸️ No Signal - Wait for better opportunity

Signals are based on technical analysis including RSI, MACD, and moving averages.

**Disclaimer:** This is for educational purposes only. Always do your own research before trading.
        """
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
        logger.info(f"Start command from user {update.effective_user.id}")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = f"""
🔧 **Bot Commands:**

/start - Welcome message and setup
/help - Show this help
/status - Check if system is running properly
/signal - Get the latest trading signal
/stop - Stop receiving automatic alerts

**Current Configuration:**
• Pair: {Config.CURRENCY_PAIR}
• Timeframe: {Config.TIMEFRAME}
• Update Interval: {Config.DATA_FETCH_INTERVAL}s

**How Signals Work:**
Signals are generated using multiple technical indicators:
• RSI (Relative Strength Index)
• MACD (Moving Average Convergence Divergence)  
• Moving Averages (SMA)
• Stochastic Oscillator

A signal is generated only when at least 2 indicators agree.

**Support:** Check logs for technical issues or contact your system administrator.
        """
        
        await update.message.reply_text(help_message, parse_mode='Markdown')
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        try:
            # Check data availability
            df = data_fetcher.get_current_data()
            
            if df is None or df.empty:
                status_message = "❌ **Status: No Data**\n\nNo market data is currently available."
            else:
                latest_time = df.index[-1]
                data_age = datetime.now() - latest_time.replace(tzinfo=None)
                latest_price = df['close'].iloc[-1]
                
                status_message = f"""
✅ **Status: Running**

📊 **Market Data:**
• Latest Price: {latest_price:.5f}
• Data Points: {len(df)}
• Last Update: {data_age.seconds // 60} minutes ago

🤖 **Bot Status:**
• Monitoring: {Config.CURRENCY_PAIR}
• Timeframe: {Config.TIMEFRAME}
• Auto-alerts: {'ON' if self.is_running else 'OFF'}

⏰ **Last Signal:** {self.last_signal_time.strftime('%H:%M:%S') if self.last_signal_time else 'None today'}
                """
            
            await update.message.reply_text(status_message, parse_mode='Markdown')
            
        except Exception as e:
            error_message = f"❌ **Error checking status:**\n{str(e)}"
            await update.message.reply_text(error_message, parse_mode='Markdown')
            logger.error(f"Status command error: {e}")
    
    async def signal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /signal command"""
        try:
            # Get current data
            df = data_fetcher.get_current_data()
            
            if df is None or df.empty:
                await update.message.reply_text("❌ No market data available")
                return
            
            # Generate signal
            signal_data = strategy.get_latest_signal(df)
            
            if signal_data is None:
                message = f"""
⏸️ **No Signal**

📊 {Config.CURRENCY_PAIR} - {Config.TIMEFRAME}
💰 Price: {df['close'].iloc[-1]:.5f}

No trading opportunity detected at the moment.
                """
            else:
                message = self.format_signal_message(signal_data)
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            error_message = f"❌ **Error getting signal:**\n{str(e)}"
            await update.message.reply_text(error_message, parse_mode='Markdown')
            logger.error(f"Signal command error: {e}")
    
    async def stop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stop command"""
        self.is_running = False
        
        message = """
⏹️ **Auto-alerts Stopped**

You will no longer receive automatic signal alerts.

Use /start to resume alerts, or /signal to get signals manually.
        """
        
        await update.message.reply_text(message, parse_mode='Markdown')
        logger.info(f"Stop command from user {update.effective_user.id}")
    
    def format_signal_message(self, signal_data: Dict[str, Any]) -> str:
        """
        Format signal data into a nice Telegram message
        
        Args:
            signal_data: Signal information dictionary
            
        Returns:
            Formatted message string
        """
        signal_type = signal_data['signal']
        emoji = "📈" if signal_type == "CALL" else "📉"
        
        # Calculate signal expiry (15 minutes for M5 timeframe)
        expiry_minutes = 15 if Config.TIMEFRAME == "M5" else 30
        
        message = f"""
{emoji} **{Config.CURRENCY_PAIR} — {signal_type}**

🕒 {Config.TIMEFRAME} — válido por {expiry_minutes} minutos
💰 Preço: {signal_data['price']:.5f}
📊 Força: {signal_data['strength']:.1%}

**Indicadores:**
• RSI: {signal_data['rsi']:.1f}
• MACD: {signal_data['macd']:.6f}

**Razão:** {signal_data['reason']}

⏰ {signal_data['timestamp'].strftime('%H:%M:%S')}

⚠️ *Risco próprio - Analise antes de operar*
        """
        
        return message
    
    async def send_signal_alert(self, signal_data: Dict[str, Any]):
        """
        Send signal alert to configured chat
        
        Args:
            signal_data: Signal information dictionary
        """
        try:
            message = self.format_signal_message(signal_data)
            
            await self.bot.send_message(
                chat_id=Config.SIGNAL_CHAT_ID,
                text=message,
                parse_mode='Markdown'
            )
            
            self.last_signal_time = datetime.now()
            self.last_signal_data = signal_data
            
            logger.info(f"Signal alert sent: {signal_data['signal']} for {signal_data['pair']}")
            
        except Exception as e:
            logger.error(f"Error sending signal alert: {e}")
    
    async def monitor_signals(self):
        """
        Main monitoring loop for signals
        """
        logger.info("Starting signal monitoring...")
        self.is_running = True
        
        while self.is_running:
            try:
                # Get current data
                df = data_fetcher.get_current_data()
                
                if df is not None and not df.empty:
                    # Generate signal
                    signal_data = strategy.get_latest_signal(df)
                    
                    # Check if this is a new signal
                    if (signal_data and 
                        signal_data['signal'] in ['CALL', 'PUT'] and
                        self._is_new_signal(signal_data)):
                        
                        await self.send_signal_alert(signal_data)
                
                # Wait before next check
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in signal monitoring: {e}")
                await asyncio.sleep(30)  # Wait 30 seconds before retry
    
    def _is_new_signal(self, signal_data: Dict[str, Any]) -> bool:
        """
        Check if this is a new signal (not already sent)
        
        Args:
            signal_data: Current signal data
            
        Returns:
            True if this is a new signal
        """
        if self.last_signal_data is None:
            return True
        
        # Check if signal type changed
        if signal_data['signal'] != self.last_signal_data['signal']:
            return True
        
        # Check if enough time has passed (minimum 15 minutes between same signals)
        if self.last_signal_time:
            time_diff = datetime.now() - self.last_signal_time
            if time_diff < timedelta(minutes=15):
                return False
        
        # Check if signal timestamp is newer
        current_time = signal_data['timestamp'].replace(tzinfo=None)
        last_time = self.last_signal_data['timestamp'].replace(tzinfo=None)
        
        return current_time > last_time
    
    async def start_bot(self):
        """Start the Telegram bot"""
        try:
            Config.validate()
            
            # Initialize the application
            await self.application.initialize()
            await self.application.start()
            
            logger.info("Telegram bot started successfully")
            
            # Start data fetching
            data_fetch_task = asyncio.create_task(
                data_fetcher.start_data_stream()
            )
            
            # Start signal monitoring
            signal_monitor_task = asyncio.create_task(
                self.monitor_signals()
            )
            
            # Start polling for commands
            await self.application.updater.start_polling()
            
            # Wait for tasks
            await asyncio.gather(
                data_fetch_task,
                signal_monitor_task,
                return_exceptions=True
            )
            
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise
        finally:
            await self.application.stop()
    
    async def stop_bot(self):
        """Stop the Telegram bot"""
        self.is_running = False
        await self.application.stop()
        logger.info("Telegram bot stopped")

# Main execution
async def main():
    """Main function to run the bot"""
    try:
        bot = TradingBot()
        await bot.start_bot()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
