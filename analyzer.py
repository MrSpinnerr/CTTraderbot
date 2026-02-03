#!/usr/bin/env python3
"""
Forex Technical Analyzer
Analyzes trends, support/resistance, candlesticks, and generates signals
"""

import numpy as np
import pandas as pd
import requests
from datetime import datetime, timedelta

class ForexAnalyzer:
    """Technical analysis for forex pairs"""
    
    def __init__(self):
        self.timeframes = {
            '1m': 1, '5m': 5, '15m': 15, '30m': 30,
            '1h': 60, '4h': 240, '1d': 1440
        }
    
    # ==================== DATA FETCHING ====================
    
    def get_price_data(self, pair, timeframe='1h', periods=100):
        """Fetch price data for a currency pair"""
        # Convert pair format (EUR/USD -> EURUSD)
        symbol = pair.replace('/', '')
        
        # Try free API first (Frankfurter)
        try:
            minutes = self.timeframes.get(timeframe, 60) * periods
            end = datetime.now()
            start = end - timedelta(minutes=minutes)
            
            url = f"https://api.frankfurter.app/{start.isoformat()}..{end.isoformat()}"
            params = {
                'from': pair[:3],
                'to': pair[4:],
                'interval': timeframe,
                'amount': 1
            }
            
            r = requests.get(url, params=params, timeout=30)
            if r.ok:
                data = r.json()
                rates = data.get('rates', {})
                
                if rates:
                    dates = list(rates.keys())
                    prices = [rates[d].get(pair[4:], d) for d in dates]
                    
                    df = pd.DataFrame({
                        'open': prices,
                        'high': prices,
                        'low': prices,
                        'close': prices,
                        'volume': [0] * len(prices)
                    }, index=pd.to_datetime(dates))
                    
                    return df.tail(periods)
                    
        except Exception as e:
            print(f"Frankfurter API error: {e}")
        
        # Fallback: generate realistic sample data for testing
        print(f"Using sample data for {pair}")
        return self._generate_sample_data(periods)
    
    def _generate_sample_data(self, periods=100):
        """Generate sample price data for testing"""
        import random
        
        base_price = {
            'EURUSD': 1.0500, 'GBPUSD': 1.2700, 'USDJPY': 155.00,
            'AUDUSD': 0.6500, 'USDCAD': 1.3500, 'EURGBP': 0.8500,
            'USDCHF': 0.8800
        }
        
        pair = 'EURUSD'  # default
        price = base_price.get(pair, 1.0)
        
        # Generate realistic random walk
        np.random.seed(42)  # Reproducible
        returns = np.random.normal(0.0001, 0.003, periods)  # Daily ~1% vol
        prices = price * (1 + returns).cumsum()
        
        df = pd.DataFrame({
            'open': prices * (1 + np.random.normal(0, 0.001, periods)),
            'high': prices * (1 + np.abs(np.random.normal(0, 0.002, periods))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.002, periods))),
            'close': prices,
            'volume': np.random.randint(1000, 10000, periods)
        }, index=pd.date_range(end=datetime.now(), periods=periods, freq='1h'))
        
        return df
    
    # ==================== TREND ANALYSIS ====================
    
    def calculate_ema(self, close, period):
        """Calculate Exponential Moving Average"""
        return close.ewm(span=period, adjust=False).mean()
    
    def get_trend(self, data, ema_fast=20, ema_slow=50, ema_trend=200):
        """Determine market trend direction"""
        close = data['close']
        
        ema_20 = self.calculate_ema(close, ema_fast)
        ema_50 = self.calculate_ema(close, ema_slow)
        ema_200 = self.calculate_ema(close, ema_trend) if len(close) >= 200 else ema_50
        
        current_price = close.iloc[-1]
        
        # Trend determination
        if current_price > ema_200.iloc[-1] and ema_50.iloc[-1] > ema_200.iloc[-1]:
            return 'STRONG_UPTREND'
        elif current_price > ema_200.iloc[-1]:
            return 'WEAK_UPTREND'
        elif current_price < ema_200.iloc[-1] and ema_50.iloc[-1] < ema_200.iloc[-1]:
            return 'STRONG_DOWNTREND'
        elif current_price < ema_200.iloc[-1]:
            return 'WEAK_DOWNTREND'
        else:
            return 'RANGE_BOUND'
    
    # ==================== SUPPORT/RESISTANCE ====================
    
    def find_support_resistance(self, close, num_levels=5):
        """Find support and resistance levels"""
        prices = close.values
        
        # Use percentiles for rough levels
        supports = []
        resistances = []
        
        # Simple approach: find local min/max
        window = 10
        
        local_mins = []
        local_maxs = []
        
        for i in range(window, len(prices) - window):
            if all(prices[i] <= prices[i+j] for j in range(-window, window+1) if j != 0):
                local_mins.append(prices[i])
            if all(prices[i] >= prices[i+j] for j in range(-window, window+1) if j != 0):
                local_maxs.append(prices[i])
        
        # Cluster similar levels
        def cluster_levels(levels, num_clusters):
            if len(levels) < num_clusters:
                return sorted(levels)
            
            # Simple binning
            min_p, max_p = min(levels), max(levels)
            step = (max_p - min_p) / num_clusters
            
            clustered = []
            for i in range(num_clusters):
                bin_levels = [l for l in levels if min_p + i*step <= l < min_p + (i+1)*step]
                if bin_levels:
                    clustered.append(sum(bin_levels) / len(bin_levels))
            
            return sorted(clustered)
        
        supports = cluster_levels(local_mins, num_levels//2)[:3]
        resistances = cluster_levels(local_maxs, num_levels//2)[:3]
        
        return {
            'support': supports,
            'resistance': resistances,
            'nearest_support': min(supports) if supports else None,
            'nearest_resistance': min(resistances) if resistances else None
        }
    
    def get_price_position(self, price, sr_levels):
        """Determine if price is at support, resistance, or neutral"""
        nearest_sup = sr_levels.get('nearest_support')
        nearest_res = sr_levels.get('nearest_resistance')
        
        if nearest_sup is None or nearest_res is None:
            return 'NEUTRAL'
        
        # Calculate distance as percentage
        sup_dist = (price - nearest_sup) / price * 100
        res_dist = (nearest_res - price) / price * 100
        
        if sup_dist < 0.5:
            return 'AT_SUPPORT'
        elif res_dist < 0.5:
            return 'AT_RESISTANCE'
        elif sup_dist < 2:
            return 'NEAR_SUPPORT'
        elif res_dist < 2:
            return 'NEAR_RESISTANCE'
        else:
            return 'NEUTRAL'
    
    # ==================== CANDLESTICK PATTERNS ====================
    
    def get_candle_patterns(self, data):
        """Detect candlestick patterns"""
        o = data['open'].iloc[-1]
        h = data['high'].iloc[-1]
        l = data['low'].iloc[-1]
        c = data['close'].iloc[-1]
        
        body = abs(c - o)
        upper_shadow = h - max(o, c)
        lower_shadow = min(o, c) - l
        body_size = body if body > 0.0001 else 0.0001
        
        # Calculate for previous candle too
        po = data['open'].iloc[-2]
        pc = data['close'].iloc[-2]
        pbody = abs(pc - po)
        
        patterns = []
        
        # Doji
        if upper_shadow > body * 3 and lower_shadow > body * 3:
            patterns.append('DOJI')
        
        # Hammer (bullish)
        if lower_shadow > body * 2 and upper_shadow < body * 0.5 and c > o:
            patterns.append('BULLISH_HAMMER')
        
        # Inverted Hammer
        if upper_shadow > body * 2 and lower_shadow < body * 0.5 and c > o:
            patterns.append('INVERTED_HAMMER')
        
        # Shooting Star (bearish)
        if upper_shadow > body * 2 and lower_shadow < body * 0.5 and c < o:
            patterns.append('SHOOTING_STAR')
        
        # Bullish Engulfing
        if c > o and pc < po and c > po and o < pc:
            patterns.append('BULLISH_ENGULFING')
        
        # Bearish Engulfing
        if c < o and pc > po and c < po and o > pc:
            patterns.append('BEARISH_ENGULFING')
        
        # Morning Star (3 candles)
        if len(data) >= 3:
            c1 = data['close'].iloc[-3]
            o1 = data['open'].iloc[-3]
            c2 = data['close'].iloc[-2]
            o2 = data['open'].iloc[-2]
            
            if c1 < o1 and abs(c2-o2) < abs(c1-o1)*0.3 and c > o and c > (o1+c1)/2:
                patterns.append('MORNING_STAR')
        
        # Evening Star (3 candles)
        if len(data) >= 3:
            c1 = data['close'].iloc[-3]
            o1 = data['open'].iloc[-3]
            c2 = data['close'].iloc[-2]
            o2 = data['open'].iloc[-2]
            
            if c1 > o1 and abs(c2-o2) < abs(c1-o1)*0.3 and c < o and c < (o1+c1)/2:
                patterns.append('EVENING_STAR')
        
        # Three White Soldiers (3 bullish candles)
        if len(data) >= 3:
            if all(data['close'].iloc[-3+i] > data['open'].iloc[-3+i] for i in range(3)):
                if all(data['close'].iloc[-3+i] > data['close'].iloc[-4+i] for i in range(3)):
                    patterns.append('THREE_WHITE_SOLDIERS')
        
        return patterns[0] if patterns else 'NONE'
    
    # ==================== MOMENTUM ====================
    
    def calculate_rsi(self, close, period=14):
        """Calculate Relative Strength Index"""
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1] if not rsi.empty else 50
    
    # ==================== SIGNAL GENERATION ====================
    
    def generate_signal(self, trend, price_position, candle_pattern, rsi, 
                        strategies=None):
        """
        Generate trading signal based on combined strategies
        
        Strategy: IF (Trend UP) AND (Price at support) AND (Bullish candle) THEN BUY
        """
        if strategies is None:
            strategies = {
                'trend': True,
                'support_resistance': True,
                'candles': True,
                'rsi': True
            }
        
        bullish_patterns = [
            'BULLISH_HAMMER', 'BULLISH_ENGULFING', 'MORNING_STAR',
            'THREE_WHITE_SOLDIERS', 'INVERTED_HAMMER'
        ]
        
        bearish_patterns = [
            'SHOOTING_STAR', 'BEARISH_ENGULFING', 'EVENING_STAR'
        ]
        
        score = 0
        reasons = []
        
        # Trend analysis
        if strategies.get('trend', False):
            if 'UPTREND' in trend:
                score += 1
                reasons.append('Uptrend')
            elif 'DOWNTREND' in trend:
                score -= 1
                reasons.append('Downtrend')
        
        # Support/Resistance
        if strategies.get('support_resistance', False):
            if price_position == 'AT_SUPPORT':
                score += 1
                reasons.append('At support')
            elif price_position == 'NEAR_SUPPORT':
                score += 0.5
                reasons.append('Near support')
            elif price_position == 'AT_RESISTANCE':
                score -= 1
                reasons.append('At resistance')
        
        # Candle patterns
        if strategies.get('candles', False):
            if candle_pattern in bullish_patterns:
                score += 1
                reasons.append(f'{candle_pattern}')
            elif candle_pattern in bearish_patterns:
                score -= 1
                reasons.append(f'{candle_pattern}')
        
        # RSI
        if strategies.get('rsi', False):
            if rsi < 35:
                score += 0.5
                reasons.append('RSI oversold')
            elif rsi > 65:
                score -= 0.5
                reasons.append('RSI overbought')
        
        # Final signal
        if score >= 2:
            return 'BUY', score, reasons
        elif score <= -2:
            return 'SELL', score, reasons
        else:
            return 'HOLD', score, reasons


# Test the analyzer
if __name__ == "__main__":
    analyzer = ForexAnalyzer()
    
    print("🧪 Testing Forex Analyzer...")
    
    # Get data
    data = analyzer.get_price_data('EUR/USD', '1h', 100)
    print(f"\n📊 Data loaded: {len(data)} periods")
    
    # Analyze
    trend = analyzer.get_trend(data)
    print(f"📈 Trend: {trend}")
    
    sr = analyzer.find_support_resistance(data['close'])
    print(f"📍 Support: {sr['support'][:2]}")
    print(f"📍 Resistance: {sr['resistance'][:2]}")
    
    position = analyzer.get_price_position(data['close'].iloc[-1], sr)
    print(f"🎯 Position: {position}")
    
    candle = analyzer.get_candle_patterns(data)
    print(f"🕯️ Candle: {candle}")
    
    rsi = analyzer.calculate_rsi(data['close'])
    print(f"📉 RSI: {rsi:.1f}")
    
    signal, score, reasons = analyzer.generate_signal(
        trend=trend,
        price_position=position,
        candle_pattern=candle,
        rsi=rsi
    )
    
    print(f"\n🎯 Signal: {signal} (score: {score})")
    print(f"📝 Reasons: {', '.join(reasons)}")
