"""
Binance historical data downloader.
Downloads OHLCV data from Binance and saves to CSV.
"""
import time
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
from binance.spot import Spot
from binance.error import ClientError


class BinanceDownloader:
    """Download historical OHLCV data from Binance"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """
        Initialize Binance client.
        API keys are optional for public data endpoints.
        """
        self.client = Spot(api_key=api_key, api_secret=api_secret)
    
    def download_klines(
        self,
        symbol: str,
        interval: str,
        start_date: str,
        end_date: str,
        output_file: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Download historical klines (candlestick) data.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            interval: Kline interval (e.g., '1h', '30m')
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            output_file: Optional CSV file to save data
        
        Returns:
            DataFrame with OHLCV data
        """
        # Convert dates to timestamps
        start_ts = int(pd.to_datetime(start_date).timestamp() * 1000)
        end_ts = int(pd.to_datetime(end_date).timestamp() * 1000)
        
        # Map interval to Binance format
        interval_map = {
            '1m': '1m',
            '5m': '5m',
            '15m': '15m',
            '30m': '30m',
            '1h': '1h',
            '2h': '2h',
            '3h': '3h',
            '4h': '4h',
            '1d': '1d'
        }
        
        if interval not in interval_map:
            raise ValueError(f"Unsupported interval: {interval}")
        
        binance_interval = interval_map[interval]
        
        # Download data in chunks (Binance limit is 1000 klines per request)
        all_klines = []
        current_ts = start_ts
        limit = 1000
        
        print(f"Downloading {symbol} {interval} data from {start_date} to {end_date}...")
        
        while current_ts < end_ts:
            try:
                klines = self.client.klines(
                    symbol=symbol,
                    interval=binance_interval,
                    startTime=current_ts,
                    endTime=end_ts,
                    limit=limit
                )
                
                if not klines:
                    break
                
                all_klines.extend(klines)
                
                # Update timestamp for next batch
                current_ts = klines[-1][0] + 1
                
                # Rate limiting
                time.sleep(0.1)
                
                print(f"Downloaded {len(all_klines)} klines...", end='\r')
                
            except ClientError as e:
                print(f"\nError downloading data: {e}")
                break
        
        print(f"\nTotal klines downloaded: {len(all_klines)}")
        
        # Convert to DataFrame
        df = self._klines_to_dataframe(all_klines)
        
        # Save to CSV if specified
        if output_file:
            df.to_csv(output_file, index=False)
            print(f"Data saved to {output_file}")
        
        return df
    
    def _klines_to_dataframe(self, klines: list) -> pd.DataFrame:
        """
        Convert Binance klines to DataFrame.
        
        Binance kline format:
        [
            0: Open time,
            1: Open,
            2: High,
            3: Low,
            4: Close,
            5: Volume,
            6: Close time,
            7: Quote asset volume,
            8: Number of trades,
            9: Taker buy base asset volume,
            10: Taker buy quote asset volume,
            11: Ignore
        ]
        """
        df = pd.DataFrame(klines, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades',
            'taker_buy_base', 'taker_buy_quote', 'ignore'
        ])
        
        # Convert timestamp to datetime (UTC)
        df['timestamp'] = pd.to_datetime(df['open_time'], unit='ms', utc=True)
        
        # Select and rename columns
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        
        # Convert price and volume to float
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        return df
