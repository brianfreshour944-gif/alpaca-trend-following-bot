"""
FILE: main.py
FUNCTION: The Orchestrator.
"""
import asyncio
import logging
import os
import sys
from exchange import AlpacaManager
from engine import TradingEngine
from database import load_position_state, save_position_state

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

async def main():
    logging.info(">>> Bot Orchestrator starting up... <<<")
    
    bot_name = os.getenv('BOT_NAME', 'alpaca_bot_2')
    ex = AlpacaManager(os.getenv('APCA_API_KEY_ID'), os.getenv('APCA_API_SECRET_KEY'), bot_name=bot_name)
    eng = TradingEngine()
    
    logging.info(f"Loading position state for bot: {bot_name}")
    in_pos, entry, stop = load_position_state(bot_name)
    logging.info(f"Current State -> In Position: {in_pos}, Entry: {entry}, Stop: {stop}")
    
    logging.info("Entering core execution loop...")
    symbols = ["BTC/USD", "ETH/USD"]
    
    while True:
        try:
            logging.info("Executing core loop iteration...")
            
            # Offload synchronous data fetching to a background worker thread
            bars = await asyncio.to_thread(ex.get_latest_bars, symbols)
            
            for symbol, data in bars.items():
                # Check signals using math engine
                signal = eng.check_signal(data) 
                current_price = data.close  # Get reference close price from data packet
                
                if signal == "BUY" and not in_pos:
                    logging.info(f"🎯 BUY Signal triggered for {symbol}. Placing order...")
                    order = await asyncio.to_thread(ex.submit_order, symbol, "buy", 0.1, current_price)
                    
                    if order:
                        in_pos = True
                        entry = current_price
                        save_position_state(bot_name, in_pos, entry, stop)
                        logging.info(f"✅ Position updated. Entry tracked at: {entry}")
                    
                elif signal == "SELL" and in_pos:
                    logging.info(f"🛑 SELL Signal triggered for {symbol}. Placing order...")
                    order = await asyncio.to_thread(ex.submit_order, symbol, "sell", 0.1, current_price)
                    
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
