"""
State management module.
Tracks position state including peaks and stops.
"""
import pandas as pd
from datetime import datetime


def update_position_peaks(state_df, alpaca_client):
    """
    Update peak prices for current positions.
    
    Args:
        state_df: DataFrame with current state
        alpaca_client: AlpacaClient instance
        
    Returns:
        pd.DataFrame: Updated state DataFrame
    """
    if state_df.empty:
        return state_df
    
    updated_state = state_df.copy()
    
    for idx, row in updated_state.iterrows():
        ticker = row['Ticker']
        current_peak = float(row.get('Peak', 0))
        
        # Get current price
        current_price = alpaca_client.get_current_price(ticker)
        
        if current_price is None:
            continue
        
        # Update peak if current price is higher
        if current_price > current_peak:
            updated_state.at[idx, 'Peak'] = current_price
            updated_state.at[idx, 'LastUpdated'] = datetime.now().isoformat()
    
    return updated_state


def initialize_state_for_positions(alpaca_client):
    """
    Initialize state from current Alpaca positions.
    
    Args:
        alpaca_client: AlpacaClient instance
        
    Returns:
        pd.DataFrame: State DataFrame
    """
    positions = alpaca_client.get_positions()
    
    if not positions:
        return pd.DataFrame()
    
    state_records = []
    
    for pos in positions:
        ticker = pos.symbol
        quantity = int(pos.qty)
        entry_price = float(pos.avg_entry_price)
        current_price = float(pos.current_price)
        
        # Initialize peak as current price
        peak = max(entry_price, current_price)
        
        state_records.append({
            'Ticker': ticker,
            'Position': quantity,
            'EntryPrice': entry_price,
            'Peak': peak,
            'ATRStop': 0.0,  # Will be calculated separately
            'LastUpdated': datetime.now().isoformat()
        })
    
    return pd.DataFrame(state_records)


def merge_state(existing_state_df, new_positions_df):
    """
    Merge existing state with new position data.
    
    Args:
        existing_state_df: Existing state from Sheets
        new_positions_df: New positions from Alpaca
        
    Returns:
        pd.DataFrame: Merged state
    """
    if existing_state_df.empty:
        return new_positions_df
    
    if new_positions_df.empty:
        return existing_state_df
    
    # Create a dictionary from existing state
    existing_dict = {}
    for _, row in existing_state_df.iterrows():
        ticker = row['Ticker']
        existing_dict[ticker] = row.to_dict()
    
    # Update with new positions
    merged_records = []
    
    for _, new_row in new_positions_df.iterrows():
        ticker = new_row['Ticker']
        
        if ticker in existing_dict:
            # Keep existing peak if higher
            existing_peak = float(existing_dict[ticker].get('Peak', 0))
            new_peak = float(new_row.get('Peak', 0))
            
            merged_records.append({
                'Ticker': ticker,
                'Position': new_row['Position'],
                'EntryPrice': new_row['EntryPrice'],
                'Peak': max(existing_peak, new_peak),
                'ATRStop': existing_dict[ticker].get('ATRStop', 0.0),
                'LastUpdated': datetime.now().isoformat()
            })
        else:
            # New position
            merged_records.append(new_row.to_dict())
    
    return pd.DataFrame(merged_records)


def check_stop_losses(state_df, alpaca_client):
    """
    Check if any positions have hit their stop losses.
    
    Args:
        state_df: DataFrame with state including stops
        alpaca_client: AlpacaClient instance
        
    Returns:
        list: Tickers that hit their stops
    """
    stopped_out = []
    
    if state_df.empty:
        return stopped_out
    
    for _, row in state_df.iterrows():
        ticker = row['Ticker']
        stop_price = float(row.get('ATRStop', 0))
        
        if stop_price == 0:
            continue
        
        current_price = alpaca_client.get_current_price(ticker)
        
        if current_price is None:
            continue
        
        # Check if current price is below stop
        if current_price <= stop_price:
            stopped_out.append(ticker)
            print(f"Stop loss triggered for {ticker}: Price {current_price:.2f} <= Stop {stop_price:.2f}")
    
    return stopped_out
