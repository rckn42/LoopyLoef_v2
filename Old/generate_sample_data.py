"""
Generate sample OHLCV data for testing the backtest system.
Creates realistic price action with support/resistance levels.
"""
import pandas as pd
import numpy as np
from pathlib import Path


def generate_sample_ohlcv(
    symbol: str,
    start_date: str,
    end_date: str,
    timeframe: str = '30m',
    initial_price: float = 100.0,
    volatility: float = 0.02,
    trend: float = 0.0001
):
    """
    Generate sample OHLCV data with realistic characteristics.
    
    Args:
        symbol: Trading symbol (e.g., 'BTCUSDT')
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        timeframe: Candle timeframe
        initial_price: Starting price
        volatility: Price volatility (std dev)
        trend: Trend component (drift)
    
    Returns:
        DataFrame with OHLCV data
    """
    # Create date range
    freq_map = {
        '1m': '1min',
        '5m': '5min',
        '15m': '15min',
        '30m': '30min',
        '1h': '1h',
        '2h': '2h',
        '3h': '3h',
        '4h': '4h',
        '1d': '1D'
    }
    
    dates = pd.date_range(
        start=start_date,
        end=end_date,
        freq=freq_map.get(timeframe, '1h'),
        tz='UTC'
    )
    
    n = len(dates)
    
    # Generate price using geometric Brownian motion
    returns = np.random.normal(trend, volatility, n)
    
    # Add some autocorrelation for more realistic price action
    for i in range(1, n):
        returns[i] = 0.3 * returns[i-1] + 0.7 * returns[i]
    
    # Calculate cumulative prices
    price_multipliers = np.exp(returns.cumsum())
    close_prices = initial_price * price_multipliers
    
    # Add support/resistance levels by creating occasional consolidations
    for i in range(50, n, 100):
        if i + 20 < n:
            # Create consolidation zone
            consolidation_price = close_prices[i]
            close_prices[i:i+20] = consolidation_price + np.random.normal(0, volatility * initial_price * 0.5, 20)
    
    # Generate OHLC from close
    open_prices = close_prices + np.random.normal(0, volatility * initial_price * 0.3, n)
    
    # High and low with realistic wicks
    high_wick = np.abs(np.random.normal(0, volatility * initial_price * 0.5, n))
    low_wick = np.abs(np.random.normal(0, volatility * initial_price * 0.5, n))
    
    high_prices = np.maximum(open_prices, close_prices) + high_wick
    low_prices = np.minimum(open_prices, close_prices) - low_wick
    
    # Generate volume
    base_volume = 1000000
    volume = base_volume + np.random.exponential(base_volume * 0.5, n)
    
    # Increase volume on big moves
    price_changes = np.abs(returns)
    volume = volume * (1 + price_changes * 10)
    
    # Create DataFrame
    df = pd.DataFrame({
        'timestamp': dates,
        'open': open_prices,
        'high': high_prices,
        'low': low_prices,
        'close': close_prices,
        'volume': volume
    })
    
    return df


def main():
    """Generate sample data files"""
    print("Generating sample OHLCV data for testing...")
    
    # Create data directory
    Path('data').mkdir(exist_ok=True)
    
    # Generate data for different symbols
    symbols = [
        ('SOLUSDT', 100.0, 0.03, 0.0002),   # Higher volatility, uptrend
        ('XRPUSDT', 0.5, 0.025, -0.0001),   # Lower price, slight downtrend
        ('UNIUSDT', 10.0, 0.028, 0.0001),   # Mid price, slight uptrend
    ]
    
    timeframes = ['30m', '1h']
    
    for symbol, initial_price, vol, trend in symbols:
        for tf in timeframes:
            print(f"\nGenerating {symbol} {tf}...")
            
            df = generate_sample_ohlcv(
                symbol=symbol,
                start_date='2023-01-01',
                end_date='2024-12-31',
                timeframe=tf,
                initial_price=initial_price,
                volatility=vol,
                trend=trend
            )
            
            # Save to CSV
            filename = f'data/{symbol}_{tf}.csv'
            df.to_csv(filename, index=False)
            
            print(f"  Saved {len(df)} bars to {filename}")
            print(f"  Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
            print(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    
    print("\n✓ Sample data generation complete!")
    print("\nYou can now run the backtest with:")
    print("  python main.py")


if __name__ == "__main__":
    main()
