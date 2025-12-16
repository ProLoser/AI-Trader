#!/usr/bin/env python3
"""
AI Trader - Main Entry Point

This script orchestrates the trading workflow:
1. Reads ticker universe from Google Sheets
2. Fetches price data from Alpaca
3. Calculates momentum (3m/6m) and ranks tickers
4. Computes ATR-based stops
5. Generates BUY/SELL suggestions (50% allocation)
6. Writes suggestions to Google Sheets
7. Executes approved trades
8. Updates position state and tracks peaks
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd

from modules.sheets import SheetsManager
from modules.alpaca_client import AlpacaClient
from modules.momentum import get_momentum_for_universe
from modules.risk import get_atr_for_ticker, update_trailing_stop
from modules.ranking import rank_tickers, identify_buy_candidates, identify_sell_candidates
from modules.executor import execute_approved_trades, calculate_position_size
from modules.state import (
    initialize_state_for_positions,
    update_position_peaks,
    merge_state,
    check_stop_losses
)


def load_configuration():
    """Load configuration from environment variables."""
    load_dotenv()
    
    config = {
        'alpaca_api_key': os.getenv('ALPACA_API_KEY'),
        'alpaca_secret_key': os.getenv('ALPACA_SECRET_KEY'),
        'alpaca_base_url': os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets'),
        'google_sheet_id': os.getenv('GOOGLE_SHEET_ID'),
        'portfolio_allocation': float(os.getenv('PORTFOLIO_ALLOCATION', '0.5'))
    }
    
    # Validate required configuration
    required_keys = ['alpaca_api_key', 'alpaca_secret_key', 'google_sheet_id']
    missing = [key for key in required_keys if not config.get(key)]
    
    if missing:
        print(f"ERROR: Missing required configuration: {', '.join(missing)}")
        print("Please check your .env file or environment variables.")
        sys.exit(1)
    
    return config


def generate_trade_suggestions(ranked_df, current_positions, account_value, allocation_pct, alpaca_client):
    """
    Generate trade suggestions based on rankings and current positions.
    
    Args:
        ranked_df: DataFrame with ranked tickers
        current_positions: List of currently held ticker symbols
        account_value: Total account value
        allocation_pct: Allocation percentage per trade
        alpaca_client: AlpacaClient instance
        
    Returns:
        pd.DataFrame: Trade suggestions
    """
    suggestions = []
    
    # Identify buy candidates (tickers not currently held)
    buy_candidates = identify_buy_candidates(ranked_df, current_positions, max_positions=10)
    
    for _, row in buy_candidates.iterrows():
        ticker = row['Ticker']
        price = row['CurrentPrice']
        
        # Calculate position size
        quantity = calculate_position_size(account_value, allocation_pct, price)
        
        if quantity > 0:
            # Get ATR data for stop loss
            atr_data = get_atr_for_ticker(alpaca_client, ticker)
            stop_loss = atr_data.get('stop_loss', 'N/A')
            
            suggestions.append({
                'Ticker': ticker,
                'Action': 'BUY',
                'Quantity': quantity,
                'Price': f"{price:.2f}",
                'Reason': f"Rank #{row['Rank']}, Momentum: {row['Momentum_Combined']:.2f}%, Stop: {stop_loss:.2f if isinstance(stop_loss, float) else stop_loss}",
                'Approved': 'NO',
                'Timestamp': datetime.now().isoformat()
            })
    
    # Identify sell candidates (poor ranking or stop loss)
    sell_candidates = identify_sell_candidates(current_positions, ranked_df, rank_threshold=20)
    
    for ticker in sell_candidates:
        # Get position info
        position = alpaca_client.get_position(ticker)
        
        if position:
            quantity = abs(int(position.qty))
            price = float(position.current_price)
            
            # Find reason for sell
            ticker_rank = ranked_df[ranked_df['Ticker'] == ticker]
            if ticker_rank.empty:
                reason = "Ticker removed from universe"
            else:
                rank = ticker_rank['Rank'].iloc[0]
                reason = f"Poor ranking (#{rank})"
            
            suggestions.append({
                'Ticker': ticker,
                'Action': 'SELL',
                'Quantity': quantity,
                'Price': f"{price:.2f}",
                'Reason': reason,
                'Approved': 'NO',
                'Timestamp': datetime.now().isoformat()
            })
    
    return pd.DataFrame(suggestions)


def update_state_with_stops(state_df, alpaca_client):
    """
    Update state with ATR-based trailing stops.
    
    Args:
        state_df: Current state DataFrame
        alpaca_client: AlpacaClient instance
        
    Returns:
        pd.DataFrame: Updated state with stops
    """
    if state_df.empty:
        return state_df
    
    updated_state = state_df.copy()
    
    for idx, row in updated_state.iterrows():
        ticker = row['Ticker']
        peak = float(row.get('Peak', 0))
        
        # Get ATR data
        atr_data = get_atr_for_ticker(alpaca_client, ticker)
        atr = atr_data.get('atr')
        
        if atr and peak:
            # Calculate trailing stop from peak
            stop = update_trailing_stop(
                current_price=atr_data.get('current_price', peak),
                peak_price=peak,
                atr=atr,
                multiplier=2.0
            )
            if stop:
                updated_state.at[idx, 'ATRStop'] = stop
    
    return updated_state


def main():
    """Main execution function."""
    print("=" * 60)
    print("AI Trader - Momentum Trading Assistant")
    print("=" * 60)
    print(f"Execution time: {datetime.now().isoformat()}\n")
    
    # Load configuration
    print("Loading configuration...")
    config = load_configuration()
    
    # Initialize clients
    print("Initializing Alpaca client...")
    alpaca_client = AlpacaClient(
        api_key=config['alpaca_api_key'],
        secret_key=config['alpaca_secret_key'],
        base_url=config['alpaca_base_url']
    )
    
    print("Initializing Google Sheets client...")
    sheets_manager = SheetsManager(sheet_id=config['google_sheet_id'])
    
    # Get account info
    print("\nFetching account information...")
    account = alpaca_client.get_account()
    account_value = float(account.equity)
    print(f"Account Value: ${account_value:,.2f}")
    
    # Get current positions
    print("\nFetching current positions...")
    positions = alpaca_client.get_positions()
    current_positions = [pos.symbol for pos in positions]
    print(f"Current positions ({len(current_positions)}): {', '.join(current_positions) if current_positions else 'None'}")
    
    # Read universe from Google Sheets
    print("\nReading ticker universe from Google Sheets...")
    universe = sheets_manager.get_universe()
    print(f"Universe size: {len(universe)} tickers")
    
    if not universe:
        print("ERROR: No tickers in universe. Please populate the 'Universe' sheet.")
        sys.exit(1)
    
    # Calculate momentum for all tickers
    print("\nCalculating momentum for all tickers...")
    momentum_df = get_momentum_for_universe(alpaca_client, universe)
    print(f"Momentum calculated for {len(momentum_df)} tickers")
    
    if momentum_df.empty:
        print("ERROR: No momentum data available. Check ticker symbols and market data access.")
        sys.exit(1)
    
    # Rank tickers
    print("\nRanking tickers by momentum...")
    ranked_df = rank_tickers(momentum_df, top_n=20)
    print(f"Top 5 tickers:")
    for _, row in ranked_df.head(5).iterrows():
        print(f"  #{row['Rank']}: {row['Ticker']} - Momentum: {row['Momentum_Combined']:.2f}%")
    
    # Generate trade suggestions
    print("\nGenerating trade suggestions...")
    suggestions_df = generate_trade_suggestions(
        ranked_df=ranked_df,
        current_positions=current_positions,
        account_value=account_value,
        allocation_pct=config['portfolio_allocation'],
        alpaca_client=alpaca_client
    )
    
    print(f"Generated {len(suggestions_df)} trade suggestions")
    
    # Write suggestions to Google Sheets
    if not suggestions_df.empty:
        print("\nWriting trade suggestions to Google Sheets...")
        sheets_manager.write_trade_suggestions(suggestions_df)
        print("Trade suggestions written to 'TradeSuggestions' tab")
        
        # Display suggestions
        print("\nTrade Suggestions:")
        for _, row in suggestions_df.iterrows():
            print(f"  {row['Action']:4s} {row['Quantity']:4d} {row['Ticker']:6s} @ ${row['Price']:8s} - {row['Reason']}")
    else:
        print("No trade suggestions generated.")
    
    # Execute approved trades
    print("\nChecking for approved trades...")
    executed_trades = execute_approved_trades(sheets_manager, alpaca_client)
    
    if executed_trades:
        print(f"Executed {len(executed_trades)} trades:")
        for trade in executed_trades:
            print(f"  {trade['Action'].upper()} {trade['Quantity']} {trade['Ticker']} - {trade['Status']}")
    else:
        print("No approved trades to execute.")
    
    # Update state
    print("\nUpdating position state...")
    
    # Initialize state from current positions
    current_state = initialize_state_for_positions(alpaca_client)
    
    # Load existing state from Sheets
    existing_state = sheets_manager.get_state()
    
    # Merge states
    merged_state = merge_state(existing_state, current_state)
    
    # Update peaks
    updated_state = update_position_peaks(merged_state, alpaca_client)
    
    # Update stops
    state_with_stops = update_state_with_stops(updated_state, alpaca_client)
    
    # Check for stop losses
    stopped_out = check_stop_losses(state_with_stops, alpaca_client)
    if stopped_out:
        print(f"WARNING: {len(stopped_out)} positions hit stop loss: {', '.join(stopped_out)}")
    
    # Write updated state to Sheets
    if not state_with_stops.empty:
        sheets_manager.update_state(state_with_stops)
        print("Position state updated in 'State' tab")
        
        print("\nCurrent State:")
        for _, row in state_with_stops.iterrows():
            print(f"  {row['Ticker']:6s}: {row['Position']:4.0f} shares, Entry: ${row['EntryPrice']:7.2f}, Peak: ${row['Peak']:7.2f}, Stop: ${row['ATRStop']:7.2f}")
    else:
        print("No positions to track.")
    
    print("\n" + "=" * 60)
    print("Execution completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExecution interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
