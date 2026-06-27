"""
FILE: main.py
FUNCTION: The Orchestrator.
"""
import asyncio
import logging
import os
import sys
import database as db   # <-- import your db module

from exchange import AlpacaManager
from engine import TradingEngine
from database import load_position_state, save_position_state

# Add Risk Manager class for drawdown protection
class RiskManager:
    def __init__(self, max_drawdown_percent=10, max_position_percent=50):
        self.max_drawdown_percent = max_drawdown_percent
        self.max_position_percent = max_position_percent
        self.session_start_equity = None
        self.halted = False
        self.halt_reason = None

    def set_starting_equity(self, equity):
        if self.session_start_equity is None:
            self.session_start_equity = equity

    def check_drawdown(self, current_equity):
        if not self.session_start_equity:
            return False
        loss_percent = (self.session_start_equity - current_equity) / self.session_start_equity * 100
        if loss_percent >= self.max_drawdown_percent:
            self.halted = True
            self.halt_reason = f"Max drawdown hit: {loss_percent:.2f}% >= {self.max_drawdown_percent}%"
        return self.halted

    def get_max_position_size(self, current_equity, price):
        max_position_value = current_equity * (self.max_position_percent / 100)
        return max_position_value / price

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

async def main():
    try:
        logging.info(">>> Bot Orchestrator starting up... <<<")

        bot_name = os.getenv('BOT_NAME', 'alpaca-trend-following-bot')
        if not bot_name:
            raise ValueError("BOT_NAME environment variable not set")

        api_key = os.getenv('APCA_API_KEY_ID')
        secret_key = os.getenv('APCA_API_SECRET_KEY')
        if not api_key or not secret_key:
            raise ValueError("Alpaca API credentials not set")

        ex = AlpacaManager(api_key, secret_key, bot_name=bot_name)
        eng = TradingEngine()
        risk = RiskManager()  # Initialize risk manager

        logging.info(f"Loading position state for bot: {bot_name}")
        in_pos, entry, stop = load_position_state(bot_name)
        logging.info(f"Current State -> In Position: {in_pos}, Entry: {entry}, Stop: {stop}")

        # Set starting equity for drawdown calculation
        try:
            account = await asyncio.to_thread(ex.get_account)
            if account is None:
                raise ValueError("Account fetch returned None")
            starting_equity = float(account.equity)
            risk.set_starting_equity(starting_equity)
            logging.info(f"💰 Starting equity set: ${starting_equity:.2f}")
        except Exception as e:
            logging.error(f"❌ FATAL: Could not fetch starting equity: {e}")
            logging.error("🚨 Bot cannot start without account information")
            return

    except Exception as e:
        logging.error(f"❌ FATAL ERROR DURING INITIALIZATION: {e}")
        logging.error("🚨 Bot startup failed - check configuration and API credentials")
        return

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
                    logging.info(f"🎯 BUY Signal triggered for {symbol}. Placing order...")
                    # Use RiskManager to calculate position size
                    position_size = risk.get_max_position_size(starting_equity, current_price)
                    logging.info(f"📊 Calculated position size: {position_size:.6f} {symbol}")
                    order = await asyncio.to_thread(ex.submit_order, symbol, "buy", position_size, current_price)
                    if order:
                        in_pos = True
                        entry = current_price
                        save_position_state(bot_name, in_pos, entry, stop)
                        logging.info(f"✅ Position updated. Entry tracked at: {entry}")

                elif signal == "SELL" and in_pos:
                    logging.info(f"🛑 SELL Signal triggered for {symbol}. Placing order...")
                    # Use RiskManager to calculate position size for sell
                    position_size = risk.get_max_position_size(starting_equity, current_price)
                    logging.info(f"📊 Calculated position size: {position_size:.6f} {symbol}")
                    order = await asyncio.to_thread(ex.submit_order, symbol, "sell", position_size, current_price)
                    if order:
                        in_pos = False
                        entry = 0.0
                        save_position_state(bot_name, in_pos, entry, stop)
                        logging.info("✅ Position updated. Position cleared.")

            # Check drawdown and halt if necessary
            if not risk.halted:
                try:
                    account = await asyncio.to_thread(ex.get_account)
                    current_equity = float(account.equity)
                    if risk.check_drawdown(current_equity):
                        logging.error(f"🚨 {risk.halt_reason} - Stopping all trading")
                        break
                except Exception as e:
                    logging.warning(f"⚠️ Could not check drawdown: {e}")

        except Exception as e:
            logging.error(f"❌ Error in execution loop: {e}")
            logging.error("🔄 Attempting to recover and continue...")

        await asyncio.sleep(60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("🛑 Bot stopped by user (Ctrl+C)")
    except Exception as e:
        logging.error(f"❌ UNHANDLED EXCEPTION: {e}")
        logging.error("🚨 Bot crashed unexpectedly - check logs above")
        import traceback
        logging.error("Full traceback:")
        logging.error(traceback.format_exc())
