"""
Trend filter module.
Determines trend direction using multi-timeframe EMA analysis.
"""
import pandas as pd
from strategy.indicators import calculate_ema


class TrendFilter:
    """Multi-timeframe trend filter"""
    
    def __init__(self, fast_period: int = 50, slow_period: int = 200, htf_multiplier: int = 2):
        """
        Initialize trend filter.
        
        Args:
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            htf_multiplier: Higher timeframe multiplier for trend confirmation
        """
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.htf_multiplier = htf_multiplier
    
    def calculate_trend(self, df: pd.DataFrame, current_idx: int) -> str:
        """
        Calculate trend direction up to current_idx (no look-ahead bias).
        
        Args:
            df: OHLCV DataFrame
            current_idx: Current bar index
        
        Returns:
            'up', 'down', or 'neutral'
        """
        # Get data up to current point
        data = df.iloc[:current_idx + 1]
        
        if len(data) < max(self.fast_period, self.slow_period):
            return 'neutral'
        
        # Calculate EMAs
        fast_ema = calculate_ema(data['close'], self.fast_period)
        slow_ema = calculate_ema(data['close'], self.slow_period)
        
        # Get current values
        current_fast = fast_ema.iloc[-1]
        current_slow = slow_ema.iloc[-1]
        current_price = data['close'].iloc[-1]
        
        # Determine trend
        if current_fast > current_slow and current_price > current_fast:
            return 'up'
        elif current_fast < current_slow and current_price < current_fast:
            return 'down'
        else:
            return 'neutral'
    
    def is_uptrend(self, df: pd.DataFrame, current_idx: int) -> bool:
        """Check if market is in uptrend"""
        return self.calculate_trend(df, current_idx) == 'up'
    
    def is_downtrend(self, df: pd.DataFrame, current_idx: int) -> bool:
        """Check if market is in downtrend"""
        return self.calculate_trend(df, current_idx) == 'down'
    
    def calculate_trend_strength(self, df: pd.DataFrame, current_idx: int) -> float:
        """
        Calculate trend strength (0 to 1).
        Based on distance between fast and slow EMAs.
        
        Returns:
            Trend strength value (higher = stronger trend)
        """
        data = df.iloc[:current_idx + 1]
        
        if len(data) < max(self.fast_period, self.slow_period):
            return 0.0
        
        fast_ema = calculate_ema(data['close'], self.fast_period)
        slow_ema = calculate_ema(data['close'], self.slow_period)
        
        current_fast = fast_ema.iloc[-1]
        current_slow = slow_ema.iloc[-1]
        
        # Calculate percentage distance
        distance = abs(current_fast - current_slow) / current_slow
        
        # Normalize to 0-1 range (cap at 10% distance = full strength)
        strength = min(distance / 0.10, 1.0)
        
        return strength
