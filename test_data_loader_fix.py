"""
Test to verify the data loader fix for downloaded data.
Validates that both downloaded and loaded data have DatetimeIndex.
"""
import sys
import pandas as pd
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from data.data_loader import DataLoader
from data.binance_downloader import BinanceDownloader


def test_downloader_creates_valid_df():
    """Test that binance downloader creates a DataFrame with timestamp column"""
    print("Testing BinanceDownloader output format...")
    
    # Create sample data like Binance would return
    klines = [
        [1640995200000, '100.0', '105.0', '99.0', '103.0', '1000.0', 
         1640997000000, '102000.0', 100, '500.0', '51000.0', '0'],
        [1640997000000, '103.0', '108.0', '102.0', '107.0', '1200.0', 
         1640998800000, '127200.0', 120, '600.0', '63600.0', '0'],
    ]
    
    downloader = BinanceDownloader()
    df = downloader._klines_to_dataframe(klines)
    
    # Verify timestamp column exists
    assert 'timestamp' in df.columns, "timestamp column missing"
    
    # Verify timestamp is not the index yet
    assert df.index.name != 'timestamp', "timestamp should not be index in downloader output"
    
    print("✓ BinanceDownloader creates DataFrame with timestamp column (not as index)")
    return df


def test_data_loader_sets_datetime_index():
    """Test that DataLoader properly sets timestamp as DatetimeIndex"""
    print("\nTesting DataLoader.load_csv sets DatetimeIndex...")
    
    # Create a temporary CSV file
    test_file = Path('/tmp/test_data.csv')
    test_data = pd.DataFrame({
        'timestamp': ['2024-01-01 00:00:00', '2024-01-01 00:30:00', '2024-01-01 01:00:00'],
        'open': [100.0, 103.0, 105.0],
        'high': [105.0, 108.0, 110.0],
        'low': [99.0, 102.0, 104.0],
        'close': [103.0, 107.0, 109.0],
        'volume': [1000.0, 1200.0, 1100.0]
    })
    test_data.to_csv(test_file, index=False)
    
    # Load using DataLoader
    loader = DataLoader()
    df = loader.load_csv(str(test_file), 'TEST')
    
    # Verify index is DatetimeIndex
    assert isinstance(df.index, pd.DatetimeIndex), f"Expected DatetimeIndex, got {type(df.index)}"
    assert df.index.name == 'timestamp', f"Expected index name 'timestamp', got {df.index.name}"
    
    # Clean up
    test_file.unlink()
    
    print("✓ DataLoader.load_csv correctly sets timestamp as DatetimeIndex")
    return df


def test_filter_date_range_with_datetime_index():
    """Test that filter_date_range works with DatetimeIndex"""
    print("\nTesting filter_date_range with DatetimeIndex...")
    
    # Create test data with DatetimeIndex
    dates = pd.date_range('2024-01-01', periods=100, freq='30min', tz='UTC')
    df = pd.DataFrame({
        'open': [100.0] * 100,
        'high': [105.0] * 100,
        'low': [99.0] * 100,
        'close': [103.0] * 100,
        'volume': [1000.0] * 100
    }, index=dates)
    df.index.name = 'timestamp'
    
    # Filter date range
    loader = DataLoader()
    filtered = loader.filter_date_range(df, '2024-01-01', '2024-01-02')
    
    # Verify filtering worked
    assert len(filtered) > 0, "Filter returned empty DataFrame"
    assert len(filtered) < len(df), "Filter did not reduce DataFrame size"
    assert filtered.index.max() <= pd.Timestamp('2024-01-02', tz='UTC'), "Filter end date not respected"
    
    print(f"✓ filter_date_range works correctly (filtered from {len(df)} to {len(filtered)} rows)")
    return filtered


def test_complete_workflow():
    """Test the complete workflow that mimics main.py"""
    print("\nTesting complete download -> load -> filter workflow...")
    
    # Step 1: Simulate downloaded data
    test_file = Path('/tmp/test_complete.csv')
    
    # Create sample data like binance_downloader would save
    sample_data = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=100, freq='30min', tz='UTC'),
        'open': [100.0] * 100,
        'high': [105.0] * 100,
        'low': [99.0] * 100,
        'close': [103.0] * 100,
        'volume': [1000.0] * 100
    })
    sample_data.to_csv(test_file, index=False)
    
    # Step 2: Load from CSV (like main.py does after download)
    loader = DataLoader()
    df = loader.load_csv(str(test_file), 'TEST')
    
    # Step 3: Filter date range (like main.py does)
    filtered = loader.filter_date_range(df, '2024-01-01', '2024-01-15')
    
    # Verify everything worked
    assert isinstance(filtered.index, pd.DatetimeIndex), "Final DataFrame should have DatetimeIndex"
    assert len(filtered) > 0, "Filtered data should not be empty"
    print(f"✓ Complete workflow successful: {len(filtered)} bars after filtering")
    
    # Clean up
    test_file.unlink()
    
    return True


def main():
    print("="*60)
    print("Data Loader Fix Validation Tests")
    print("="*60)
    
    try:
        test_downloader_creates_valid_df()
        test_data_loader_sets_datetime_index()
        test_filter_date_range_with_datetime_index()
        test_complete_workflow()
        
        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED")
        print("="*60)
        return 0
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
