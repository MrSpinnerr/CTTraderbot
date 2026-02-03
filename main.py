#!/usr/bin/env python3
"""
Forex Trading Signal Bot with Virtual Trading Journal
Monitors currency pairs, generates signals, and tracks virtual trades
Files saved to Windows Desktop by default
"""

import sys
import os
import json
import time
import logging
import getpass
from datetime import datetime
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyzer import ForexAnalyzer
from chart_generator import ChartGenerator
from telegram_sender import TelegramSender
from trading_journal import TradingJournal, VirtualTrader

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== WINDOWS PATHS ====================

try:
    WINDOWS_USER = os.environ.get('USERNAME', getpass.getuser())
except:
    WINDOWS_USER = 'user'

WINDOWS_DESKTOP = f"/mnt/c/Users/{WINDOWS_USER}/Desktop"
APP_FOLDER = f"{WINDOWS_DESKTOP}/forex_trader_bot"
CHARTS_FOLDER = f"{APP_FOLDER}/charts"
DATA_FOLDER = f"{APP_FOLDER}/data"

# Create directories
os.makedirs(CHARTS_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)

# Telegram config
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

# Currency pairs
PAIRS = [
    'EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD', 'USD/CAD'
]

# Settings
CHECK_INTERVAL = 300  # 5 minutes
INITIAL_BALANCE = 10000.0

