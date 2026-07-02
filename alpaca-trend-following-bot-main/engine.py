"""
FILE: engine.py
FUNCTION: The Analytical Brain.
Contains pure logic for technical analysis and signal generation.
Processes streaming bar objects and manages historical windows for calculations.
"""
import pandas as pd
from collections import defaultdict

class TradingEngine:
    def __init__(self, fast_p=9, slow_p=21):
        self.fast_p = fast_p
        self.slow_p = slow_p
        # Maintain a rolling history window of closing prices for each symbol
        self.history = defaultdict(list)
        # Limit history size to prevent memory leaks (keep double what the slow EMA needs)
        self.max_history = slow_p * 2 

    def check_signal(self, bar):
        """
        Processes an incoming bar object, updates the rolling historical sequence,
        and evaluates if an EMA cross (Golden Cross / Death Cross) has occurred.
        """
        # Try to extract the symbol name safely from the Alpaca bar object attributes
        symbol = getattr(bar, 'symbol', 'UNKNOWN')
        close_price = float(bar.close)
        
        # 1. Append the latest close price to this symbol's history cache
        self.history[symbol].append(close_price)
        
        # Enforce history boundary limits
        if len(self.history[symbol]) > self.max_history:
            self.history[symbol].pop(0)
            
        # 2. Guard clause: Ensure we have enough data points to compute a valid slow EMA
        if len(self.history[symbol]) < self.slow_p:
            print(f"📊 [{symbol}] Gathering history... ({len(self.history[symbol])}/{self.slow_p} bars)")
            return "HOLD"
            
        # 3. Compute EMA values using your pandas configuration
        closes = self.history[symbol]
        fast_ema = pd.Series(closes).ewm(span=self.fast_p, adjust=False).mean()
        slow_ema = pd.Series(closes).ewm(span=self.slow_p, adjust=False).mean()
        
        # Grab current values
        current_fast = fast_ema.iloc[-1]
        current_slow = slow_ema.iloc[-1]
        
        # Grab previous step values to detect crossover trajectory
        prev_fast = fast_ema.iloc[-2]
        prev_slow = slow_ema.iloc[-2]
        
        # 4. Evaluate Crossover Strategies
        # Fast EMA crosses ABOVE Slow EMA -> Golden Cross (Bullish Momentum)
        if prev_fast <= prev_slow and current_fast > current_slow:
            return "BUY"
            
        # Fast EMA crosses BELOW Slow EMA -> Death Cross (Bearish Momentum)
        elif prev_fast >= prev_slow and current_fast < current_slow:
            return "SELL"
            
        return "HOLD"

    @staticmethod
    def calculate_emas(closes, fast_p=9, slow_p=21):
        """ Retained standard utility method for backwards compatibility """
        fast_ema = pd.Series(closes).ewm(span=fast_p, adjust=False).mean()
        slow_ema = pd.Series(closes).ewm(span=slow_p, adjust=False).mean()
        return fast_ema.iloc[-1], slow_ema.iloc[-1], fast_ema.iloc[-2], slow_ema.iloc[-2]
