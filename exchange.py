"""
FILE: exchange.py
FUNCTION: Manages Alpaca API connections and order execution.
"""
from alpaca.trading.client import TradingClient
from alpaca.data.historical import CryptoHistoricalDataClient
from alpaca.data.requests import CryptoLatestBarsRequest
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from utils import log_trade 

class AlpacaManager:
    def __init__(self, api_key, secret_key, bot_name="alpaca_bot_2"):
        self.trading_client = TradingClient(api_key, secret_key, paper=True)
        self.data_client = CryptoHistoricalDataClient()
        self.bot_name = bot_name

    def get_position_qty(self, symbol="BTC/USD"):
        try:
            # Strip slash for trading endpoint (BTC/USD -> BTCUSD)
            trade_symbol = symbol.replace("/", "")
            pos = self.trading_client.get_position(trade_symbol)
            return float(pos.qty)
        except Exception:
            return 0.0

    def get_latest_bars(self, symbols):
        """
        Fetches the most recent bar data for given symbols.
        Returns a dictionary mapping symbol strings to their latest bar object.
        """
        try:
            request_params = CryptoLatestBarsRequest(symbol_or_symbols=symbols)
            bars_response = self.data_client.get_crypto_latest_bars(request_params)
            return bars_response.data
        except Exception as e:
            print(f"❌ Error fetching latest bars from Alpaca: {e}")
            return {}

    def submit_order(self, symbol, side, qty, fallback_price=0.0):
        """
        Submits a market order. Normalizes symbols for trading endpoints.
        """
        try:
            # Alpaca execution endpoint requires standard symbols without the slash
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
            
            # Use fallback execution price if the order isn't completely filled at submission millisecond
            filled_price = float(order.filled_avg_price) if order.filled_avg_price else float(fallback_price)
            
            # Log the trade using our utils module tracking parameters
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
