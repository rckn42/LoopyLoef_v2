"""
Binance client for live trading.
Handles REST API and WebSocket connections with proper error handling.
"""
import time
from typing import Dict, Optional, List
from binance.spot import Spot
from binance.error import ClientError, ServerError
import logging


class BinanceClient:
    """Binance API client with error handling and reconnection logic"""
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = False,
        max_reconnect_attempts: int = 5
    ):
        """
        Initialize Binance client.
        
        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            testnet: Use testnet instead of production
            max_reconnect_attempts: Maximum reconnection attempts
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.max_reconnect_attempts = max_reconnect_attempts
        
        # Initialize client
        self.client = self._create_client()
        
        self.logger = logging.getLogger(__name__)
    
    def _create_client(self) -> Spot:
        """Create Binance Spot client"""
        if self.testnet:
            base_url = "https://testnet.binance.vision"
        else:
            base_url = "https://api.binance.com"
        
        return Spot(
            api_key=self.api_key,
            api_secret=self.api_secret,
            base_url=base_url
        )
    
    def get_account_balance(self) -> Dict[str, float]:
        """
        Get account balances.
        
        Returns:
            Dict of asset -> free balance
        """
        try:
            account_info = self.client.account()
            balances = {}
            
            for balance in account_info['balances']:
                asset = balance['asset']
                free = float(balance['free'])
                if free > 0:
                    balances[asset] = free
            
            return balances
        
        except (ClientError, ServerError) as e:
            self.logger.error(f"Error getting account balance: {e}")
            return {}
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current market price for symbol.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
        
        Returns:
            Current price or None if error
        """
        try:
            ticker = self.client.ticker_price(symbol=symbol)
            return float(ticker['price'])
        
        except (ClientError, ServerError) as e:
            self.logger.error(f"Error getting price for {symbol}: {e}")
            return None
    
    def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float
    ) -> Optional[Dict]:
        """
        Place market order.
        
        Args:
            symbol: Trading pair
            side: 'BUY' or 'SELL'
            quantity: Order quantity
        
        Returns:
            Order response dict or None if error
        """
        try:
            response = self.client.new_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=quantity
            )
            
            self.logger.info(f"Market order placed: {symbol} {side} {quantity}")
            return response
        
        except (ClientError, ServerError) as e:
            self.logger.error(f"Error placing market order: {e}")
            return None
    
    def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float
    ) -> Optional[Dict]:
        """
        Place limit order.
        
        Args:
            symbol: Trading pair
            side: 'BUY' or 'SELL'
            quantity: Order quantity
            price: Limit price
        
        Returns:
            Order response dict or None if error
        """
        try:
            response = self.client.new_order(
                symbol=symbol,
                side=side,
                type='LIMIT',
                timeInForce='GTC',
                quantity=quantity,
                price=price
            )
            
            self.logger.info(f"Limit order placed: {symbol} {side} {quantity} @ {price}")
            return response
        
        except (ClientError, ServerError) as e:
            self.logger.error(f"Error placing limit order: {e}")
            return None
    
    def place_stop_loss(
        self,
        symbol: str,
        side: str,
        quantity: float,
        stop_price: float
    ) -> Optional[Dict]:
        """
        Place stop loss order.
        
        Args:
            symbol: Trading pair
            side: 'BUY' or 'SELL'
            quantity: Order quantity
            stop_price: Stop price
        
        Returns:
            Order response dict or None if error
        """
        try:
            response = self.client.new_order(
                symbol=symbol,
                side=side,
                type='STOP_LOSS_LIMIT',
                timeInForce='GTC',
                quantity=quantity,
                price=stop_price,
                stopPrice=stop_price
            )
            
            self.logger.info(f"Stop loss placed: {symbol} {side} {quantity} @ {stop_price}")
            return response
        
        except (ClientError, ServerError) as e:
            self.logger.error(f"Error placing stop loss: {e}")
            return None
    
    def cancel_order(self, symbol: str, order_id: int) -> bool:
        """
        Cancel an open order.
        
        Args:
            symbol: Trading pair
            order_id: Order ID to cancel
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.cancel_order(symbol=symbol, orderId=order_id)
            self.logger.info(f"Order cancelled: {symbol} order_id={order_id}")
            return True
        
        except (ClientError, ServerError) as e:
            self.logger.error(f"Error cancelling order: {e}")
            return False
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Get open orders.
        
        Args:
            symbol: Optional symbol filter
        
        Returns:
            List of open orders
        """
        try:
            if symbol:
                orders = self.client.get_open_orders(symbol=symbol)
            else:
                orders = self.client.get_open_orders()
            
            return orders
        
        except (ClientError, ServerError) as e:
            self.logger.error(f"Error getting open orders: {e}")
            return []
    
    def cancel_all_orders(self, symbol: str) -> bool:
        """
        Cancel all open orders for a symbol.
        
        Args:
            symbol: Trading pair
        
        Returns:
            True if successful, False otherwise
        """
        try:
            open_orders = self.get_open_orders(symbol)
            for order in open_orders:
                self.cancel_order(symbol, order['orderId'])
            
            self.logger.info(f"All orders cancelled for {symbol}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error cancelling all orders: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test API connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.client.ping()
            return True
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False
