#!/usr/bin/env python3
"""
Forex Trading Telegram WebApp
Runs as a web app inside Telegram with real-time charts and trading journal
Files saved to Windows Desktop by default
"""

import os
import json
import threading
import time
import getpass
from datetime import datetime
from flask import Flask, render_template, jsonify, request, redirect, url_for

app = Flask(__name__)

# ==================== WINDOWS PATHS ====================

try:
    WINDOWS_USER = os.environ.get('USERNAME', getpass.getuser())
except:
    WINDOWS_USER = 'user'

WINDOWS_DESKTOP = f"/mnt/c/Users/{WINDOWS_USER}/Desktop"
APP_FOLDER = f"{WINDOWS_DESKTOP}/forex_trader_bot"
DATA_FOLDER = f"{APP_FOLDER}/data"
CHARTS_FOLDER = f"{APP_FOLDER}/charts"

# Create directories
os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(CHARTS_FOLDER, exist_ok=True)

# File paths
JOURNAL_FILE = f'{DATA_FOLDER}/journal.json'
BALANCE_FILE = f'{DATA_FOLDER}/balance.json'

def load_journal():
    if os.path.exists(JOURNAL_FILE):
        with open(JOURNAL_FILE, 'r') as f:
            return json.load(f)
    return {'trades': [], 'next_id': 1}

def save_journal(data):
    with open(JOURNAL_FILE, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def load_balance():
    if os.path.exists(BALANCE_FILE):
        with open(BALANCE_FILE, 'r') as f:
            data = json.load(f)
            return data.get('balance', 10000.00)
    return 10000.00

def save_balance(balance):
    with open(BALANCE_FILE, 'w') as f:
        json.dump({'balance': balance}, f)

# ==================== TRADING LOGIC ====================

def open_trade(pair, direction, entry_price):
    """Open a virtual trade"""
    journal = load_journal()
    
    trade_id = f"TR{journal['next_id']:04d}"
    journal['next_id'] += 1
    
    trade = {
        'id': trade_id,
        'pair': pair,
        'direction': direction,
        'entry_price': entry_price,
        'entry_time': datetime.now().isoformat(),
        'status': 'OPEN',
        'exit_price': None,
        'exit_time': None,
        'pips': 0,
        'pnl': 0
    }
    
    journal['trades'].append(trade)
    save_journal(journal)
    
    return trade

def close_trade(trade_id, exit_price):
    """Close a virtual trade"""
    journal = load_journal()
    
    for trade in journal['trades']:
        if trade['id'] == trade_id and trade['status'] == 'OPEN':
            trade['exit_price'] = exit_price
            trade['exit_time'] = datetime.now().isoformat()
            trade['status'] = 'CLOSED'
            
            # Calculate P&L
            if trade['direction'] == 'BUY':
                trade['pips'] = round((exit_price - trade['entry_price']) * 10000, 1)
            else:
                trade['pips'] = round((trade['entry_price'] - exit_price) * 10000, 1)
            
            trade['pnl'] = round(trade['pips'] * 0.10, 2)  # $0.10 per pip
            
            # Update balance
            balance = load_balance()
            balance += trade['pnl']
            save_balance(balance)
            
            save_journal(journal)
            return trade
    
    return None

def get_stats():
    """Get trading statistics"""
    journal = load_journal()
    balance = load_balance()
    
    open_trades = [t for t in journal['trades'] if t['status'] == 'OPEN']
    closed_trades = [t for t in journal['trades'] if t['status'] == 'CLOSED']
    
    wins = len([t for t in closed_trades if t['pnl'] > 0])
    losses = len([t for t in closed_trades if t['pnl'] < 0])
    
    total_pnl = sum(t['pnl'] for t in closed_trades)
    win_rate = (wins / len(closed_trades) * 100) if closed_trades else 0
    
    return {
        'balance': round(balance, 2),
        'open_trades': len(open_trades),
        'total_trades': len(closed_trades),
        'wins': wins,
        'losses': losses,
        'win_rate': round(win_rate, 1),
        'total_pnl': round(total_pnl, 2),
        'trades': journal['trades'][-20:]  # Last 20 trades
    }

# ==================== FLASK ROUTES ====================

@app.route('/')
def index():
    """Main webapp page"""
    return render_template('index.html', page='dashboard')

@app.route('/dashboard')
def dashboard():
    """Dashboard with stats and charts"""
    stats = get_stats()
    return render_template('index.html', page='dashboard', stats=stats)

@app.route('/trades')
def trades():
    """Open and closed trades"""
    stats = get_stats()
    return render_template('index.html', page='trades', stats=stats)

@app.route('/analysis')
def analysis():
    """Live analysis of currency pairs"""
    return render_template('index.html', page='analysis')

@app.route('/settings')
def settings():
    """Settings page"""
    return render_template('index.html', page='settings')

# ==================== API ROUTES ====================

@app.route('/api/stats')
def api_stats():
    """Get trading stats"""
    return jsonify(get_stats())

@app.route('/api/open_trade', methods=['POST'])
def api_open_trade():
    """Open a new trade"""
    data = request.json
    trade = open_trade(
        pair=data['pair'],
        direction=data['direction'],
        entry_price=float(data['price'])
    )
    return jsonify({'success': True, 'trade': trade})

@app.route('/api/close_trade/<trade_id>', methods=['POST'])
def api_close_trade(trade_id):
    """Close a trade"""
    data = request.json
    trade = close_trade(trade_id, float(data['price']))
    if trade:
        return jsonify({'success': True, 'trade': trade})
    return jsonify({'success': False, 'error': 'Trade not found'})

@app.route('/api/reset', methods=['POST'])
def api_reset():
    """Reset journal"""
    save_journal({'trades': [], 'next_id': 1})
    save_balance(10000)
    return jsonify({'success': True})

# ==================== TELEGRAM BOT ====================

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')

def send_webapp_button(chat_id):
    """Send message with webapp button"""
    if not TELEGRAM_TOKEN:
        return False
    
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    url = os.environ.get('WEBAPP_URL', 'https://your-app.railway.app')
    
    keyboard = [
        [InlineKeyboardButton("📊 Open Trading App", web_app=WebAppInfo(url=url))]
    ]
    
    # This would be used with python-telegram-bot library
    # For now, just return the URL
    return url

# ==================== RUN ====================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
