"""
FILE: run_all_backtests.py
FUNCTION: Runs backtests for Alpaca trend bots and saves results to DB.
"""
from universal_backtester import TrendBacktester
from datetime import datetime, date
import database as db  # Uses your bot's database.py (has get_db_connection)

def save_backtest_result(bot_name, strategy_name, start_date, end_date, results):
    """Insert a single backtest result into the database."""
    try:
        with db.get_db_connection() as conn, conn.cursor() as cur:
            cur.execute("""
                INSERT INTO backtest_results 
                (bot_name, strategy_name, start_date, end_date, total_trades, net_profit, sharpe_ratio, max_drawdown_pct, win_rate)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                bot_name,
                strategy_name,
                start_date,
                end_date,
                results['total_trades'],
                results['net_profit'],
                round(results['sharpe'], 2),
                round(results['max_drawdown_pct'], 2),
                round(results['win_rate'], 2)
            ))
            conn.commit()
        print(f"✅ Inserted backtest for {bot_name}")
    except Exception as e:
        print(f"❌ Failed to insert for {bot_name}: {e}")

def run_all_trend_backtests():
    # ===== ONLY YOUR 2 ALPACA BOTS =====
    bots = [
        {
            "bot_name": "Grok_alpaca_Apex_v8.py",
            "symbol": "BTC-USD",
            "fast": 9,
            "slow": 21,
            "capital": 1000,
            "trade_size": 0.001,   # 0.001 BTC
        },
        {
            "bot_name": "alpaca-trend-following-bot",  # Your fixed bot
            "symbol": "ETH-USD",                       # Change to BTC-USD if it trades BTC
            "fast": 9,
            "slow": 21,
            "capital": 1000,
            "trade_size": 0.01,                       # 0.01 ETH (or 0.001 if BTC)
        },
    ]

    start_date = "2025-01-01"
    end_date = date.today().strftime("%Y-%m-%d")

    for cfg in bots:
        print(f"\n🚀 Running backtest for {cfg['bot_name']} on {cfg['symbol']}...")
        backtester = TrendBacktester(
            symbol=cfg['symbol'],
            fast_p=cfg['fast'],
            slow_p=cfg['slow'],
            capital=cfg['capital'],
            trade_size=cfg['trade_size']
        )
        backtester.fetch_data(start_date, end_date)
        results = backtester.run()
        if results:
            save_backtest_result(
                bot_name=cfg['bot_name'],
                strategy_name=f"EMA_cross_{cfg['fast']}_{cfg['slow']}",
                start_date=start_date,
                end_date=end_date,
                results=results
            )
        else:
            print(f"⚠️ No results for {cfg['bot_name']}")

if __name__ == "__main__":
    run_all_trend_backtests()
