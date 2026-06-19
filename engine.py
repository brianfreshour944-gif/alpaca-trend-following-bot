"""
FILE: engine.py
FUNCTION: The Analytical Brain.
Contains pure logic for technical analysis and signal generation.
No external API dependencies; it only processes data provided to it.
"""
"""
FILE: engine.py
FUNCTION: Pure mathematical logic for indicators and signals.
"""
import pandas as pd

class TradingEngine:
    @staticmethod
    def calculate_emas(closes, fast_p=9, slow_p=21):
        fast_ema = pd.Series(closes).ewm(span=fast_p, adjust=False).mean()
        slow_ema = pd.Series(closes).ewm(span=slow_p, adjust=False).mean()
        return fast_ema.iloc[-1], slow_ema.iloc[-1], fast_ema.iloc[-2], slow_ema.iloc[-2]
