#!/usr/bin/env python3
"""
Virtual Trading Journal
Tracks all paper trades with unique IDs, P&L, and history
Files saved to Windows Desktop by default
"""

import json
import os
import getpass
from datetime import datetime
from pathlib import Path

# ==================== WINDOWS PATHS ====================

try:
    WINDOWS_USER = os.environ.get('USERNAME', getpass.getuser())
except:
    WINDOWS_USER = 'user'

WINDOWS_DESKTOP = f"/mnt/c/Users/{WINDOWS_USER}/Desktop"
APP_FOLDER = f"{WINDOWS_DESKTOP}/forex_trader_bot"
DATA_FOLDER = f"{APP_FOLDER}/data"

# Create directories
os.makedirs(DATA_FOLDER, exist_ok=True)

class TradingJournal:
    """Virtual trading journal with tracking"""
    
    def __init__(self, balance=10000):
        self.journal_file = f'{DATA_FOLDER}/journal.json'
        self.balance_file = f'{DATA_FOLDER}/balance.json'
        
        # Load or initialize
        self.trades = self._load_trades()
        self.balance = self._load_balance(balance)
        
        # Trade counter for unique IDs
        self.trade_counter = len(self.trades) + 1
    
    def _load_trades(self):
        """Load trades from file"""
        if os.path.exists(self.journal_file):
            try:
                with open(self.journal_file, 'r') as f:
                    return json.load(f)
            except:
                return {'trades': []}
        return {'trades': []}
    
    def _save_trades(self):
        """Save trades to file"""
        with open(self.journal_file, 'w') as f:
            json.dump(self.trades, f, indent=2, default=str)
    
    def _load_balance(self, default):
        """Load virtual balance"""
        if os.path.exists(self.balance_file):
            try:
                with open(self.balance_file, 'r') as f:
                    data = json.load(f)
                    return data.get('balance', default)
            except:
                return default
        return default
    
    def _save_balance(self):
        """Save balance"""
        with open(self.balance_file, 'w') as f:
            json.dump({'balance': self.balance}, f)
    
    # ==================== TRADE MANAGEMENT ====================
    
    def open_trade(self, pair, direction, entry_price, signal_info, lot_size=0.01):
        """Open a new virtual trade"""
        trade_id = f"TR{self.trade_counter:04d}"
        self.trade_counter += 1
        
        trade = {
            'id': trade_id,
            'pair': pair,
            'direction': direction,  # BUY or SELL
            'entry_price': entry_price,
            'entry_time': datetime.now().isoformat(),
            'lot_size': lot_size,
            'signal_info': signal_info,  # trend, candle, rsi, etc.
            'status': 'OPEN',
            'exit_price': None,
            'exit_time': None,
            'exit_reason': None,
            'pips': 0,
            'pnl': 0,
            'notes': ''
        }
        
        self.trades['trades'].append(trade)
        self._save_trades()
        
        return trade_id
    
    def close_trade(self, trade_id, exit_price, reason='MANUAL'):
        """Close an open trade"""
        for trade in self.trades['trades']:
            if trade['id'] == trade_id and trade['status'] == 'OPEN':
                trade['exit_price'] = exit_price
                trade['exit_time'] = datetime.now().isoformat()
                trade['exit_reason'] = reason
                trade['status'] = 'CLOSED'
                
                # Calculate P&L
                if trade['direction'] == 'BUY':
                    trade['pips'] = round((exit_price - trade['entry_price']) * 10000, 1)
                else:  # SELL
                    trade['pips'] = round((trade['entry_price'] - exit_price) * 10000, 1)
                
                # Calculate $ P&L (approximate: 1 pip = $0.10 for 0.01 lot)
                trade['pnl'] = round(trade['pips'] * trade['lot_size'] * 10, 2)
                
                # Update balance
                self.balance += trade['pnl']
                self._save_balance()
                self._save_trades()
                
                return trade
        
        return None
    
    def close_all_at_market(self, current_prices):
        """Close all trades at current market prices"""
        closed = []
        for trade in self.trades['trades']:
            if trade['status'] == 'OPEN' and trade['pair'] in current_prices:
                current_price = current_prices[trade['pair']]
                result = self.close_trade(trade['id'], current_price, 'MARKET_CLOSE')
                if result:
                    closed.append(trade['id'])
        return closed
    
    # ==================== TRACKING ====================
    
    def get_open_trades(self):
        """Get all open trades"""
        return [t for t in self.trades['trades'] if t['status'] == 'OPEN']
    
    def get_closed_trades(self):
        """Get all closed trades"""
        return [t for t in self.trades['trades'] if t['status'] == 'CLOSED']
    
    def get_trade(self, trade_id):
        """Get specific trade"""
        for trade in self.trades['trades']:
            if trade['id'] == trade_id:
                return trade
        return None
    
    def get_stats(self):
        """Calculate trading statistics"""
        closed = self.get_closed_trades()
        open_trades = self.get_open_trades()
        
        if not closed:
            return {
                'total_trades': 0,
                'wins': 0,
                'losses': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'open_trades': len(open_trades),
                'balance': self.balance
            }
        
        wins = [t for t in closed if t['pnl'] > 0]
        losses = [t for t in closed if t['pnl'] < 0]
        
        total_pnl = sum(t['pnl'] for t in closed)
        win_rate = (len(wins) / len(closed)) * 100 if closed else 0
        
        return {
            'total_trades': len(closed),
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': round(win_rate, 1),
            'total_pnl': round(total_pnl, 2),
            'open_trades': len(open_trades),
            'balance': round(self.balance, 2),
            'best_trade': max(closed, key=lambda x: x['pnl'], default=None),
            'worst_trade': min(closed, key=lambda x: x['pnl'], default=None)
        }
    
    # ==================== FORMATTED OUTPUT ====================
    
    def print_status(self):
        """Print current status"""
        stats = self.get_stats()
        open_trades = self.get_open_trades()
        
        print(f"\n{'='*70}")
        print(f"  📊 VIRTUAL TRADING JOURNAL")
        print(f"{'='*70}")
        
        print(f"\n💰 VIRTUAL BALANCE: ${stats['balance']:.2f}")
        
        print(f"\n📈 STATISTICS:")
        print(f"   Total Trades: {stats['total_trades']}")
        print(f"   Wins: {stats['wins']} | Losses: {stats['losses']}")
        print(f"   Win Rate: {stats['win_rate']}%")
        print(f"   Total P&L: ${stats['total_pnl']:.2f}")
        
        print(f"\n🔴 OPEN TRADES ({len(open_trades)}):")
        print(f"   {'ID':<8} {'Pair':<10} {'Dir':<6} {'Entry':<10} {'Current':<10} {'P/L':<10}")
        print(f"   {'-'*54}")
        
        for trade in open_trades:
            entry = trade['entry_price']
            direction = trade['direction']
            print(f"   {trade['id']:<8} {trade['pair']:<10} {direction:<6} {entry:<10} {'---':<10} {'---':<10}")
        
        if not open_trades:
            print("   No open trades")
        
        print()
    
    def print_closed_trades(self, limit=10):
        """Print recent closed trades"""
        closed = self.get_closed_trades()[-limit:]
        
        print(f"\n🟢 RECENT CLOSED TRADES:")
        print(f"   {'ID':<8} {'Pair':<8} {'Dir':<5} {'Entry':<10} {'Exit':<10} {'Pips':<8} {'P/L':<10}")
        print(f"   {'-'*59}")
        
        for trade in reversed(closed):
            pnl_emoji = '🟢' if trade['pnl'] > 0 else '🔴' if trade['pnl'] < 0 else '⚪'
            print(f"   {trade['id']:<8} {trade['pair']:<8} {trade['direction']:<5} "
                  f"{trade['entry_price']:<10} {trade['exit_price']:<10} "
                  f"{trade['pips']:<8} {pnl_emoji} ${trade['pnl']:.2f}")
        
        print()
    
    def print_full_report(self):
        """Print complete trading report"""
        stats = self.get_stats()
        self.print_status()
        self.print_closed_trades()
        
        if stats.get('best_trade'):
            t = stats['best_trade']
            print(f"🏆 BEST TRADE: {t['id']} ({t['pair']}) - ${t['pnl']:.2f}")
        
        if stats.get('worst_trade'):
            t = stats['worst_trade']
            print(f"📉 WORST TRADE: {t['id']} ({t['pair']}) - ${t['pnl']:.2f}")
        
        print()
    
    def reset(self, new_balance=10000):
        """Reset journal (delete all trades)"""
        self.trades = {'trades': []}
        self.balance = new_balance
        self._save_trades()
        self._save_balance()
        print(f"✅ Journal reset. New balance: ${new_balance}")


