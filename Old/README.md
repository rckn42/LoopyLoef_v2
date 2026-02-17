# Independent SR Trading System

A production-grade Support/Resistance (SR) based trading system for Binance Spot with backtesting, paper trading, and live execution capabilities.

## Overview

This system implements a complete algorithmic trading solution built from first principles with:
- Independent architecture and implementation
- Modular, production-quality code
- Comprehensive risk management
- Event-driven backtesting with no look-ahead bias
- Configuration-driven parameters (no magic numbers)

## Features

- ✅ **Multi-mode operation**: Backtest, Paper Trading, Live Trading
- ✅ **SR Strategy**: Dynamic support/resistance detection with swing points
- ✅ **Trend Filter**: Multi-timeframe EMA trend analysis
- ✅ **Regime Filter**: Volatility-based market state detection
- ✅ **Risk Management**: Position sizing, exposure limits, kill switch
- ✅ **Backtesting**: Event-driven engine with comprehensive metrics
- ✅ **Binance Integration**: REST API support for live trading
- ✅ **Logging**: Structured logging across all modules

## System Architecture

```
LoopyLoef/
├── config/
│   └── config_loader.py      # Configuration management
├── data/
│   ├── data_loader.py         # CSV OHLCV data loading
│   └── binance_downloader.py  # Historical data downloader
├── strategy/
│   ├── indicators.py          # Technical indicators (ATR, EMA, etc.)
│   ├── sr_detection.py        # Support/Resistance detection
│   ├── trend_filter.py        # Trend filtering logic
│   ├── regime_filter.py       # Market regime detection
│   └── sr_strategy.py         # Main strategy logic
├── risk/
│   ├── position_sizer.py      # Position sizing calculations
│   └── risk_manager.py        # Risk limits and kill switch
├── execution/
│   ├── order_manager.py       # Order and trade management
│   ├── paper_trader.py        # Simulated execution
│   └── binance_client.py      # Binance API client
├── backtest/
│   ├── backtest_engine.py     # Event-driven backtester
│   └── metrics.py             # Performance metrics
├── logs/                      # Log files and results
├── config.yaml                # Configuration file
├── requirements.txt           # Python dependencies
└── main.py                    # Main entry point
```

## Installation

### Prerequisites

- Python >= 3.10
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/rckn42/LoopyLoef.git
cd LoopyLoef
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file for API credentials (optional for backtest):
```bash
BINANCE_API_KEY=your_api_key_here
BINANCE_SECRET_KEY=your_secret_key_here
```

## Configuration

All parameters are configured in `config.yaml`:

### Key Parameters

```yaml
# Operating mode
mode: backtest  # backtest | paper | live

# Symbols to trade
symbols:
  - SOLUSDT
  - XRPUSDT
  - UNIUSDT

# Timeframe
base_tf: 30m  # 30m | 1h | 2h | 3h | 4h

# Risk Management
risk_per_trade: 0.0275      # 2.75% per trade
max_gross_alloc: 0.275      # 27.5% total exposure
max_open_trades: 5
max_daily_loss: 0.05        # 5% daily loss kills switch

# Strategy Parameters
sr_lookback: 200
sr_atr_mult: 1.2
touch_threshold: 2
use_trend_filter: true
use_regime_filter: true

# Backtesting
backtest_start_date: "2023-01-01"
backtest_end_date: "2024-12-31"
initial_capital: 10000
```

See `config.yaml` for all available parameters.

## Usage

### Running Backtests

1. Set mode to `backtest` in `config.yaml`:
```yaml
mode: backtest
```

2. Run the system:
```bash
python main.py
```

The system will:
- Download historical data if not available
- Run event-driven backtest
- Display performance metrics
- Export results to `logs/`

### Output Files

After backtesting, you'll find:
- `logs/equity.csv` - Equity curve over time
- `logs/trades.csv` - Detailed trade log
- `logs/stats.json` - Performance metrics
- `logs/system_*.log` - System logs

### Performance Metrics

The system calculates:
- **Returns**: Total Return, CAGR
- **Risk**: Sharpe, Sortino, Max Drawdown
- **Trade Stats**: Win Rate, Profit Factor, Expectancy
- **R-Multiples**: Average, Median, SQN

## Strategy Description

### Support/Resistance Detection

1. **Swing Points**: Identifies swing highs and lows
2. **Clustering**: Groups nearby levels into zones
3. **ATR Scaling**: Dynamic tolerance based on volatility
4. **Confirmation**: Minimum touch threshold

### Entry Logic

**Long Entry**:
- Price approaches support level
- Bullish rejection candle (long lower shadow)
- Trend filter passes (not in strong downtrend)
- Risk limits satisfied

**Short Entry**:
- Price approaches resistance level
- Bearish rejection candle (long upper shadow)
- Trend filter passes (not in strong uptrend)
- Risk limits satisfied

### Exit Logic

- **Stop Loss**: ATR-based stop below/above entry
- **Take Profit**: R-multiple based target (default 2R)
- **Kill Switch**: Triggers on max daily loss

## Paper Trading

**Status**: Framework implemented, real-time execution pending

To run paper trading:
```yaml
mode: paper
```

This would:
- Connect to live market data
- Run strategy in real-time
- Simulate order execution
- Track performance without real money

## Live Trading

**Status**: API integration ready, production deployment pending

⚠️ **WARNING**: Live trading involves real money and risk.

### Safety Checklist

Before enabling live trading:

1. ✅ Thoroughly backtest strategy
2. ✅ Run paper trading for extended period
3. ✅ Validate all risk parameters
4. ✅ Set up API keys with appropriate permissions
5. ✅ Start with small capital
6. ✅ Monitor continuously

### Enabling Live Trading

1. Set API credentials in `.env`
2. Enable in config:
```yaml
mode: live
enable_live: true  # Must be explicitly enabled
```

3. Run:
```bash
python main.py
```

### Safety Features

- **Kill Switch**: Auto-stops on daily loss limit
- **Position Limits**: Max open trades and exposure
- **Heartbeat Monitoring**: Detects connection issues
- **Error Handling**: Graceful failure handling
- **Logging**: Complete audit trail

## Development

### Code Structure

The system follows clean architecture principles:

- **Separation of Concerns**: Each module has single responsibility
- **No Look-Ahead Bias**: All indicators use only past data
- **Independent Implementation**: Built from scratch
- **Production Quality**: Error handling, logging, validation

### Testing

To validate the system:

1. **Backtest Validation**: Run on historical data
2. **Walk-Forward Testing**: Rolling window backtests
3. **Monte Carlo**: Resample trades for robustness
4. **Parameter Sensitivity**: Test parameter ranges

## Risk Disclaimer

This software is for educational and research purposes. Trading involves substantial risk of loss.

- Past performance does not guarantee future results
- Start with small amounts if trading live
- Never risk more than you can afford to lose
- Understand all risks before trading

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
- GitHub Issues: https://github.com/rckn42/LoopyLoef/issues
- Documentation: This README

## Roadmap

- [x] Core system architecture
- [x] Backtest engine
- [x] SR strategy implementation
- [x] Risk management
- [x] Binance API integration
- [ ] Real-time paper trading
- [ ] WebSocket integration
- [ ] Live trading deployment
- [ ] Telegram/Discord alerts
- [ ] Walk-forward testing
- [ ] Monte Carlo simulation
- [ ] Web dashboard
- [ ] Multi-strategy support

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch
3. Add tests for new features
4. Submit pull request

## Acknowledgments

Built independently following production trading system best practices.
