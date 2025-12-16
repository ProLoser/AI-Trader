"""
Momentum calculation module.
Calculates 3-month and 6-month momentum for ranking tickers.
"""
import pandas as pd
import numpy as np


def calculate_momentum(bars_df, period_months=3):
    """
    Calculate momentum over a specified period.
    
    Args:
        bars_df: DataFrame with OHLCV data (datetime index)
        period_months: Number of months for momentum calculation
        
    Returns:
        float: Momentum percentage or None if insufficient data
    """
    if bars_df.empty or len(bars_df) < 2:
        return None
    
    # Approximate trading days per month
    days_per_month = 21
    period_days = period_months * days_per_month
    
    if len(bars_df) < period_days:
        # Use available data if less than desired period
        period_days = len(bars_df)
    
    # Get close prices
    closes = bars_df['close'].values
    
    # Calculate momentum: (current_price - old_price) / old_price
    current_price = closes[-1]
    old_price = closes[-period_days]
    
    if old_price == 0:
        return None
    
    momentum = ((current_price - old_price) / old_price) * 100
    return momentum


def calculate_multi_period_momentum(bars_df):
    """
    Calculate both 3-month and 6-month momentum.
    
    Args:
        bars_df: DataFrame with OHLCV data (datetime index)
        
    Returns:
        dict: Dictionary with '3m' and '6m' momentum values
    """
    momentum_3m = calculate_momentum(bars_df, period_months=3)
    momentum_6m = calculate_momentum(bars_df, period_months=6)
    
    return {
        '3m': momentum_3m,
        '6m': momentum_6m,
        'combined': (momentum_3m + momentum_6m) / 2 if momentum_3m is not None and momentum_6m is not None else None
    }


def get_momentum_for_universe(alpaca_client, tickers):
    """
    Calculate momentum for all tickers in the universe.
    
    Args:
        alpaca_client: AlpacaClient instance
        tickers: List of ticker symbols
        
    Returns:
        pd.DataFrame: DataFrame with tickers and their momentum values
    """
    results = []
    
    for ticker in tickers:
        print(f"Calculating momentum for {ticker}...")
        bars = alpaca_client.get_historical_bars(ticker, days_back=180)
        
        if bars.empty:
            print(f"  No data available for {ticker}")
            continue
        
        momentum = calculate_multi_period_momentum(bars)
        
        if momentum['combined'] is not None:
            results.append({
                'Ticker': ticker,
                'Momentum_3M': momentum['3m'],
                'Momentum_6M': momentum['6m'],
                'Momentum_Combined': momentum['combined'],
                'CurrentPrice': bars['close'].iloc[-1]
            })
    
    df = pd.DataFrame(results)
    
    if not df.empty:
        # Sort by combined momentum (descending)
        df = df.sort_values('Momentum_Combined', ascending=False)
    
    return df
