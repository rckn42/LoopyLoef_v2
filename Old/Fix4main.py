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