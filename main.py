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
