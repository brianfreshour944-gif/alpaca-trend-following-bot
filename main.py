"""
FILE: main.py
FUNCTION: The Orchestrator.
The main control loop that connects the Memory (database), 
the Hands (exchange), and the Brain (engine) to execute the trading strategy.
"""
import asyncio
import logging
import os
import sys
from exchange import AlpacaManager
from engine import TradingEngine
from database import load_position_state, save_position_state

# Configure logging to flush immediately to standard output so Coolify can see it
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

async def main():
    logging.info(">>> Bot Orchestrator starting up... <<<")
    
    # Initialize components
    ex = AlpacaManager(os.getenv('APCA_API_KEY_ID'), os.getenv('APCA_API_SECRET_KEY'))
    eng = TradingEngine()
    bot_name = os.getenv('BOT_NAME', 'alpaca_bot_2')
    
    logging.info(f"Loading position state for bot: {bot_name}")
    in_pos, entry, stop = load_position_state(bot_name)
    logging.info(f"Current State -> In Position: {in_pos}, Entry: {entry}, Stop: {stop}")
    
    logging.info("Entering core execution loop...")
    while True:
        logging.info("Checking market conditions...")
        
        # NOTE: You need to replace these comments with your actual function calls!
        # Example: 
        # data = await ex.get_historical_data()
        # signal = eng.calculate_signals(data)
        # if signal: await ex.execute_trade(...)
        
        # Keeping it awake for now
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
while True:
        try:
            logging.info("Executing core loop iteration...")
            
            # 1. Fetch current market data for your symbols
            # (e.g., getting the latest 1-minute or 5-minute bars from Alpaca)
            bars = ex.get_latest_bars(["BTC/USD", "ETH/USD"])
            
            # 2. Feed that data into your TradingEngine to calculate signals
            # (e.g., is the short-term trend crossing above the long-term trend?)
            for symbol, data in bars.items():
                signal = eng.check_signal(data) 
                
                # 3. Check if you need to execute a trade based on the signal
                if signal == "BUY" and not in_pos:
                    order = ex.place_market_order(symbol, side="buy", qty=0.1)
                    in_pos = True
                    entry = order.price
                    # Save the new state so you don't lose it if the server crashes
                    save_position_state(bot_name, in_pos, entry, stop)
                    
                elif signal == "SELL" and in_pos:
                    ex.place_market_order(symbol, side="sell", qty=0.1)
                    in_pos = False
                    entry = 0.0
                    save_position_state(bot_name, in_pos, entry, stop)
                    
        except Exception as e:
            logging.error(f"Error in execution loop: {e}")
            
        await asyncio.sleep(60)
