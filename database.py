"""
FILE: database.py
FUNCTION: The Memory Layer.
Handles all PostgreSQL interactions, including trade logging, 
order registration, and persistent status state management.

EXTENDED FUNCTION: Manages PostgreSQL connection and data persistence.
"""
import os
import psycopg2
import logging

def get_db_connection():
    return psycopg2.connect(os.getenv('DATABASE_URL'))

# ... keep the rest of your functions (log_trade_to_db, save_position_state, load_position_state) exactly as they are

def log_trade_to_db(bot_name, symbol, side, price, quantity, value, order_id, fee=0.0, realized_pnl=0.0):
    try:
        with get_db_connection() as conn, conn.cursor() as cur:
            cur.execute("""
                INSERT INTO trades (bot_name, exchange, symbol, side, price, quantity, value, fee_paid, order_id, realized_pnl, timestamp)
                VALUES (%s, 'Alpaca', %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (bot_name, symbol, side, float(price), float(quantity), float(value), float(fee), str(order_id), float(realized_pnl)))
            conn.commit()
    except Exception as e:
        logging.error(f"Database write error: {e}")

def save_position_state(bot_name, in_position, entry_price, trailing_stop):
    try:
        with get_db_connection() as conn, conn.cursor() as cur:
            cur.execute("""
                INSERT INTO bot_status (bot_name, in_position, entry_price, trailing_stop, last_update)
                VALUES (%s, %s, %s, %s, NOW())
                ON CONFLICT (bot_name) DO UPDATE 
                SET in_position = EXCLUDED.in_position, entry_price = EXCLUDED.entry_price, 
                    trailing_stop = EXCLUDED.trailing_stop, last_update = NOW()
            """, (bot_name, in_position, float(entry_price), float(trailing_stop)))
            conn.commit()
    except Exception as e:
        logging.error(f"save_position_state error: {e}")

def load_position_state(bot_name):
    try:
        with get_db_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT in_position, entry_price, trailing_stop FROM bot_status WHERE bot_name = %s", (bot_name,))
            row = cur.fetchone()
            return (bool(row[0]), float(row[1] or 0), float(row[2] or 0)) if row else (False, 0.0, 0.0)
    except:
        return False, 0.0, 0.0
