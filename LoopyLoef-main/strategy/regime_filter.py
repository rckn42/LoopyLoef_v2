"""
Regime filter module.
Determines market state (trending vs ranging) using volatility and ATR.
"""
import pandas as pd
from strategy.indicators import calculate_atr, calculate_volatility, normalize_atr


class RegimeFilter:
    """Market regime filter (trending vs ranging)"""
    
    def __init__(self, atr_period: int = 20, vol_threshold: float = 1.5):
        """
        Initialize regime filter.
        
        Args:
            atr_period: ATR calculation period
            vol_threshold: Volatility threshold for trending regime
        """
        self.atr_period = atr_period
        self.vol_threshold = vol_threshold
    
    def calculate_regime(self, df: pd.DataFrame, current_idx: int) -> str:
        """
        Calculate market regime up to current_idx (no look-ahead bias).
        
        Args:
            df: OHLCV DataFrame
            current_idx: Current bar index
        
        Returns:
            'trending' or 'ranging'
        """
        data = df.iloc[:current_idx + 1]
        
        if len(data) < self.atr_period * 2:
            return 'ranging'
        
        # Calculate ATR
        atr = calculate_atr(data['high'], data['low'], data['close'], self.atr_period)
        
        # Normalize ATR by price
        normalized_atr = normalize_atr(atr, data['close'])
        
        # Calculate recent volatility
        returns = data['close'].pct_change()
        vol = calculate_volatility(returns, self.atr_period)
        
        current_atr = normalized_atr.iloc[-1]
        current_vol = vol.iloc[-1]
        
        # Calculate average volatility over lookback
        avg_vol = vol.iloc[-self.atr_period:].mean()
        
        # Regime determination:
        # Trending if current volatility is significantly higher than average
        if current_vol > avg_vol * self.vol_threshold:
            return 'trending'
        else:
            return 'ranging'
    
    def is_trending(self, df: pd.DataFrame, current_idx: int) -> bool:
        """Check if market is trending"""
        return self.calculate_regime(df, current_idx) == 'trending'
    
    def is_ranging(self, df: pd.DataFrame, current_idx: int) -> bool:
        """Check if market is ranging"""
        return self.calculate_regime(df, current_idx) == 'ranging'
    
    def calculate_volatility_ratio(self, df: pd.DataFrame, current_idx: int) -> float:
        """
        Calculate current volatility relative to average.
        
        Returns:
            Volatility ratio (>1 = higher than average, <1 = lower than average)
        """
        data = df.iloc[:current_idx + 1]
        
        if len(data) < self.atr_period * 2:
            return 1.0
        
        returns = data['close'].pct_change()
        vol = calculate_volatility(returns, self.atr_period)
        
        current_vol = vol.iloc[-1]
        avg_vol = vol.iloc[-self.atr_period:].mean()
        
        if avg_vol == 0:
            return 1.0
        
        return current_vol / avg_vol
