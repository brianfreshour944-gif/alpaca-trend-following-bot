"""
FILE: exchange.py
FUNCTION: Manages Alpaca API connections and order execution.
"""
from alpaca.trading.client import TradingClient
from alpaca.data.historical import CryptoHistoricalDataClient
# FIX: Changed from CryptoLatestBarsRequest to CryptoLatestBarRequest (singular)
from alpaca.data.requests import CryptoLatestBarRequest 
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from utils import log_trade 

class AlpacaManager:
    def __init__(self, api_key, secret_key, bot_name="alpaca_bot_2"):
        self.trading_client = TradingClient(api_key, secret_key, paper=True)
        self.data_client = CryptoHistoricalDataClient()
        self.bot_name = bot_name

    def get_account(self):
        """
        Get the account information including equity.
        Returns the full account object from Alpaca.
        """
        try:
            return self.trading_client.get_account()
        except Exception as e:
            print(f"❌ Error fetching account: {e}")
            return None

    def get_position_qty(self, symbol="BTC/USD"):
        try:
            trade_symbol = symbol.replace("/", "")
            pos = self.trading_client.get_position(trade_symbol)
            return float(pos.qty)
        except Exception:
            return 0.0

    def get_latest_bars(self, symbols):
        """
        Fetches the most recent bar data for given symbols.
        Returns a dictionary mapping symbol strings directly to their latest bar object.
        """
        try:
            # FIX: Use the singular Request model and method name
            request_params = CryptoLatestBarRequest(symbol_or_symbols=symbols)
            bars_response = self.data_client.get_crypto_latest_bar(request_params)
            
            # get_crypto_latest_bar returns a raw dictionary of {symbol: Bar} natively,
            # so we return it directly without looking for a `.data` property wrapper.
            return bars_response 
        except Exception as e:
            print(f"❌ Error fetching latest bars from Alpaca: {e}")
            return {}

    def submit_order(self, symbol, side, qty, fallback_price=0.0):
        try:
            trade_symbol = symbol.replace("/", "")
            order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
            
            order = self.trading_client.submit_order(
                order_data=MarketOrderRequest(
                    symbol=trade_symbol, 
                    qty=qty, 
                    side=order_side, 
                    time_in_force=TimeInForce.GTC
                )
            )
            
            filled_price = float(order.filled_avg_price) if order.filled_avg_price else float(fallback_price)
            
            log_trade(
                bot_name=self.bot_name,
                symbol=symbol,
                side=side.lower(), 
                qty=float(qty),
                entry_price=filled_price,
                order_id=str(order.id)
            )
            
            return order
        except Exception as e:
            print(f"❌ Failed to submit order for {symbol}: {e}")
            return None
