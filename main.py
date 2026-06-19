"""
FILE: main.py
FUNCTION: The Orchestrator.
The main control loop that connects the Memory (database), 
the Hands (exchange), and the Brain (engine) to execute the trading strategy.
"""
"""
FILE: main.py
FUNCTION: Orchestrator. Connects the engine, exchange, and database.
"""
import asyncio, logging, os
from exchange import AlpacaManager
from engine import TradingEngine
from database import load_position_state, save_position_state

logging.basicConfig(level=logging.INFO)

async def main():
    ex = AlpacaManager(os.getenv('APCA_API_KEY_ID'), os.getenv('APCA_API_SECRET_KEY'))
    eng = TradingEngine()
    bot_name = os.getenv('BOT_NAME', 'alpaca_bot_2')
    
    in_pos, entry, stop = load_position_state(bot_name)
    
    while True:
        # 1. Fetch Data (from ex)
        # 2. Analyze (from eng)
        # 3. Trade (from ex)
        # 4. Save (to database)
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
