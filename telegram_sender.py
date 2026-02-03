#!/usr/bin/env python3
"""
Telegram Signal Sender
Sends trading signals to Telegram with chart screenshots
"""

import os
import requests
from datetime import datetime

class TelegramSender:
    """Send trading signals to Telegram"""
    
    def __init__(self):
        self.token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
        self.chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.enabled = bool(self.token and self.chat_id)
    
    def send_message(self, text, parse_mode='HTML'):
        """Send text message to Telegram"""
        if not self.enabled:
            print(f"📱 Telegram (disabled): {text[:100]}...")
            return False
        
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': parse_mode
            }
            r = requests.post(url, json=data, timeout=10)
            return r.ok
        except Exception as e:
            print(f"❌ Telegram error: {e}")
            return False
    
    def send_photo(self, photo_path, caption=''):
        """Send photo with caption to Telegram"""
        if not self.enabled:
            print(f"📷 Telegram (disabled): {caption[:50]}...")
            return False
        
        try:
            url = f"{self.base_url}/sendPhoto"
            data = {
                'chat_id': self.chat_id,
                'caption': caption,
                'parse_mode': 'HTML'
            }
            files = {'photo': open(photo_path, 'rb')}
            r = requests.post(url, data=data, files=files, timeout=30)
            return r.ok
        except Exception as e:
            print(f"❌ Telegram photo error: {e}")
            return False
    
    def send_signal(self, pair, signal, price, trend, candle, rsi, chart_path=None):
        """Send complete trading signal with chart"""
        
        # Signal emojis
        signal_emoji = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '🟡'}
        emoji = signal_emoji.get(signal, '⚪')
        
        # Build message
        message = f"""
{emoji} <b>FOREX SIGNAL</b>

🏷️ <b>{pair}</b>
💰 <b>Price:</b> {price:.5f}
🎯 <b>SIGNAL:</b> {signal}

📊 <b>Analysis:</b>
• Trend: {trend}
• Candle: {candle}
• RSI: {rsi:.1f}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
        
        # Send message first
        self.send_message(message)
        
        # Send chart if available
        if chart_path and os.path.exists(chart_path):
            caption = f"{pair} - {signal} Signal at {price:.5f}"
            self.send_photo(chart_path, caption)
        
        return True
    
    def send_daily_summary(self, results):
        """Send daily analysis summary"""
        buy_pairs = [r for r in results if r['signal'] == 'BUY']
        sell_pairs = [r for r in results if r['signal'] == 'SELL']
        hold_pairs = [r for r in results if r['signal'] == 'HOLD']
        
        message = f"""
📊 <b>DAILY FOREX SUMMARY</b>

🟢 <b>BUY Signals:</b> {len(buy_pairs)}
{', '.join([r['pair'] for r in buy_pairs]) if buy_pairs else 'None'}

🔴 <b>SELL Signals:</b> {len(sell_pairs)}
{', '.join([r['pair'] for r in sell_pairs]) if sell_pairs else 'None'}

🟡 <b>HOLD:</b> {len(hold_pairs)}
{', '.join([r['pair'] for r in hold_pairs]) if hold_pairs else 'None'}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
        
        self.send_message(message)
        return True


# Test Telegram sender
if __name__ == "__main__":
    print("🧪 Testing Telegram Sender...")
    
    sender = TelegramSender()
    
    if sender.enabled:
        print("✅ Telegram configured")
        # Test send
        sender.send_signal(
            pair='EUR/USD',
            signal='BUY',
            price=1.0523,
            trend='WEAK_UPTREND',
            candle='BULLISH_ENGULFING',
            rsi=42.5
        )
    else:
        print("⚠️ Telegram not configured (missing token/chat_id)")
        print("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
