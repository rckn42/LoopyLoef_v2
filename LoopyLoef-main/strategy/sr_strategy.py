"""
Support/Resistance trading strategy.
Implements entry logic based on SR levels, trend, and regime filters.
"""
import pandas as pd
from typing import Optional, Dict, Tuple
from strategy.sr_detection import SRDetector, SRLevel
from strategy.trend_filter import TrendFilter
from strategy.regime_filter import RegimeFilter
from strategy.indicators import calculate_atr, calculate_rsi


class SRStrategy:
    """Support/Resistance based trading strategy"""
    
    def __init__(self, config: Dict):
        """
        Initialize SR strategy with configuration.
        
        Args:
            config: Strategy configuration dictionary
        """
        # SR Detection
        self.sr_detector = SRDetector(
            lookback=config.get('sr_lookback', 200),
            atr_mult=config.get('sr_atr_mult', 1.2),
            touch_threshold=config.get('touch_threshold', 2),
            min_swing_strength=config.get('min_swing_strength', 3)
        )
        
        # Trend Filter
        self.use_trend_filter = config.get('use_trend_filter', True)
        if self.use_trend_filter:
            self.trend_filter = TrendFilter(
                fast_period=config.get('trend_ema_fast', 50),
                slow_period=config.get('trend_ema_slow', 200),
                htf_multiplier=config.get('trend_lookback_mult', 2)
            )
        
        # Regime Filter
        self.use_regime_filter = config.get('use_regime_filter', True)
        if self.use_regime_filter:
            self.regime_filter = RegimeFilter(
                atr_period=config.get('regime_atr_period', 20),
                vol_threshold=config.get('regime_vol_threshold', 1.5)
            )
        
        # Risk parameters
        self.stop_loss_atr_mult = config.get('stop_loss_atr_mult', 2.0)
        self.take_profit_r_mult = config.get('take_profit_r_mult', 2.0)
    
    def check_long_setup(self, df: pd.DataFrame, current_idx: int) -> Optional[Dict]:
        """
        Check for long entry setup.
        
        Args:
            df: OHLCV DataFrame
            current_idx: Current bar index
        
        Returns:
            Dict with entry signal details if setup exists, None otherwise
        """
        # Get current bar data
        current_bar = df.iloc[current_idx]
        current_price = current_bar['close']
        
        # Detect SR levels
        sr_levels = self.sr_detector.detect_levels(df, current_idx)
        
        # Find nearest support
        support = self.sr_detector.find_nearest_support(current_price, tolerance=0.02)
        
        if support is None:
            return None
        
        # Check if price is approaching support (within 2%)
        distance_to_support = (current_price - support.price) / support.price
        if distance_to_support > 0.02:
            return None
        
        # Check trend filter (if enabled)
        if self.use_trend_filter:
            trend = self.trend_filter.calculate_trend(df, current_idx)
            if trend == 'down':  # Don't long in downtrend
                return None
        
        # Check regime filter (if enabled)
        if self.use_regime_filter:
            regime = self.regime_filter.calculate_regime(df, current_idx)
            # SR strategy works better in ranging markets, but allow both
        
        # Check for rejection candle (bullish signal)
        rejection = self._check_bullish_rejection(df, current_idx)
        if not rejection:
            return None
        
        # Calculate ATR for stop loss
        atr = calculate_atr(df.iloc[:current_idx + 1]['high'], 
                           df.iloc[:current_idx + 1]['low'], 
                           df.iloc[:current_idx + 1]['close'])
        current_atr = atr.iloc[-1]
        
        # Calculate entry, stop, and target
        entry_price = current_price
        stop_loss = entry_price - (current_atr * self.stop_loss_atr_mult)
        risk_per_share = entry_price - stop_loss
        take_profit = entry_price + (risk_per_share * self.take_profit_r_mult)
        
        return {
            'direction': 'long',
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'risk_per_share': risk_per_share,
            'sr_level': support.price,
            'atr': current_atr,
            'timestamp': df.index[current_idx]
        }
    
    def check_short_setup(self, df: pd.DataFrame, current_idx: int) -> Optional[Dict]:
        """
        Check for short entry setup.
        
        Args:
            df: OHLCV DataFrame
            current_idx: Current bar index
        
        Returns:
            Dict with entry signal details if setup exists, None otherwise
        """
        # Get current bar data
        current_bar = df.iloc[current_idx]
        current_price = current_bar['close']
        
        # Detect SR levels
        sr_levels = self.sr_detector.detect_levels(df, current_idx)
        
        # Find nearest resistance
        resistance = self.sr_detector.find_nearest_resistance(current_price, tolerance=0.02)
        
        if resistance is None:
            return None
        
        # Check if price is approaching resistance (within 2%)
        distance_to_resistance = (resistance.price - current_price) / current_price
        if distance_to_resistance > 0.02:
            return None
        
        # Check trend filter (if enabled)
        if self.use_trend_filter:
            trend = self.trend_filter.calculate_trend(df, current_idx)
            if trend == 'up':  # Don't short in uptrend
                return None
        
        # Check regime filter (if enabled)
        if self.use_regime_filter:
            regime = self.regime_filter.calculate_regime(df, current_idx)
            # SR strategy works better in ranging markets, but allow both
        
        # Check for rejection candle (bearish signal)
        rejection = self._check_bearish_rejection(df, current_idx)
        if not rejection:
            return None
        
        # Calculate ATR for stop loss
        atr = calculate_atr(df.iloc[:current_idx + 1]['high'], 
                           df.iloc[:current_idx + 1]['low'], 
                           df.iloc[:current_idx + 1]['close'])
        current_atr = atr.iloc[-1]
        
        # Calculate entry, stop, and target
        entry_price = current_price
        stop_loss = entry_price + (current_atr * self.stop_loss_atr_mult)
        risk_per_share = stop_loss - entry_price
        take_profit = entry_price - (risk_per_share * self.take_profit_r_mult)
        
        return {
            'direction': 'short',
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'risk_per_share': risk_per_share,
            'sr_level': resistance.price,
            'atr': current_atr,
            'timestamp': df.index[current_idx]
        }
    
    def _check_bullish_rejection(self, df: pd.DataFrame, current_idx: int) -> bool:
        """
        Check for bullish rejection candle pattern.
        Indicates buying pressure at support.
        """
        if current_idx < 1:
            return False
        
        current_bar = df.iloc[current_idx]
        prev_bar = df.iloc[current_idx - 1]
        
        # Bullish candle (close > open)
        is_bullish = current_bar['close'] > current_bar['open']
        
        # Long lower shadow (bottom wick)
        body_size = abs(current_bar['close'] - current_bar['open'])
        lower_shadow = min(current_bar['open'], current_bar['close']) - current_bar['low']
        
        has_long_shadow = lower_shadow > body_size * 1.5
        
        # Price bouncing from low
        bouncing = current_bar['close'] > current_bar['low'] * 1.001
        
        return is_bullish and has_long_shadow and bouncing
    
    def _check_bearish_rejection(self, df: pd.DataFrame, current_idx: int) -> bool:
        """
        Check for bearish rejection candle pattern.
        Indicates selling pressure at resistance.
        """
        if current_idx < 1:
            return False
        
        current_bar = df.iloc[current_idx]
        prev_bar = df.iloc[current_idx - 1]
        
        # Bearish candle (close < open)
        is_bearish = current_bar['close'] < current_bar['open']
        
        # Long upper shadow (top wick)
        body_size = abs(current_bar['close'] - current_bar['open'])
        upper_shadow = current_bar['high'] - max(current_bar['open'], current_bar['close'])
        
        has_long_shadow = upper_shadow > body_size * 1.5
        
        # Price falling from high
        falling = current_bar['close'] < current_bar['high'] * 0.999
        
        return is_bearish and has_long_shadow and falling
