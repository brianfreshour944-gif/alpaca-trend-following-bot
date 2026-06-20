"""
FILE: exchange.py
FUNCTION: Manages Alpaca API connections and order execution.
"""
from alpaca.trading.client import TradingClient
from alpaca.data.historical import CryptoHistoricalDataClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# 1. Import your reporting utility
from utils import log_trade 

class AlpacaManager:
    def __init__(self, api_key, secret_key, bot_name="Grok_Alpaca_Apex"):
        self.trading_client = TradingClient(api_key, secret_key, paper=True)
        self.data_client = CryptoHistoricalDataClient()
        self.bot_name = bot_name # Store the name to pass to log_trade

    def get_position_qty(self, symbol="BTC/USD"):
        try:
            pos = self.trading_client.get_position(symbol.replace("/", ""))
            return float(pos.qty)
        except:
            return 0.0

    def submit_order(self, symbol, side, qty, price=0.0):
        # 2. Execute the order
        order = self.trading_client.submit_order(
            order_data=MarketOrderRequest(
                symbol=symbol, 
                qty=qty, 
                side=side, 
                time_in_force=TimeInForce.GTC
            )
        )
        
        # 3. Log the trade to your dashboard immediately after execution
        log_trade(
            bot_name=self.bot_name,
            symbol=symbol,
            side=side.value, # Ensure we send 'buy' or 'sell'
            qty=float(qty),
            entry_price=float(price),
            order_id=order.id
        )
        
        return order
