"""
FILE: exchange.py
FUNCTION: The Hands.
Handles all direct communication with the Alpaca API, 
including fetching market data, checking positions, and executing orders.
"""
from alpaca.trading.client import TradingClient
from alpaca.data.historical import CryptoHistoricalDataClient

class AlpacaManager:
# ... rest of your exchange code ...
"""
FILE: exchange.py
FUNCTION: Manages Alpaca API connections and order execution.
"""
from alpaca.trading.client import TradingClient
from alpaca.data.historical import CryptoHistoricalDataClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

class AlpacaManager:
    def __init__(self, api_key, secret_key):
        self.trading_client = TradingClient(api_key, secret_key, paper=True)
        self.data_client = CryptoHistoricalDataClient()

    def get_position_qty(self, symbol="BTC/USD"):
        try:
            pos = self.trading_client.get_position(symbol.replace("/", ""))
            return float(pos.qty)
        except:
            return 0.0

    def submit_order(self, symbol, side, qty):
        return self.trading_client.submit_order(
            order_data=MarketOrderRequest(symbol=symbol, qty=qty, side=side, time_in_force=TimeInForce.GTC)
        )
