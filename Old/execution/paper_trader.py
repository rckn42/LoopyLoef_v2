"""
Paper trading execution module.
Simulates order execution for backtesting and paper trading.
"""
from typing import Dict, Optional
from datetime import datetime
from execution.order_manager import OrderManager, Trade


class PaperTrader:
    """Simulate order execution without real trading"""
    
    def __init__(
        self,
        initial_capital: float,
        slippage_pct: float = 0.001,
        maker_fee: float = 0.001,
        taker_fee: float = 0.001
    ):
        """
        Initialize paper trader.
        
        Args:
            initial_capital: Starting capital
            slippage_pct: Slippage percentage
            maker_fee: Maker fee percentage
            taker_fee: Taker fee percentage
        """
        self.initial_capital = initial_capital
        self.equity = initial_capital
        self.cash = initial_capital
        self.slippage_pct = slippage_pct
        self.maker_fee = maker_fee
        self.taker_fee = taker_fee
        
        self.order_manager = OrderManager()
        
        # Track equity curve
        self.equity_curve = []
    
    def execute_entry(
        self,
        symbol: str,
        direction: str,
        entry_price: float,
        quantity: float,
        stop_loss: float,
        take_profit: float,
        timestamp: datetime,
        order_type: str = 'market'
    ) -> Optional[Trade]:
        """
        Execute entry order.
        
        Args:
            symbol: Trading symbol
            direction: 'long' or 'short'
            entry_price: Entry price
            quantity: Position size
            stop_loss: Stop loss price
            take_profit: Take profit price
            timestamp: Execution timestamp
            order_type: 'market' or 'limit'
        
        Returns:
            Trade object if successful, None otherwise
        """
        # Check if already have position in this symbol
        if self.order_manager.has_open_position(symbol):
            return None
        
        # Apply slippage for market orders
        if order_type == 'market':
            if direction == 'long':
                fill_price = entry_price * (1 + self.slippage_pct)
            else:  # short
                fill_price = entry_price * (1 - self.slippage_pct)
        else:
            fill_price = entry_price
        
        # Calculate position value and fees
        position_value = fill_price * quantity
        fee = position_value * self.taker_fee
        total_cost = position_value + fee
        
        # Check if sufficient cash
        if total_cost > self.cash:
            return None
        
        # Create trade
        trade = self.order_manager.create_trade(
            symbol=symbol,
            direction=direction,
            entry_price=fill_price,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit,
            timestamp=timestamp
        )
        
        # Update cash
        self.cash -= total_cost
        
        return trade
    
    def execute_exit(
        self,
        symbol: str,
        exit_price: float,
        timestamp: datetime,
        reason: str
    ) -> Optional[Trade]:
        """
        Execute exit order.
        
        Args:
            symbol: Trading symbol
            exit_price: Exit price
            timestamp: Execution timestamp
            reason: Exit reason
        
        Returns:
            Closed Trade object if successful, None otherwise
        """
        if not self.order_manager.has_open_position(symbol):
            return None
        
        # Get open trade
        trade = self.order_manager.open_trades[symbol]
        
        # Apply slippage
        if trade.direction == 'long':
            fill_price = exit_price * (1 - self.slippage_pct)
        else:  # short
            fill_price = exit_price * (1 + self.slippage_pct)
        
        # Calculate exit value and fees
        exit_value = fill_price * trade.quantity
        fee = exit_value * self.taker_fee
        
        # Close trade
        closed_trade = self.order_manager.close_trade(
            symbol=symbol,
            exit_price=fill_price,
            exit_timestamp=timestamp,
            reason=reason
        )
        
        # Update cash
        if trade.direction == 'long':
            proceeds = exit_value - fee
        else:  # short
            # For short, we get back the difference
            proceeds = (2 * trade.entry_price * trade.quantity) - exit_value - fee
        
        self.cash += proceeds
        
        # Update equity
        self.equity = self.cash
        
        return closed_trade
    
    def update_equity(self, current_prices: Dict[str, float], timestamp: datetime):
        """
        Update equity based on current market prices.
        
        Args:
            current_prices: Dict of symbol -> current price
            timestamp: Current timestamp
        """
        unrealized_pnl = 0.0
        
        for symbol, trade in self.order_manager.open_trades.items():
            if symbol in current_prices:
                current_price = current_prices[symbol]
                
                if trade.direction == 'long':
                    pnl = (current_price - trade.entry_price) * trade.quantity
                else:  # short
                    pnl = (trade.entry_price - current_price) * trade.quantity
                
                unrealized_pnl += pnl
        
        self.equity = self.cash + unrealized_pnl
        
        # Record equity
        self.equity_curve.append({
            'timestamp': timestamp,
            'equity': self.equity,
            'cash': self.cash,
            'unrealized_pnl': unrealized_pnl
        })
    
    def check_stops(self, symbol: str, current_high: float, current_low: float, timestamp: datetime) -> Optional[Trade]:
        """
        Check and execute stops if hit.
        
        Args:
            symbol: Trading symbol
            current_high: Current bar high
            current_low: Current bar low
            timestamp: Current timestamp
        
        Returns:
            Closed Trade if stop hit, None otherwise
        """
        stop_hit = self.order_manager.check_stops(symbol, current_high, current_low)
        
        if stop_hit:
            reason, exit_price = stop_hit
            return self.execute_exit(symbol, exit_price, timestamp, reason)
        
        return None
    
    def get_equity(self) -> float:
        """Get current equity"""
        return self.equity
    
    def get_cash(self) -> float:
        """Get current cash"""
        return self.cash
    
    def get_equity_curve(self) -> list[Dict]:
        """Get equity curve history"""
        return self.equity_curve
