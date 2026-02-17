"""
Simulate the exact backtest workflow to verify the fix.
"""
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from data.data_loader import DataLoader
from data.binance_downloader import BinanceDownloader


def create_sample_csv_data(filepath):
    """Create sample CSV data similar to what Binance downloader would create"""
    # Create sample data for 6 months
    dates = pd.date_range('2024-01-01', '2024-06-30', freq='30min', tz='UTC')
    
    # Generate some realistic-ish price data
    import numpy as np
    np.random.seed(42)
    base_price = 100.0
    prices = base_price + np.cumsum(np.random.randn(len(dates)) * 2)
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': prices + np.abs(np.random.randn(len(dates)) * 1.5),
        'low': prices - np.abs(np.random.randn(len(dates)) * 1.5),
        'close': prices + np.random.randn(len(dates)) * 0.5,
        'volume': np.abs(np.random.randn(len(dates)) * 1000 + 5000)
    })
    
    # Ensure OHLC relationships are valid
    df['high'] = df[['open', 'high', 'low', 'close']].max(axis=1)
    df['low'] = df[['open', 'high', 'low', 'close']].min(axis=1)
    
    # Save like binance_downloader does (index=False)
    df.to_csv(filepath, index=False)
    print(f"Created sample data: {len(df)} bars saved to {filepath}")
    return df


def simulate_backtest_workflow():
    """Simulate the exact workflow from main.py"""
    print("\n" + "="*60)
    print("Simulating Backtest Workflow from main.py")
    print("="*60 + "\n")
    
    symbol = 'SOLUSDT'
    base_tf = '30m'
    csv_file = Path(f'data/{symbol}_{base_tf}.csv')
    
    # Simulate the scenario from the error: CSV doesn't exist yet
    if csv_file.exists():
        csv_file.unlink()
        print(f"Removed existing {csv_file}\n")
    
    # Step 1: Download data (simulated)
    print("Step 1: Simulating data download from Binance...")
    create_sample_csv_data(csv_file)
    
    # Step 2: Load from CSV (THIS IS THE FIX)
    print("\nStep 2: Loading data from CSV using DataLoader...")
    data_loader = DataLoader()
    df = data_loader.load_csv(str(csv_file), symbol)
    print(f"✓ Loaded {len(df)} bars")
    print(f"  Index type: {type(df.index).__name__}")
    print(f"  Index name: {df.index.name}")
    
    # Verify index is DatetimeIndex
    assert isinstance(df.index, pd.DatetimeIndex), f"ERROR: Expected DatetimeIndex, got {type(df.index)}"
    print("  ✓ Index is DatetimeIndex as expected")
    
    # Step 3: Filter date range (THIS WOULD FAIL BEFORE THE FIX)
    print("\nStep 3: Filtering date range...")
    start_date = '2024-01-01'
    end_date = '2024-06-30'
    
    try:
        filtered_df = data_loader.filter_date_range(df, start_date, end_date)
        print(f"✓ Successfully filtered data")
        print(f"  Filtered from {len(df)} to {len(filtered_df)} bars")
        print(f"  Date range: {filtered_df.index[0]} to {filtered_df.index[-1]}")
        
        # Verify the filtered data has the right structure
        assert isinstance(filtered_df.index, pd.DatetimeIndex), "Filtered data should have DatetimeIndex"
        assert len(filtered_df) > 0, "Filtered data should not be empty"
        
        print("\n" + "="*60)
        print("✓ WORKFLOW COMPLETED SUCCESSFULLY")
        print("  The TypeError that occurred before is now FIXED!")
        print("="*60)
        return True
        
    except TypeError as e:
        print(f"\n✗ FILTER FAILED WITH TypeError: {e}")
        print("  This is the error that was occurring before the fix")
        return False


def main():
    try:
        success = simulate_backtest_workflow()
        return 0 if success else 1
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
