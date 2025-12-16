"""
Alpaca API client module.
Handles fetching market data and executing trades.
"""
import alpaca_trade_api as tradeapi
import pandas as pd
from datetime import datetime, timedelta


class AlpacaClient:
    """Manages Alpaca API operations for market data and trading."""
    
    def __init__(self, api_key, secret_key, base_url):
        """
        Initialize Alpaca client.
        
        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            base_url: Alpaca base URL (paper or live)
        """
        self.api = tradeapi.REST(api_key, secret_key, base_url, api_version='v2')
    
    def get_historical_bars(self, symbol, timeframe='1Day', days_back=180):
        """
        Fetch historical price data for a symbol.
        
        Args:
            symbol: Ticker symbol
            timeframe: Bar timeframe (e.g., '1Day', '1Hour')
            days_back: Number of days to look back
            
        Returns:
            pd.DataFrame: OHLCV data with datetime index
        """
        try:
            end = datetime.now()
            start = end - timedelta(days=days_back)
            
            bars = self.api.get_bars(
                symbol,
                timeframe,
                start=start.strftime('%Y-%m-%d'),
                end=end.strftime('%Y-%m-%d'),
                adjustment='raw'
            ).df
            
            return bars
        except Exception as e:
            print(f"Error fetching bars for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_current_price(self, symbol):
        """
        Get current price for a symbol.
        
        Args:
            symbol: Ticker symbol
            
        Returns:
            float: Current price or None if unavailable
        """
        try:
            trade = self.api.get_latest_trade(symbol)
            return float(trade.price)
        except Exception as e:
            print(f"Error fetching current price for {symbol}: {e}")
            return None
    
    def get_account(self):
        """
        Get account information.
        
        Returns:
            Account object with portfolio details
        """
        return self.api.get_account()
    
    def get_positions(self):
        """
        Get current positions.
        
        Returns:
            list: List of Position objects
        """
        return self.api.list_positions()
    
    def submit_order(self, symbol, qty, side, order_type='market', time_in_force='day'):
        """
        Submit a trading order.
        
        Args:
            symbol: Ticker symbol
            qty: Quantity to trade
            side: 'buy' or 'sell'
            order_type: Order type (default 'market')
            time_in_force: Time in force (default 'day')
            
        Returns:
            Order object or None if failed
        """
        try:
            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type=order_type,
                time_in_force=time_in_force
            )
            print(f"Order submitted: {side.upper()} {qty} shares of {symbol}")
            return order
        except Exception as e:
            print(f"Error submitting order for {symbol}: {e}")
            return None
    
    def get_position(self, symbol):
        """
        Get position for a specific symbol.
        
        Args:
            symbol: Ticker symbol
            
        Returns:
            Position object or None if no position
        """
        try:
            return self.api.get_position(symbol)
        except:
            return None
