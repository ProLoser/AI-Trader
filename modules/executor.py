"""
Trade executor module.
Handles trade execution logic based on approved suggestions.
"""
import pandas as pd
from datetime import datetime


def execute_approved_trades(sheets_manager, alpaca_client):
    """
    Execute trades that have been approved in the TradeSuggestions sheet.
    
    Args:
        sheets_manager: SheetsManager instance
        alpaca_client: AlpacaClient instance
        
    Returns:
        list: List of executed trade results
    """
    approved_trades = sheets_manager.get_approved_trades()
    
    if approved_trades.empty:
        print("No approved trades to execute.")
        return []
    
    executed = []
    
    for _, trade in approved_trades.iterrows():
        ticker = trade['Ticker']
        action = trade['Action'].lower()
        quantity = int(trade['Quantity'])
        
        # Determine order side
        side = 'buy' if action == 'buy' else 'sell'
        
        # Submit order
        order = alpaca_client.submit_order(
            symbol=ticker,
            qty=quantity,
            side=side
        )
        
        if order:
            executed.append({
                'Ticker': ticker,
                'Action': action,
                'Quantity': quantity,
                'Status': 'Executed',
                'OrderId': order.id,
                'Timestamp': datetime.now().isoformat()
            })
        else:
            executed.append({
                'Ticker': ticker,
                'Action': action,
                'Quantity': quantity,
                'Status': 'Failed',
                'OrderId': None,
                'Timestamp': datetime.now().isoformat()
            })
    
    return executed


def calculate_position_size(account_value, allocation_pct=0.5, price=None):
    """
    Calculate position size based on account value and allocation.
    
    Args:
        account_value: Total account value
        allocation_pct: Percentage to allocate per position (e.g., 0.5 for 50%)
        price: Price per share
        
    Returns:
        int: Number of shares to buy
    """
    if price is None or price <= 0:
        return 0
    
    position_value = account_value * allocation_pct
    shares = int(position_value / price)
    
    return shares
