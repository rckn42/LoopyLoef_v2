"""
Support and Resistance detection module.
Identifies swing highs/lows, clusters price levels, and forms dynamic SR zones.
"""
import pandas as pd
import numpy as np
from typing import List, Tuple, Dict
from strategy.indicators import detect_swing_highs, detect_swing_lows, calculate_atr


class SRLevel:
    """Represents a Support or Resistance level"""
    
    def __init__(self, price: float, level_type: str, touches: int = 1, strength: float = 1.0):
        self.price = price
        self.type = level_type  # 'support' or 'resistance'
        self.touches = touches
        self.strength = strength
        self.last_touch_idx = None
    
    def __repr__(self):
        return f"SRLevel({self.type}, price={self.price:.2f}, touches={self.touches}, strength={self.strength:.2f})"


class SRDetector:
    """Detect and manage Support/Resistance levels"""
    
    def __init__(self, lookback: int = 200, atr_mult: float = 1.2, touch_threshold: int = 2, min_swing_strength: int = 3):
        """
        Initialize SR detector.
        
        Args:
            lookback: Number of bars to look back for SR detection
            atr_mult: ATR multiplier for zone tolerance
            touch_threshold: Minimum touches to confirm SR level
            min_swing_strength: Minimum bars between swing points
        """
        self.lookback = lookback
        self.atr_mult = atr_mult
        self.touch_threshold = touch_threshold
        self.min_swing_strength = min_swing_strength
        self.sr_levels: List[SRLevel] = []
    
    def detect_levels(self, df: pd.DataFrame, current_idx: int) -> List[SRLevel]:
        """
        Detect SR levels up to current_idx (no look-ahead bias).
        
        Args:
            df: OHLCV DataFrame
            current_idx: Current bar index (inclusive)
        
        Returns:
            List of SRLevel objects
        """
        # Get data up to current point
        data = df.iloc[:current_idx + 1]
        
        if len(data) < self.lookback:
            return []
        
        # Use only lookback period
        lookback_data = data.iloc[-self.lookback:]
        
        # Calculate ATR for zone tolerance
        atr = calculate_atr(lookback_data['high'], lookback_data['low'], lookback_data['close'])
        current_atr = atr.iloc[-1]
        zone_tolerance = current_atr * self.atr_mult
        
        # Detect swing points
        swing_highs = detect_swing_highs(lookback_data['high'], self.min_swing_strength)
        swing_lows = detect_swing_lows(lookback_data['low'], self.min_swing_strength)
        
        # Extract swing high prices
        resistance_prices = lookback_data.loc[swing_highs, 'high'].values
        
        # Extract swing low prices
        support_prices = lookback_data.loc[swing_lows, 'low'].values
        
        # Cluster resistance levels
        resistance_levels = self._cluster_levels(resistance_prices, zone_tolerance, 'resistance')
        
        # Cluster support levels
        support_levels = self._cluster_levels(support_prices, zone_tolerance, 'support')
        
        # Combine and filter by touch threshold
        all_levels = resistance_levels + support_levels
        confirmed_levels = [level for level in all_levels if level.touches >= self.touch_threshold]
        
        self.sr_levels = confirmed_levels
        return confirmed_levels
    
    def _cluster_levels(self, prices: np.ndarray, tolerance: float, level_type: str) -> List[SRLevel]:
        """
        Cluster nearby price levels into zones.
        
        Args:
            prices: Array of price levels
            tolerance: Maximum distance to cluster prices together
            level_type: 'support' or 'resistance'
        
        Returns:
            List of clustered SRLevel objects
        """
        if len(prices) == 0:
            return []
        
        # Sort prices
        sorted_prices = np.sort(prices)
        
        clusters = []
        current_cluster = [sorted_prices[0]]
        
        for price in sorted_prices[1:]:
            if price - current_cluster[-1] <= tolerance:
                # Price is close enough, add to current cluster
                current_cluster.append(price)
            else:
                # Start new cluster
                clusters.append(current_cluster)
                current_cluster = [price]
        
        # Add last cluster
        clusters.append(current_cluster)
        
        # Create SR levels from clusters
        sr_levels = []
        for cluster in clusters:
            avg_price = np.mean(cluster)
            touches = len(cluster)
            strength = touches / self.touch_threshold  # Strength relative to threshold
            
            level = SRLevel(avg_price, level_type, touches, strength)
            sr_levels.append(level)
        
        return sr_levels
    
    def find_nearest_support(self, current_price: float, tolerance: float) -> SRLevel | None:
        """Find nearest support level below current price"""
        support_levels = [level for level in self.sr_levels if level.type == 'support' and level.price < current_price]
        
        if not support_levels:
            return None
        
        # Find closest support
        closest = min(support_levels, key=lambda x: abs(x.price - current_price))
        
        # Check if within tolerance
        if abs(closest.price - current_price) / current_price <= tolerance:
            return closest
        
        return None
    
    def find_nearest_resistance(self, current_price: float, tolerance: float) -> SRLevel | None:
        """Find nearest resistance level above current price"""
        resistance_levels = [level for level in self.sr_levels if level.type == 'resistance' and level.price > current_price]
        
        if not resistance_levels:
            return None
        
        # Find closest resistance
        closest = min(resistance_levels, key=lambda x: abs(x.price - current_price))
        
        # Check if within tolerance
        if abs(closest.price - current_price) / current_price <= tolerance:
            return closest
        
        return None
    
    def is_near_support(self, current_price: float, tolerance_pct: float = 0.01) -> bool:
        """Check if current price is near a support level"""
        support = self.find_nearest_support(current_price, tolerance_pct)
        return support is not None
    
    def is_near_resistance(self, current_price: float, tolerance_pct: float = 0.01) -> bool:
        """Check if current price is near a resistance level"""
        resistance = self.find_nearest_resistance(current_price, tolerance_pct)
        return resistance is not None
