"""
FILE: main.py
FUNCTION: The Orchestrator.

FIX: BUY and SELL orders were both hardcoded to a fixed quantity of 0.1,
regardless of actual account balance or actual position size. This caused
two separate failure modes seen in production:
  - BUY: repeated "insufficient balance for USD" errors when 0.1 of a
    symbol cost more than the available cash.
  - SELL: "insufficient balance for BTC (requested 0.1, available
    0.039463...)" when a previous BUY had only partially filled, leaving
    a real position smaller than 0.1 -- the bot then tried to sell more
    than it actually held.
Now: BUY sizes itself from real buying power (spends TRADE_USD worth of
the symbol, skips if unaffordable). SELL queries the real held quantity
from Alpaca via get_position_qty() right before selling, instead of
trusting local position state which can drift from partial fills.
"""
import asyncio
import logging
import os
import sys
import database as db   # <-- import your db module

from exchange import AlpacaManager
from engine import TradingEngine
from database import load_position_state, save_position_state

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# How much USD to spend per BUY (env-overridable). Keeping this modest and
# explicit avoids guessing a coin quantity that may or may not be affordable.
TRADE_USD = float(os.getenv("TRADE_USD", "100"))

async def main():
    logging.info(">>> Bot Orchestrator starting up... <<<")

    bot_name = os.getenv('BOT_NAME', 'alpaca-trend-following-bot')
    ex = AlpacaManager(os.getenv('APCA_API_KEY_ID'), os.getenv('APCA_API_SECRET_KEY'), bot_name=bot_name)
    eng = TradingEngine()

    logging.info(f"Loading position state for bot: {bot_name}")
    in_pos, entry, stop = load_position_state(bot_name)
    logging.info(f"Current State -> In Position: {in_pos}, Entry: {entry}, Stop: {stop}")

    logging.info("Entering core execution loop...")
    symbols = ["BTC/USD", "ETH/USD"]

    while True:
        try:
            # ✅ Update bot status to RUNNING (creates/updates row) – ADD THIS LINE
            db.update_status(bot_name, 'RUNNING')

            logging.info("Executing core loop iteration...")
            # Offload synchronous data fetching to a background worker thread
            bars = await asyncio.to_thread(ex.get_latest_bars, symbols)

            for symbol, data in bars.items():
                signal = eng.check_signal(data)
                current_price = data.close

                if signal == "BUY" and not in_pos:
                    buying_power = await asyncio.to_thread(ex.get_buying_power)
                    if buying_power < TRADE_USD:
                        logging.warning(f"🚫 Skipping BUY for {symbol} -- buying power "
                                         f"${buying_power:.2f} is below trade size ${TRADE_USD:.2f}")
                        continue
                    qty = round(TRADE_USD / current_price, 6)
                    logging.info(f"🎯 BUY Signal triggered for {symbol}. Placing order for "
                                 f"{qty} (~${TRADE_USD})...")
                    order = await asyncio.to_thread(ex.submit_order, symbol, "buy", qty, current_price)
                    if order:
                        in_pos = True
                        entry = current_price
                        save_position_state(bot_name, in_pos, entry, stop)
                        logging.info(f"✅ Position updated. Entry tracked at: {entry}")

                elif signal == "SELL" and in_pos:
                    held_qty = await asyncio.to_thread(ex.get_position_qty, symbol)
                    if held_qty <= 0:
                        logging.warning(f"🚫 SELL signal for {symbol} but no position found on "
                                         f"Alpaca -- clearing stale local position state.")
                        in_pos = False
                        entry = 0.0
                        save_position_state(bot_name, in_pos, entry, stop)
                        continue
                    logging.info(f"🛑 SELL Signal triggered for {symbol}. Selling actual held "
                                 f"qty {held_qty}...")
                    order = await asyncio.to_thread(ex.submit_order, symbol, "sell", held_qty, current_price)
                    if order:
                        in_pos = False
                        entry = 0.0
                        save_position_state(bot_name, in_pos, entry, stop)
                        logging.info("✅ Position updated. Position cleared.")

        except Exception as e:
            logging.error(f"❌ Error in execution loop: {e}")

        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
