"""
Risk management module.
Calculates ATR-based stop losses.
"""
import pandas as pd
import numpy as np


def calculate_atr(bars_df, period=14):
    """
    Calculate Average True Range (ATR).
    
    Args:
        bars_df: DataFrame with OHLCV data
        period: ATR period (default 14)
        
    Returns:
        float: ATR value or None if insufficient data
    """
    if bars_df.empty or len(bars_df) < period:
        return None
    
    high = bars_df['high'].values
    low = bars_df['low'].values
    close = bars_df['close'].values
    
    # Calculate True Range
    tr_list = []
    for i in range(1, len(bars_df)):
        tr = max(
            high[i] - low[i],
            abs(high[i] - close[i-1]),
            abs(low[i] - close[i-1])
        )
        tr_list.append(tr)
    
    if len(tr_list) < period:
        return None
    
    # Calculate ATR as simple moving average of TR
    atr = np.mean(tr_list[-period:])
    return atr


def calculate_atr_stop(current_price, atr, multiplier=2.0):
    """
    Calculate ATR-based stop loss.
    
    Args:
        current_price: Current price of the asset
        atr: Average True Range value
        multiplier: ATR multiplier for stop distance (default 2.0)
        
    Returns:
        float: Stop loss price
    """
    if atr is None or current_price is None:
        return None
    
    stop_loss = current_price - (atr * multiplier)
    return stop_loss


def get_atr_for_ticker(alpaca_client, ticker, period=14, multiplier=2.0):
    """
    Calculate ATR and stop loss for a ticker.
    
    Args:
        alpaca_client: AlpacaClient instance
        ticker: Ticker symbol
        period: ATR period (default 14)
        multiplier: ATR multiplier (default 2.0)
        
    Returns:
        dict: Dictionary with ATR and stop loss values
    """
    bars = alpaca_client.get_historical_bars(ticker, days_back=60)
    
    if bars.empty:
        return {'atr': None, 'stop_loss': None}
    
    atr = calculate_atr(bars, period=period)
    current_price = bars['close'].iloc[-1]
    stop_loss = calculate_atr_stop(current_price, atr, multiplier)
    
    return {
        'atr': atr,
        'stop_loss': stop_loss,
        'current_price': current_price
    }


def update_trailing_stop(current_price, peak_price, atr, multiplier=2.0):
    """
    Update trailing stop based on new peak.
    
    Args:
        current_price: Current price
        peak_price: Peak price achieved
        atr: Average True Range
        multiplier: ATR multiplier
        
    Returns:
        float: Updated stop loss price
    """
    if atr is None or peak_price is None:
        return None
    
    # Trail from the peak
    stop_loss = peak_price - (atr * multiplier)
    return stop_loss
