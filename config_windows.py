#!/usr/bin/env python3
"""
Configuration - Windows Paths
All files saved to Windows Desktop by default
"""

import os
import getpass

# Detect Windows username
try:
    WINDOWS_USER = os.environ.get('USERNAME', getpass.getuser())
except:
    WINDOWS_USER = os.environ.get('USER', 'user')

# Windows paths
WINDOWS_DESKTOP = f"/mnt/c/Users/{WINDOWS_USER}/Desktop"
WINDOWS_DOCUMENTS = f"/mnt/c/Users/{WINDOWS_USER}/Documents"
WINDOWS_DOWNLOADS = f"/mnt/c/Users/{WINDOWS_USER}/Downloads"

# App directories on Windows
APP_FOLDER = f"{WINDOWS_DESKTOP}/forex_trader_bot"
CHARTS_FOLDER = f"{APP_FOLDER}/charts"
DATA_FOLDER = f"{APP_FOLDER}/data"

# Ensure directories exist
os.makedirs(CHARTS_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)

# Default file paths (Windows)
JOURNAL_FILE = f"{DATA_FOLDER}/journal.json"
BALANCE_FILE = f"{DATA_FOLDER}/balance.json"
CONFIG_FILE = f"{APP_FOLDER}/config.py"
LOG_FILE = f"{APP_FOLDER}/bot.log"

# Telegram credentials
TELEGRAM_BOT_TOKEN = os.environ.get('8113812075:AAF2dQuXRyC0XCGwIvYD34ioSJK96a7Ke14', '')
TELEGRAM_CHAT_ID = os.environ.get('5759195216', '')

# Currency pairs
PAIRS = [
    'EUR/USD',
    'GBP/USD', 
    'USD/JPY',
    'AUD/USD',
    'USD/CAD'
]

# Settings
CHECK_INTERVAL = 300  # 5 minutes
INITIAL_BALANCE = 10000.0
LOT_SIZE = 0.01
