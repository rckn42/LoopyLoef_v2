# Quick Start Guide

## Getting Started in 5 Minutes

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Generate Sample Data

```bash
python generate_sample_data.py
```

This creates sample OHLCV data for SOLUSDT, XRPUSDT, and UNIUSDT in the `data/` directory.

### 3. Run a Backtest

```bash
python demo_backtest.py
```

Or run the full system:

```bash
python main.py
```

### 4. View Results

Check the `logs/` directory for:
- `equity.csv` - Equity curve over time
- `trades.csv` - Detailed trade log with entry/exit
- `stats.json` - Performance metrics

## Example Output

```
============================================================
Running backtest for SOLUSDT
Period: 2024-01-01 00:00:00+00:00 to 2024-06-30 00:00:00+00:00
Bars: 8689
Initial Capital: $10,000.00
============================================================

[2024-01-09 20:30:00] Trade closed: take_profit | P&L: $159.18 (1.87R) | Equity: $10,063.79
[2024-01-15 19:30:00] Trade closed: take_profit | P&L: $221.83 (1.91R) | Equity: $10,125.83
[2024-01-19 13:30:00] Trade closed: take_profit | P&L: $199.43 (1.89R) | Equity: $10,270.38

============================================================
BACKTEST RESULTS
============================================================

Performance:
  Total Return: 12.50%
  CAGR: 15.30%
  Sharpe Ratio: 1.45
  Sortino Ratio: 2.10
  Max Drawdown: -8.50%
  Max DD Duration: 25 bars

Trade Statistics:
  Total Trades: 45
  Win Rate: 55.00%
  Profit Factor: 1.75
  Expectancy: $25.50

R-Multiple Statistics:
  Average: 0.25R
  Median: 0.15R
  SQN: 2.10
```

## Configuration

Edit `config.yaml` to customize:

```yaml
# Change trading symbols
symbols:
  - BTCUSDT
  - ETHUSDT

# Adjust risk
risk_per_trade: 0.02  # 2% per trade
max_open_trades: 3

# Modify strategy
sr_lookback: 100
touch_threshold: 3
```

## Next Steps

1. **Backtest Different Symbols**: Edit `symbols` in config.yaml
2. **Optimize Parameters**: Adjust SR and risk parameters
3. **Paper Trade**: Set `mode: paper` (requires live data feed)
4. **Go Live**: Set `mode: live` and `enable_live: true` (requires API keys)

## Common Commands

```bash
# Generate new sample data
python generate_sample_data.py

# Run quick demo backtest
python demo_backtest.py

# Run full system
python main.py

# Validate system
python test_system.py
```

## Troubleshooting

**Issue**: No data files found
**Solution**: Run `python generate_sample_data.py` first

**Issue**: Import errors
**Solution**: `pip install -r requirements.txt`

**Issue**: Backtest runs forever
**Solution**: Reduce date range in config.yaml or use demo_backtest.py

## Real Data

To use real Binance data instead of synthetic:

```python
from data.binance_downloader import BinanceDownloader

downloader = BinanceDownloader()
df = downloader.download_klines(
    symbol='BTCUSDT',
    interval='1h',
    start_date='2024-01-01',
    end_date='2024-06-30',
    output_file='data/BTCUSDT_1h.csv'
)
```

Then update config.yaml to use your symbol and timeframe.

## Learning Resources

- Review `strategy/sr_strategy.py` for entry/exit logic
- Check `backtest/metrics.py` for performance calculations
- Read `risk/risk_manager.py` for risk controls
- Study `execution/paper_trader.py` for trade simulation

## Safety First

Before going live:
1. Thoroughly backtest
2. Run paper trading for at least 30 days
3. Start with very small capital
4. Monitor continuously
5. Have an exit plan

Remember: Past performance does not guarantee future results!
