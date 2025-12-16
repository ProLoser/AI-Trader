"""
Ranking module.
Ranks tickers based on momentum and other criteria.
"""
import pandas as pd


def rank_tickers(momentum_df, top_n=10):
    """
    Rank tickers based on momentum score.
    
    Args:
        momentum_df: DataFrame with momentum data
        top_n: Number of top tickers to return (default 10)
        
    Returns:
        pd.DataFrame: Top ranked tickers
    """
    if momentum_df.empty:
        return pd.DataFrame()
    
    # Already sorted by combined momentum in momentum module
    # Return top N tickers
    top_tickers = momentum_df.head(top_n).copy()
    
    # Add rank column
    top_tickers['Rank'] = range(1, len(top_tickers) + 1)
    
    return top_tickers


def identify_buy_candidates(ranked_df, current_positions, max_positions=10):
    """
    Identify tickers to buy based on ranking.
    
    Args:
        ranked_df: DataFrame with ranked tickers
        current_positions: List of currently held tickers
        max_positions: Maximum number of positions to hold
        
    Returns:
        pd.DataFrame: Buy candidates
    """
    if ranked_df.empty:
        return pd.DataFrame()
    
    # Filter out tickers already held
    buy_candidates = ranked_df[~ranked_df['Ticker'].isin(current_positions)].copy()
    
    # Limit to available slots
    available_slots = max(0, max_positions - len(current_positions))
    buy_candidates = buy_candidates.head(available_slots)
    
    return buy_candidates


def identify_sell_candidates(current_positions, ranked_df, rank_threshold=20):
    """
    Identify positions to sell based on poor ranking or stop loss.
    
    Args:
        current_positions: List of currently held tickers
        ranked_df: DataFrame with all ranked tickers
        rank_threshold: Rank below which to consider selling
        
    Returns:
        list: Tickers to sell
    """
    sell_candidates = []
    
    for ticker in current_positions:
        # Check if ticker is in ranked list
        ticker_rank = ranked_df[ranked_df['Ticker'] == ticker]
        
        if ticker_rank.empty:
            # Ticker not in universe anymore - sell
            sell_candidates.append(ticker)
        elif 'Rank' in ticker_rank.columns and not ticker_rank.empty:
            rank_value = ticker_rank['Rank'].iloc[0]
            if rank_value > rank_threshold:
                # Poor ranking - sell
                sell_candidates.append(ticker)
    
    return sell_candidates
