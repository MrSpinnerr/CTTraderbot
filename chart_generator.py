#!/usr/bin/env python3
"""
Chart Generator for Trading Bot
Creates chart images with technical analysis overlays
Files saved to Windows Desktop by default
"""

import os
import getpass
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from datetime import datetime

# ==================== WINDOWS PATHS ====================

try:
    WINDOWS_USER = os.environ.get('USERNAME', getpass.getuser())
except:
    WINDOWS_USER = 'user'

WINDOWS_DESKTOP = f"/mnt/c/Users/{WINDOWS_USER}/Desktop"
CHARTS_FOLDER = f"{WINDOWS_DESKTOP}/forex_trader_bot/charts"

# Create directory
os.makedirs(CHARTS_FOLDER, exist_ok=True)

class ChartGenerator:
    """Generate trading charts with analysis"""
    
    def __init__(self):
        self.charts_dir = CHARTS_FOLDER
        os.makedirs(self.charts_dir, exist_ok=True)
        
        # Configure matplotlib
        plt.style.use('dark_background')
        plt.rcParams['figure.facecolor'] = '#1a1a2e'
        plt.rcParams['axes.facecolor'] = '#1a1a2e'
        plt.rcParams['axes.edgecolor'] = '#444'
        plt.rcParams['text.color'] = '#fff'
        plt.rcParams['axes.labelcolor'] = '#aaa'
        plt.rcParams['xtick.color'] = '#888'
        plt.rcParams['ytick.color'] = '#888'
    
    def create_analysis_chart(self, pair, signal, save_path=None):
        """Create comprehensive analysis chart"""
        from analyzer import ForexAnalyzer
        
        analyzer = ForexAnalyzer()
        
        # Get data
        data = analyzer.get_price_data(pair, '1h', 100)
        if data is None:
            return None
        
        # Calculate indicators
        ema_20 = analyzer.calculate_ema(data['close'], 20)
        ema_50 = analyzer.calculate_ema(data['close'], 50)
        ema_200 = analyzer.calculate_ema(data['close'], 200) if len(data) >= 200 else ema_50
        
        # Get support/resistance
        sr = analyzer.find_support_resistance(data['close'])
        
        # Calculate RSI
        rsi = analyzer.calculate_rsi(data['close'], 14)
        
        # Create figure
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), 
                                        gridspec_kw={'height_ratios': [3, 1]})
        fig.patch.set_facecolor('#1a1a2e')
        
        # ===== PRICE CHART =====
        ax1.set_facecolor('#1a1a2e')
        
        # Plot candlesticks (simplified as line + fill)
        dates = range(len(data))
        ax1.plot(dates, data['close'], color='#2196F3', linewidth=1.5, label='Price')
        ax1.fill_between(dates, data['close'], alpha=0.1, color='#2196F3')
        
        # EMAs
        ax1.plot(dates, ema_20, color='#4CAF50', linewidth=1, label='EMA 20', alpha=0.8)
        ax1.plot(dates, ema_50, color='#FF9800', linewidth=1.5, label='EMA 50', alpha=0.8)
        ax1.plot(dates, ema_200, color='#F44336', linewidth=2, label='EMA 200', alpha=0.8)
        
        # Support/Resistance lines
        for sup in sr.get('support', [])[:3]:
            ax1.axhline(y=sup, color='#4CAF50', linestyle='--', alpha=0.5, linewidth=1)
        for res in sr.get('resistance', [])[:3]:
            ax1.axhline(y=res, color='#F44336', linestyle='--', alpha=0.5, linewidth=1)
        
        # Mark current price
        current_price = data['close'].iloc[-1]
        ax1.scatter([len(data)-1], [current_price], color='#FFD700', s=100, 
                   zorder=5, marker='*', label='Current')
        
        # Color based on signal
        signal_colors = {
            'BUY': '#4CAF50',
            'SELL': '#F44336', 
            'HOLD': '#FFC107'
        }
        color = signal_colors.get(signal['signal'], '#888')
        
        # Add signal annotation
        ax1.annotate(
            f"🚨 {signal['signal']}\n💰 {signal['price']:.5f}",
            xy=(len(data)-1, current_price),
            xytext=(len(data)-15, current_price * 1.005),
            fontsize=14,
            fontweight='bold',
            color=color,
            bbox=dict(boxstyle='round', facecolor='#222', edgecolor=color, alpha=0.9),
            arrowprops=dict(arrowstyle='->', color=color)
        )
        
        # Labels
        ax1.set_title(f"📈 {pair} - 1H Chart | Signal: {signal['signal']}", 
                     fontsize=14, fontweight='bold', color=color, pad=15)
        ax1.set_ylabel('Price', fontsize=11)
        ax1.legend(loc='upper left', fontsize=9)
        ax1.grid(True, alpha=0.2)
        
        # ===== RSI CHART =====
        ax2.set_facecolor('#1a1a2e')
        
        rsi_values = []
        for i in range(len(data)):
            rsi_val = analyzer.calculate_rsi(data['close'].iloc[:i+1], 14)
            rsi_values.append(rsi_val)
        
        ax2.plot(dates, rsi_values, color='#9C27B0', linewidth=1.5)
        ax2.axhline(y=70, color='#F44336', linestyle='--', alpha=0.5)
        ax2.axhline(y=30, color='#4CAF50', linestyle='--', alpha=0.5)
        ax2.axhline(y=50, color='#888', linestyle='-', alpha=0.3)
        ax2.fill_between(dates, rsi_values, 70, alpha=0.1, color='#F44336')
        ax2.fill_between(dates, rsi_values, 30, alpha=0.1, color='#4CAF50')
        
        ax2.set_ylim(0, 100)
        ax2.set_ylabel('RSI (14)', fontsize=11)
        ax2.set_xlabel('Periods (1H)', fontsize=11)
        ax2.grid(True, alpha=0.2)
        
        # Add RSI value
        ax2.annotate(f"RSI: {rsi:.1f}", 
                    xy=(len(data)-5, rsi), fontsize=10, color='#9C27B0')
        
        # ===== INFO BOX =====
        info_text = (
            f"🕐 {signal['timestamp'][:19]}\n"
            f"📊 Trend: {signal['trend']}\n"
            f"🎯 Position: {signal['position']}\n"
            f"🕯️ Pattern: {signal['candle_pattern']}\n"
            f"📉 RSI: {signal['rsi']:.1f}\n"
            f"📍 Support: {signal['support'][:2] if signal['support'] else 'N/A'}\n"
            f"📍 Resistance: {signal['resistance'][:2] if signal['resistance'] else 'N/A'}"
        )
        
        fig.text(0.02, 0.02, info_text, fontsize=9, 
                family='monospace', color='#aaa',
                bbox=dict(boxstyle='round', facecolor='#222', alpha=0.8))
        
        plt.tight_layout()
        
        # Save
        if save_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            save_path = f"{self.charts_dir}/{pair.replace('/', '_')}_{timestamp}.png"
        
        plt.savefig(save_path, dpi=100, facecolor='#1a1a2e', 
                   edgecolor='none', bbox_inches='tight')
        plt.close()
        
        return save_path


# Test chart generator
if __name__ == "__main__":
    print("🧪 Testing Chart Generator...")
    
    generator = ChartGenerator()
    
    # Sample signal data
    signal_data = {
        'pair': 'EUR/USD',
        'price': 1.0523,
        'trend': 'WEAK_UPTREND',
        'position': 'NEAR_SUPPORT',
        'support': [1.0480, 1.0450, 1.0400],
        'resistance': [1.0550, 1.0600, 1.0650],
        'candle_pattern': 'BULLISH_ENGULFING',
        'rsi': 42.5,
        'signal': 'BUY',
        'timestamp': datetime.now().isoformat()
    }
    
    chart_path = generator.create_analysis_chart('EUR/USD', signal_data)
    
    if chart_path:
        print(f"✅ Chart saved: {chart_path}")
    else:
        print("❌ Chart generation failed")
