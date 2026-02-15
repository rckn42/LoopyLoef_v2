"""
Data loader for OHLCV data.
Supports CSV import and timezone-aware UTC handling.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime


class DataLoader:
    """Load and preprocess OHLCV data"""
    
    def __init__(self):
        self.data_cache: Dict[str, pd.DataFrame] = {}
    
    def load_csv(self, filepath: str, symbol: str) -> pd.DataFrame:
        """
        Load OHLCV data from CSV file.
        Expected columns: timestamp, open, high, low, close, volume
        """
        if not Path(filepath).exists():
            raise FileNotFoundError(f"Data file not found: {filepath}")
        
        # Load CSV
        df = pd.read_csv(filepath)
        
        # Normalize column names to lowercase
        df.columns = df.columns.str.lower()
        
        # Validate required columns
        required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Convert timestamp to datetime (UTC)
        df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
        
        # Set timestamp as index
        df.set_index('timestamp', inplace=True)
        
        # Sort by timestamp
        df.sort_index(inplace=True)
        
        # Remove duplicates
        df = df[~df.index.duplicated(keep='first')]
        
        # Validate OHLC relationships
        self._validate_ohlc(df)
        
        # Cache the data
        self.data_cache[symbol] = df
        
        return df
    
    def _validate_ohlc(self, df: pd.DataFrame):
        """Validate OHLC data integrity"""
        # High should be >= all other prices
        invalid_high = (df['high'] < df['low']) | (df['high'] < df['open']) | (df['high'] < df['close'])
        if invalid_high.any():
            raise ValueError(f"Found {invalid_high.sum()} bars where high < other prices")
        
        # Low should be <= all other prices
        invalid_low = (df['low'] > df['high']) | (df['low'] > df['open']) | (df['low'] > df['close'])
        if invalid_low.any():
            raise ValueError(f"Found {invalid_low.sum()} bars where low > other prices")
        
        # Volume should be non-negative
        if (df['volume'] < 0).any():
            raise ValueError("Found negative volume values")
    
    def resample_timeframe(self, df: pd.DataFrame, target_tf: str) -> pd.DataFrame:
        """
        Resample OHLCV data to target timeframe.
        target_tf: '30m', '1h', '2h', '3h', '4h'
        """
        # Map timeframe string to pandas offset
        tf_map = {
            '1m': '1T',
            '5m': '5T',
            '15m': '15T',
            '30m': '30T',
            '1h': '1H',
            '2h': '2H',
            '3h': '3H',
            '4h': '4H',
            '1d': '1D'
        }
        
        if target_tf not in tf_map:
            raise ValueError(f"Unsupported timeframe: {target_tf}")
        
        offset = tf_map[target_tf]
        
        # Resample OHLCV data
        resampled = df.resample(offset).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        })
        
        # Remove bars with no data
        resampled = resampled.dropna()
        
        return resampled
    
    def get_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Get cached data for symbol"""
        return self.data_cache.get(symbol)
    
    def filter_date_range(self, df: pd.DataFrame, start_date: str, end_date: str) -> pd.DataFrame:
        """Filter data by date range"""
        start = pd.to_datetime(start_date, utc=True)
        end = pd.to_datetime(end_date, utc=True)
        
        return df[(df.index >= start) & (df.index <= end)]
