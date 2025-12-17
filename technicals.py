import pandas as pd
import numpy as np

def calculate_rsi(prices, period=14):
    """
    Calculates RSI for a pandas Series of prices.
    """
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    # Use exponential moving average for better smoothing (optional, but standard RSI uses Wilder's smoothing)
    # For simplicity/robustness, we'll use simple rolling mean first or valid Wilder's if easy.
    # Let's use Wilder's Smoothing for accuracy.
    
    delta = prices.diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    
    # Wilder's smoothing
    roll_up = up.ewm(com=period - 1, adjust=False).mean()
    roll_down = down.abs().ewm(com=period - 1, adjust=False).mean()
    
    rs = roll_up / roll_down
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi

def find_support_resistance(df, current_price, window=20):
    """
    Identifies potential support and resistance levels based on rolling mins and maxs.
    Returns the nearest Support and Resistance levels.
    """
    # Simple algorithm: Find local mins and maxs over a window
    # Then group them to find "significant" levels
    
    # Find local peaks/valleys
    df['min'] = df['close'].shift(1).rolling(window=window).min()
    df['max'] = df['close'].shift(1).rolling(window=window).max()
    
    # We can just take the most recent significant high/low or simply the range.
    # A better heuristic:
    # Support: Recent lows below current price
    # Resistance: Recent highs above current price
    
    recent_data = df.tail(60) # Last ~3 months
    
    potential_supports = recent_data[recent_data['close'] < current_price]['close'].tolist()
    potential_resistances = recent_data[recent_data['close'] > current_price]['close'].tolist()
    
    # Fallback if no recent data matches
    if not potential_supports:
        support = recent_data['close'].min()
    else:
        # Simplest: The lowest low in recent times, or maybe the "nearest" low?
        # Usually Support is the lowest recent point or a cluster.
        # Let's take the global min of the recent period as "Major Support"
        # And maybe a local min closer as "Minor Support". 
        # For this requirement, let's just return the lowest low of last 3 months.
        support = min(potential_supports)
        
    if not potential_resistances:
        resistance = recent_data['close'].max()
    else:
        # Resistance is the highest high
        resistance = max(potential_resistances)
        
    return support, resistance