class ForexTradingBot:
    """Main trading bot class with virtual trading"""
    
    def __init__(self, virtual_trading=True, initial_balance=10000):
        self.config = Config()
        self.analyzer = ForexAnalyzer()
        self.chart_gen = ChartGenerator()
        self.telegram = TelegramSender()
        
        # Virtual trading
        self.virtual_trading = virtual_trading
        if virtual_trading:
            self.trader = VirtualTrader(initial_balance)
            logger.info(f"🎮 Virtual trading enabled. Balance: ${initial_balance}")
        
        # Currency pairs to monitor
        self.pairs = self.config.get('pairs', [
            'EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD', 'USD/CAD'
        ])
        
        # Trading session state
        self.last_signals = {}
        
        # Ensure charts directory exists
        Path(CHARTS_FOLDER).mkdir(exist_ok=True)
        
        # Check interval
        self.check_interval = self.config.get('check_interval', 300)  # 5 minutes
    
    def analyze_pair(self, pair):
        """Analyze a single currency pair"""
        logger.info(f"Analyzing {pair}...")
        
        # Get price data
        data = self.analyzer.get_price_data(pair, timeframe='1h', periods=100)
        if data is None:
            logger.warning(f"No data for {pair}")
            return None
        
        current_price = data['close'].iloc[-1]
        
        # Get trend
        trend = self.analyzer.get_trend(data)
        
        # Get support/resistance
        sr_levels = self.analyzer.find_support_resistance(data['close'])
        
        # Price position
        position = self.analyzer.get_price_position(current_price, sr_levels)
        
        # Candle pattern
        candle = self.analyzer.get_candle_patterns(data)
        
        # RSI
        rsi = self.analyzer.calculate_rsi(data['close'], 14)
        
        # Generate signal
        signal, score, reasons = self.analyzer.generate_signal(
            trend=trend,
            price_position=position,
            candle_pattern=candle,
            rsi=rsi
        )
        
        signal_data = {
            'pair': pair,
            'price': current_price,
            'trend': trend,
            'position': position,
            'support': sr_levels.get('support', [])[:3],
            'resistance': sr_levels.get('resistance', [])[:3],
            'candle_pattern': candle,
            'rsi': round(rsi, 1),
            'signal': signal,
            'score': score,
            'reasons': reasons,
            'timestamp': datetime.now().isoformat()
        }
        
        return signal_data
    
    def generate_chart(self, pair, signal_data):
        """Generate chart screenshot"""
        try:
            chart_path = self.chart_gen.create_analysis_chart(
                pair=pair,
                signal=signal_data,
                save_path=f"{CHARTS_FOLDER}/{pair.replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.png"
            )
            return chart_path
        except Exception as e:
            logger.error(f"Chart generation failed: {e}")
            return None
    
    def should_notify(self, pair, signal):
        """Check if we should send notification"""
        last_signal = self.last_signals.get(pair)
        
        # Always notify on BUY or SELL
        if signal in ['BUY', 'SELL']:
            return True
        
        # For HOLD, only notify if was previously BUY/SELL
        if signal == 'HOLD' and last_signal in ['BUY', 'SELL']:
            return True
        
        return False
    
    def process_pair(self, pair):
        """Process a single pair"""
        result = self.analyze_pair(pair)
        if result is None:
            return None
        
        signal = result['signal']
        logger.info(f"  → Signal: {signal} ({result['score']:.1f} points)")
        
        # Generate chart
        chart_path = self.generate_chart(pair, result)
        
        # Send notification
        if self.should_notify(pair, signal):
            self.telegram.send_signal(
                pair=pair,
                signal=signal,
                price=result['price'],
                trend=result['trend'],
                candle=result['candle_pattern'],
                rsi=result['rsi'],
                chart_path=chart_path
            )
            logger.info(f"  📱 Signal sent to Telegram")
        
        # Virtual trading
        if self.virtual_trading and self.trader:
            trade_id = self.trader.on_signal(
                pair=pair,
                signal=signal,
                price=result['price'],
                signal_data=result
            )
            if trade_id:
                logger.info(f"  🎮 Virtual trade opened: {trade_id}")
        
        # Update last signal
        self.last_signals[pair] = signal
        
        return result
    
    def run_analysis_cycle(self):
        """Run one analysis cycle"""
        results = []
        prices = {}  # Current prices for closing trades
        
        for pair in self.pairs:
            try:
                result = self.process_pair(pair)
                if result:
                    results.append(result)
                    prices[pair] = result['price']
            except Exception as e:
                logger.error(f"Error analyzing {pair}: {e}")
                continue
        
        # Update unrealized P&L for open trades
        if self.virtual_trading and self.trader:
            self.trader.update_prices(prices)
        
        return results
    
    def print_status(self):
        """Print current trading status"""
        if self.virtual_trading and self.trader:
            self.trader.journal.print_full_report()
    
    def run(self):
        """Main bot loop"""
        logger.info("🚀 Forex Trading Bot Started!")
        logger.info(f"📊 Monitoring: {', '.join(self.pairs)}")
        logger.info(f"🎮 Virtual Trading: {'ENABLED' if self.virtual_trading else 'DISABLED'}")
        logger.info(f"⏰ Check interval: {self.check_interval} seconds")
        
        try:
            while True:
                logger.info(f"\n{'='*60}")
                logger.info(f"Analysis Cycle - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'='*60}")
                
                results = self.run_analysis_cycle()
                
                # Print virtual trading status
                self.print_status()
                
                # Save results
                self.save_results(results)
                
                logger.info(f"\n⏰ Waiting {self.check_interval} seconds...")
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Bot stopped by user")
        except Exception as e:
            logger.error(f"Bot error: {e}")
            raise
    
    def save_results(self, results):
        """Save analysis results"""
        filename = f"{APP_FOLDER}/signals_{datetime.now().strftime('%Y%m%d')}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'results': results
            }, f, indent=2, default=str)
        
        logger.info(f"Results saved to {filename}")


# ==================== COMMAND LINE ====================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Forex Trading Bot')
    parser.add_argument('--novirtual', action='store_true', help='Disable virtual trading')
    parser.add_argument('--status', action='store_true', help='Show trading journal status')
    parser.add_argument('--reset', action='store_true', help='Reset virtual trading journal')
    parser.add_argument('--history', action='store_true', help='Show trade history')
    
    args = parser.parse_args()
    
    if args.reset:
        journal = TradingJournal()
        journal.reset()
        exit()
    
    if args.status:
        journal = TradingJournal()
        journal.print_full_report()
        exit()
    
    if args.history:
        journal = TradingJournal()
        journal.print_closed_trades(limit=20)
        exit()
    
    # Run bot
    bot = ForexTradingBot(virtual_trading=not args.novirtual)
    bot.run()