# ==================== INTEGRATION WITH MAIN BOT ====================

class VirtualTrader:
    """Virtual trader that auto-executes signals"""
    
    def __init__(self, initial_balance=10000):
        self.journal = TradingJournal(initial_balance)
        self.analyzer = None  # Will be set from main
    
    def on_signal(self, pair, signal, price, signal_data):
        """Handle incoming signal"""
        if signal == 'HOLD':
            return
        
        open_trades = self.journal.get_open_trades()
        pair_trades = [t for t in open_trades if t['pair'] == pair]
        
        if signal == 'BUY':
            # Close any SELL trades on this pair
            for trade in pair_trades:
                if trade['direction'] == 'SELL':
                    self.journal.close_trade(trade['id'], price, 'REVERSED')
            
            # Open new BUY if none exists
            if not any(t['direction'] == 'BUY' for t in pair_trades):
                trade_id = self.journal.open_trade(
                    pair=pair,
                    direction='BUY',
                    entry_price=price,
                    signal_info=signal_data,
                    lot_size=0.01
                )
                return trade_id
        
        elif signal == 'SELL':
            # Close any BUY trades on this pair
            for trade in pair_trades:
                if trade['direction'] == 'BUY':
                    self.journal.close_trade(trade['id'], price, 'REVERSED')
            
            # Open new SELL if none exists
            if not any(t['direction'] == 'SELL' for t in pair_trades):
                trade_id = self.journal.open_trade(
                    pair=pair,
                    direction='SELL',
                    entry_price=price,
                    signal_info=signal_data,
                    lot_size=0.01
                )
                return trade_id
    
    def update_prices(self, prices):
        """Update with current prices (for tracking unrealized P&L)"""
        open_trades = self.journal.get_open_trades()
        for trade in open_trades:
            if trade['pair'] in prices:
                current = prices[trade['pair']]
                if trade['direction'] == 'BUY':
                    unrealized = (current - trade['entry_price']) * 10000 * trade['lot_size'] * 10
                else:
                    unrealized = (trade['entry_price'] - current) * 10000 * trade['lot_size'] * 10
                # Note: We don't save unrealized to balance, just track it


# Test the journal
if __name__ == "__main__":
    journal = TradingJournal()
    
    print("🧪 Testing Trading Journal...")
    
    # Open some test trades
    print("\n📝 Opening test trades...")
    id1 = journal.open_trade('EUR/USD', 'BUY', 1.0523, {'trend': 'UPTREND', 'candle': 'HAMMER'})
    id2 = journal.open_trade('GBP/USD', 'SELL', 1.2675, {'trend': 'DOWNTREND', 'candle': 'DOJI'})
    print(f"Opened: {id1}, {id2}")
    
    # Close one
    print("\n🔴 Closing EUR/USD at 1.0545...")
    journal.close_trade(id1, 1.0545, 'TAKE_PROFIT')
    
    # Print status
    journal.print_full_report()
