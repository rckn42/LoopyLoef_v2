"""
Main entry point for the SR Trading System.
Supports backtest, paper trading, and live trading modes.
"""
import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from config.config_loader import get_config
from data.data_loader import DataLoader
from data.binance_downloader import BinanceDownloader
from backtest.backtest_engine import BacktestEngine


def setup_logging(config):
    """Set up logging configuration"""
    log_level = getattr(logging, config.get('log_level', 'INFO'))
    
    # Create logs directory
    Path('logs').mkdir(exist_ok=True)
    
    # Configure logging
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    handlers = []
    
    if config.get('log_to_console', True):
        handlers.append(logging.StreamHandler())
    
    if config.get('log_to_file', True):
        log_file = f"logs/system_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=handlers
    )
    
    return logging.getLogger(__name__)


def run_backtest_mode(config, logger):
    """Run backtest mode"""
    logger.info("Running in BACKTEST mode")
    
    # Initialize data loader
    data_loader = DataLoader()
    
    # Get symbols
    symbols = config['symbols']
    
    for symbol in symbols:
        logger.info(f"Processing {symbol}")
        
        # Check if CSV data exists
        csv_file = Path(f"data/{symbol}_{config['base_tf']}.csv")
        
        if not csv_file.exists():
            logger.warning(f"Data file not found: {csv_file}")
            logger.info(f"Attempting to download historical data for {symbol}")
            
            # Download data from Binance
            try:
                downloader = BinanceDownloader()
                downloader.download_klines(
                    symbol=symbol,
                    interval=config['base_tf'],
                    start_date=config['backtest_start_date'],
                    end_date=config['backtest_end_date'],
                    output_file=str(csv_file)  # ← Saves to file
                )
                logger.info(f"Downloaded data for {symbol}")
            except Exception as e:
                logger.error(f"Failed to download data for {symbol}: {e}")
                continue

        # Load from CSV (whether just downloaded or previously existing)
        df = data_loader.load_csv(str(csv_file), symbol)  # ← Always loads from CSV
        logger.info(f"Loaded {len(df)} bars from {csv_file}")
        # Filter date range
        df = data_loader.filter_date_range(
            df,
            config['backtest_start_date'],
            config['backtest_end_date']
        )
        
        # Add this check:
        if len(df) == 0:
            logger.error(f"No data for {symbol} in date range {config['backtest_start_date']} to {config['backtest_end_date']}")
            continue

        logger.info(f"After filtering: {len(df)} bars from {df.index[0]} to {df.index[-1]}")

        # Run backtest
        backtest = BacktestEngine(config)
        results = backtest.run_backtest(df, symbol)
        
        # Export results
        backtest.export_results()


def run_paper_mode(config, logger):
    """Run paper trading mode"""
    logger.info("Running in PAPER TRADING mode")
    logger.warning("Paper trading mode not fully implemented yet")
    logger.info("Paper mode would run live but with simulated execution")
    
    # TODO: Implement real-time paper trading
    # This would:
    # 1. Connect to Binance WebSocket for real-time data
    # 2. Run strategy in real-time
    # 3. Simulate order execution
    # 4. Track performance
    
    print("\nPaper trading mode:")
    print("- Would connect to live market data")
    print("- Run strategy in real-time")
    print("- Simulate order execution (no real trades)")
    print("- Track performance")
    print("\nTo implement: Set up WebSocket connections and real-time event loop")


def run_live_mode(config, logger):
    """Run live trading mode"""
    logger.info("Running in LIVE TRADING mode")
    
    # Safety check
    if not config.get('enable_live', False):
        logger.error("Live trading is disabled in config!")
        logger.error("Set 'enable_live: true' in config.yaml to enable live trading")
        sys.exit(1)
    
    # Get API credentials
    api_key, api_secret = config.get_api_credentials()
    
    if not api_key or not api_secret:
        logger.error("Binance API credentials not found!")
        logger.error("Set BINANCE_API_KEY and BINANCE_SECRET_KEY environment variables")
        sys.exit(1)
    
    logger.warning("LIVE TRADING MODE - Real money at risk!")
    logger.warning("Live trading mode not fully implemented yet")
    
    # TODO: Implement live trading
    # This would:
    # 1. Connect to Binance API
    # 2. Set up WebSocket for real-time data
    # 3. Run strategy in real-time
    # 4. Execute real orders
    # 5. Monitor positions
    # 6. Implement safety features (heartbeat, reconnection, etc.)
    
    print("\nLive trading mode:")
    print("- Would connect to Binance API")
    print("- Execute real orders")
    print("- Monitor positions in real-time")
    print("- Implement safety features (kill switch, position reconciliation, etc.)")
    print("\nTo implement: Set up production-grade order execution and monitoring")


def main():
    """Main entry point"""
    print("""
╔════════════════════════════════════════════════════════════╗
║   Independent SR Trading System                            ║
║   Support/Resistance Strategy for Binance Spot            ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    # Load environment variables
    load_dotenv()
    
    # Load configuration
    try:
        config = get_config()
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)
    
    # Setup logging
    logger = setup_logging(config)
    
    # Get mode
    mode = config['mode'].lower()
    logger.info(f"System mode: {mode}")
    
    # Route to appropriate mode
    try:
        if mode == 'backtest':
            run_backtest_mode(config, logger)
        elif mode == 'paper':
            run_paper_mode(config, logger)
        elif mode == 'live':
            run_live_mode(config, logger)
        else:
            logger.error(f"Invalid mode: {mode}")
            logger.error("Mode must be 'backtest', 'paper', or 'live'")
            sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
        print("\nShutting down gracefully...")
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    
    logger.info("System shutdown complete")


if __name__ == "__main__":
    main()
