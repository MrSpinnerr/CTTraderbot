#!/usr/bin/env python3
"""Configuration for Forex Trading Bot"""

import os
from pathlib import Path

class Config:
    """Configuration manager"""
    
    def __init__(self):
        self.config_file = os.environ.get('FOREX_BOT_CONFIG', 
                                          '/home/user/clawd/forex_trader_bot/config.json')
        self._config = self._load_config()
    
    def _load_config(self):
        """Load config from file or create default"""
        default = {
            # Telegram settings
            'telegram': {
                'bot_token': os.environ.get('TELEGRAM_BOT_TOKEN', ''),
                'chat_id': os.environ.get('TELEGRAM_CHAT_ID', ''),
                'enabled': True
            },
            
            # Trading settings
            'pairs': [
                'EUR/USD',
                'GBP/USD', 
                'USD/JPY',
                'AUD/USD',
                'USD/CAD',
                'EUR/GBP',
                'USD/CHF'
            ],
            
            # Analysis settings
            'timeframe': '1h',
            'ema_fast': 20,
            'ema_slow': 50,
            'ema_trend': 200,
            'rsi_period': 14,
            'rsi_oversold': 35,
            'rsi_overbought': 65,
            
            # Strategy settings
            'strategies': {
                'trend': True,
                'support_resistance': True,
                'candles': True,
                'rsi': True
            },
            
            # Bot settings
            'check_interval': 300,  # seconds
            'debug': False
        }
        
        # Try to load from file
        if os.path.exists(self.config_file):
            try:
                import json
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                    default.update(file_config)
            except:
                pass
        
        return default
    
    def get(self, key, default=None):
        """Get config value using dot notation"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key, value):
        """Set config value"""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        
        # Save to file
        try:
            import json
            with open(self.config_file, 'w') as f:
                json.dump(self._config, f, indent=2)
        except:
            pass
    
    def save(self):
        """Save current config"""
        try:
            import json
            with open(self.config_file, 'w') as f:
                json.dump(self._config, f, indent=2)
            return True
        except:
            return False

# Quick config checker
if __name__ == "__main__":
    config = Config()
    print("\n📋 Current Configuration:")
    print(f"  Telegram enabled: {config.get('telegram.enabled')}")
    print(f"  Pairs: {config.get('pairs')}")
    print(f"  Check interval: {config.get('check_interval')}s")
    print(f"  Trend EMA: {config.get('ema_trend')}")
    print()
