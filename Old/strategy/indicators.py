"""
Technical indicators for the trading strategy.
All indicators implemented from scratch without external TA libraries.
"""
import pandas as pd
import numpy as np
from typing import Tuple


def calculate_sma(prices: pd.Series, period: int) -> pd.Series:
    """Calculate Simple Moving Average"""
    return prices.rolling(window=period).mean()


def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average"""
    return prices.ewm(span=period, adjust=False).mean()


def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range (ATR).
    
    True Range = max(high - low, abs(high - prev_close), abs(low - prev_close))
    ATR = EMA(True Range, period)
    """
    prev_close = close.shift(1)
    
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    atr = true_range.ewm(span=period, adjust=False).mean()
    
    return atr


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index (RSI).
    
    RSI = 100 - (100 / (1 + RS))
    RS = Average Gain / Average Loss
    """
    delta = prices.diff()
    
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.ewm(span=period, adjust=False).mean()
    avg_loss = loss.ewm(span=period, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_bollinger_bands(
    prices: pd.Series,
    period: int = 20,
    num_std: float = 2.0
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate Bollinger Bands.
    
    Returns: (middle_band, upper_band, lower_band)
    """
    middle = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    
    upper = middle + (std * num_std)
    lower = middle - (std * num_std)
    
    return middle, upper, lower


def calculate_momentum(prices: pd.Series, period: int = 10) -> pd.Series:
    """Calculate price momentum (rate of change)"""
    return prices.pct_change(period)


def calculate_volatility(returns: pd.Series, period: int = 20) -> pd.Series:
    """Calculate rolling volatility (standard deviation of returns)"""
    return returns.rolling(window=period).std()


def normalize_atr(atr: pd.Series, close: pd.Series) -> pd.Series:
    """Normalize ATR by price for cross-asset comparison"""
    return atr / close


def calculate_higher_tf_ema(
    df: pd.DataFrame,
    period: int,
    tf_multiplier: int = 2
) -> pd.Series:
    """
    Calculate EMA on a higher timeframe.
    Used for trend filtering.
    
    Args:
        df: OHLCV DataFrame
        period: EMA period on higher TF
        tf_multiplier: Timeframe multiplier (e.g., 2 for 2x higher TF)
    
    Returns:
        EMA values aligned to original timeframe
    """
    # Resample to higher timeframe
    htf_close = df['close'].resample(f'{tf_multiplier}T').last()
    
    # Calculate EMA on higher TF
    htf_ema = calculate_ema(htf_close, period)
    
    # Reindex to original timeframe (forward fill)
    ema_aligned = htf_ema.reindex(df.index, method='ffill')
    
    return ema_aligned


def detect_swing_highs(high: pd.Series, lookback: int = 5) -> pd.Series:
    """
    Detect swing high points.
    A swing high occurs when a high is greater than N bars before and after it.
    
    Returns: Boolean series indicating swing highs
    """
    swing_highs = pd.Series(False, index=high.index)
    
    for i in range(lookback, len(high) - lookback):
        is_swing_high = True
        
        # Check if current high is greater than lookback bars before and after
        for j in range(1, lookback + 1):
            if high.iloc[i] <= high.iloc[i - j] or high.iloc[i] <= high.iloc[i + j]:
                is_swing_high = False
                break
        
        if is_swing_high:
            swing_highs.iloc[i] = True
    
    return swing_highs


def detect_swing_lows(low: pd.Series, lookback: int = 5) -> pd.Series:
    """
    Detect swing low points.
    A swing low occurs when a low is less than N bars before and after it.
    
    Returns: Boolean series indicating swing lows
    """
    swing_lows = pd.Series(False, index=low.index)
    
    for i in range(lookback, len(low) - lookback):
        is_swing_low = True
        
        # Check if current low is less than lookback bars before and after
        for j in range(1, lookback + 1):
            if low.iloc[i] >= low.iloc[i - j] or low.iloc[i] >= low.iloc[i + j]:
                is_swing_low = False
                break
        
        if is_swing_low:
            swing_lows.iloc[i] = True
    
    return swing_lows
