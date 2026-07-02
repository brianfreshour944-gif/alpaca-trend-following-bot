
"""
FILE: database.py
FUNCTION: The Memory Layer.
Handles all PostgreSQL interactions, including trade logging, 
order registration, and persistent status state management.
"""
import os
import psycopg2
import logging

def get_db_connection():
    """Returns a PostgreSQL database connection."""
    return psycopg2.connect(os.getenv('DATABASE_URL'))

def report_equity(bot_name, current_equity):
    """
    Reports this bot's real account equity to the dashboard.
    starting_equity is set the first time a bot reports in and is never
    overwritten afterward. live_equity and live_equity_updated_at are
    overwritten on every call -- call this once at startup and once per
    loop iteration with the bot's real account equity (e.g. from
    AlpacaManager.get_account().equity).
    """
    try:
        with get_db_connection() as conn, conn.cursor() as cur:
            cur.execute("""
                INSERT INTO bot_status (bot_name, starting_equity, live_equity, live_equity_updated_at, last_update)
                VALUES (%s, %s, %s, NOW(), NOW())
                ON CONFLICT (bot_name) DO UPDATE
                SET live_equity = EXCLUDED.live_equity,
                    live_equity_updated_at = NOW(),
                    last_update = NOW(),
                    starting_equity = COALESCE(bot_status.starting_equity, EXCLUDED.starting_equity)
            """, (bot_name, float(current_equity), float(current_equity)))
            conn.commit()
    except Exception as e:
        logging.error(f"❌ [CRITICAL] report_equity FAILED for {bot_name}: {e}")

def update_status(bot_name, status):
    """
    Updates the live runtime heartbeat and state inside the bot_status table.
    If the bot name doesn't exist yet, it safely creates the row.
    """
    try:
        with get_db_connection() as conn, conn.cursor() as cur:
            # 1. Attempt to update the existing bot's row heartbeat
            cur.execute("""
                UPDATE bot_status 
                SET status = %s, last_update = NOW() 
                WHERE bot_name = %s
            """, (status, bot_name))
            
            # 2. Fallback check: If the row doesn't exist, insert it fresh
            if cur.rowcount == 0:
                cur.execute("""
                    INSERT INTO bot_status (bot_name, status, last_update, session_start_time)
                    VALUES (%s, %s, NOW(), NOW())
                """, (bot_name, status))
            conn.commit()
            print(f"✅ [DEBUG] update_status succeeded for {bot_name} -> {status}")
    except Exception as e:
        print(f"❌ [CRITICAL] update_status FAILED: {e}")

def log_trade_to_db(bot_name, symbol, side, price, quantity, value, order_id, fee=0.0, realized_pnl=0.0):
    if price is None or quantity is None or float(price) <= 0 or float(quantity) <= 0:
        logging.warning(f"⚠️ Rejected log_trade_to_db call with invalid price/quantity: "
                         f"bot={bot_name} side={side} symbol={symbol} price={price} quantity={quantity}")
        return
    try:
        with get_db_connection() as conn, conn.cursor() as cur:
            cur.execute("""
                INSERT INTO trades (bot_name, exchange, symbol, side, price, quantity, value, fee_paid, order_id, realized_pnl, timestamp)
                VALUES (%s, 'Alpaca', %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (bot_name, symbol, side, float(price), float(quantity), float(value), float(fee), str(order_id), float(realized_pnl)))
            conn.commit()
            print(f"✅ [DEBUG] log_trade_to_db succeeded for {bot_name} -> {side} {quantity} {symbol} @ {price}")
    except Exception as e:
        logging.error(f"❌ [CRITICAL] log_trade_to_db FAILED for {bot_name} ({side} {symbol}): {e}", exc_info=True)

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
