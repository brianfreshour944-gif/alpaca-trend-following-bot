"""
FILE: universal_backtester.py
FUNCTION: Backtests the EMA crossover strategy using the REAL TradingEngine.
"""
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
from engine import TradingEngine

class TrendBacktester:
    def __init__(self, symbol, fast_p=9, slow_p=21, capital=1000, trade_size=0.1):
        self.symbol = symbol
        self.fast_p = fast_p
        self.slow_p = slow_p
        self.capital = capital
        self.trade_size = trade_size
        self.data = None

    def fetch_data(self, start_date, end_date):
        print(f"📥 Fetching {self.symbol} from {start_date} to {end_date}...")
        self.data = yf.download(self.symbol, start=start_date, end=end_date)
        if self.data.empty:
            print("❌ No data returned.")
        else:
            print(f"✅ Downloaded {len(self.data)} bars.")
        return self.data

    def run(self):
        if self.data is None or self.data.empty:
            return {}

        df = self.data.copy()
        engine = TradingEngine(fast_p=self.fast_p, slow_p=self.slow_p)

        cash = self.capital
        holdings = 0.0
        trades = []

        # Mock bar object that matches what engine.check_signal expects
        class MockBar:
            def __init__(self, symbol, close):
                self.symbol = symbol
                # Ensure close is a scalar
                self.close = float(close) if not isinstance(close, (pd.Series, pd.DataFrame)) else float(close.iloc[0])

        for idx, row in df.iterrows():
            bar = MockBar(self.symbol, row['Close'])
            signal = engine.check_signal(bar)
            price = float(row['Close']) if not isinstance(row['Close'], (pd.Series, pd.DataFrame)) else float(row['Close'].iloc[0])

            if signal == "BUY" and holdings == 0:
                cost = price * self.trade_size
                if cost <= cash:
                    cash -= cost
                    holdings = self.trade_size
                    trades.append({'type': 'BUY', 'price': price})
                    print(f"BUY at {price:.2f}")
            elif signal == "SELL" and holdings > 0:
                cash += price * holdings
                trades.append({'type': 'SELL', 'price': price})
                holdings = 0
                print(f"SELL at {price:.2f}")

        # Close any remaining position at last price
        if holdings > 0:
            last_price = float(df['Close'].iloc[-1])
            cash += last_price * holdings
            trades.append({'type': 'SELL (close)', 'price': last_price})
            holdings = 0

        net_profit = cash - self.capital

        # Metrics
        sell_trades = [t for t in trades if t['type'] in ('SELL', 'SELL (close)')]
        total_trades = len(sell_trades)

        buys = [t for t in trades if t['type'] == 'BUY']
        sells = [t for t in trades if t['type'] in ('SELL', 'SELL (close)')]
        profits = []
        for buy, sell in zip(buys, sells):
            pnl = (sell['price'] - buy['price']) * self.trade_size
            profits.append(pnl)

        win_rate = (sum(1 for p in profits if p > 0) / len(profits) * 100) if profits else 0.0

        # ---- Safe Sharpe and Drawdown ----
        daily_returns = df['Close'].pct_change().dropna()
        sharpe = 0.0
        if not daily_returns.empty:
            std = daily_returns.std()
            # Ensure scalar
            if hasattr(std, 'iloc'):
                std = std.iloc[0]
            if std != 0:
                sharpe = (daily_returns.mean() / std) * np.sqrt(252)

        cumulative = df['Close'].pct_change().cumsum().fillna(0)
        running_max = cumulative.expanding().max()
        denom = running_max.abs().replace(0, 1)
        drawdown = (cumulative - running_max) / denom
        max_drawdown_pct = drawdown.min() * 100 if not drawdown.empty else 0.0
        if hasattr(max_drawdown_pct, 'iloc'):
            max_drawdown_pct = max_drawdown_pct.iloc[0]

        print(f"\n📊 Backtest Results for {self.symbol}:")
        print(f"   Total Trades: {total_trades}")
        print(f"   Net Profit: ${net_profit:.2f}")
        print(f"   Win Rate: {win_rate:.2f}%")
        print(f"   Sharpe: {sharpe:.2f}")
        print(f"   Max Drawdown: {max_drawdown_pct:.2f}%")

        return {
            'total_trades': total_trades,
            'net_profit': net_profit,
            'win_rate': win_rate,
            'sharpe': sharpe,
            'max_drawdown_pct': max_drawdown_pct,
        }
