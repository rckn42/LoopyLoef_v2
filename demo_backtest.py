"""
Quick backtest demo - shows system in action with limited data.
"""
import sys
import pandas as pd
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.config_loader import get_config
from data.data_loader import DataLoader
from backtest.backtest_engine import BacktestEngine


def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║   SR Trading System - Quick Demo                          ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    # Load config
    config = get_config()
    
    # Load data
    data_loader = DataLoader()
    symbol = 'SOLUSDT'
    csv_file = f'data/{symbol}_{config["base_tf"]}.csv'
    
    if not Path(csv_file).exists():
        print(f"Error: Data file not found: {csv_file}")
        print("Run generate_sample_data.py first")
        return 1
    
    df = data_loader.load_csv(csv_file, symbol)
    
    # Filter to shorter period for demo
    df = data_loader.filter_date_range(df, '2024-01-01', '2024-06-30')
    
    print(f"Loaded {len(df)} bars for {symbol}")
    print(f"Period: {df.index[0]} to {df.index[-1]}")
    
    # Run backtest
    backtest = BacktestEngine(config)
    results = backtest.run_backtest(df, symbol)
    
    # Export results
    backtest.export_results()
    
    print("\n✓ Demo complete!")
    print("\nResults saved to logs/")
    print("  - equity.csv")
    print("  - trades.csv") 
    print("  - stats.json")


if __name__ == "__main__":
    sys.exit(main() or 0)
