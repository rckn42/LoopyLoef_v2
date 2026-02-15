"""
Order manager module.
Manages order lifecycle including entry, stop loss, and take profit.
"""
from typing import Dict, Optional
from enum import Enum
from datetime import datetime


class OrderType(Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


class OrderStatus(Enum):
    """Order status"""
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class Trade:
    """Represents a complete trade with entry, stop, and target"""
    
    def __init__(
        self,
        symbol: str,
        direction: str,
        entry_price: float,
        quantity: float,
        stop_loss: float,
        take_profit: float,
        timestamp: datetime
    ):
        self.symbol = symbol
        self.direction = direction  # 'long' or 'short'
        self.entry_price = entry_price
        self.quantity = quantity
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.entry_timestamp = timestamp
        
        # Trade status
        self.status = "open"
        self.exit_price = None
        self.exit_timestamp = None
        self.exit_reason = None
        
        # Performance
        self.pnl = 0.0
        self.pnl_percentage = 0.0
        self.r_multiple = 0.0
        
        # Risk metrics
        self.risk_per_share = abs(entry_price - stop_loss)
        self.position_value = entry_price * quantity
    
    def update_exit(self, exit_price: float, exit_timestamp: datetime, reason: str):
        """Update trade with exit information"""
        self.exit_price = exit_price
        self.exit_timestamp = exit_timestamp
        self.exit_reason = reason
        self.status = "closed"
        
        # Calculate P&L
        if self.direction == 'long':
            self.pnl = (exit_price - self.entry_price) * self.quantity
        else:  # short
            self.pnl = (self.entry_price - exit_price) * self.quantity
        
        self.pnl_percentage = self.pnl / self.position_value
        
        # Calculate R-multiple
        if self.risk_per_share > 0:
            if self.direction == 'long':
                self.r_multiple = (exit_price - self.entry_price) / self.risk_per_share
            else:
                self.r_multiple = (self.entry_price - exit_price) / self.risk_per_share
    
    def to_dict(self) -> Dict:
        """Convert trade to dictionary"""
        return {
            'symbol': self.symbol,
            'direction': self.direction,
            'entry_price': self.entry_price,
            'quantity': self.quantity,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'entry_timestamp': self.entry_timestamp,
            'exit_price': self.exit_price,
            'exit_timestamp': self.exit_timestamp,
            'exit_reason': self.exit_reason,
            'status': self.status,
            'pnl': self.pnl,
            'pnl_percentage': self.pnl_percentage,
            'r_multiple': self.r_multiple,
            'risk_per_share': self.risk_per_share,
            'position_value': self.position_value
        }


class OrderManager:
    """Manage orders and trades"""
    
    def __init__(self):
        self.open_trades: Dict[str, Trade] = {}  # symbol -> Trade
        self.closed_trades: list[Trade] = []
    
    def create_trade(
        self,
        symbol: str,
        direction: str,
        entry_price: float,
        quantity: float,
        stop_loss: float,
        take_profit: float,
        timestamp: datetime
    ) -> Trade:
        """
        Create and register a new trade.
        
        Returns:
            Trade object
        """
        trade = Trade(
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit,
            timestamp=timestamp
        )
        
        self.open_trades[symbol] = trade
        return trade
    
    def close_trade(
        self,
        symbol: str,
        exit_price: float,
        exit_timestamp: datetime,
        reason: str
    ) -> Optional[Trade]:
        """
        Close an open trade.
        
        Args:
            symbol: Trading symbol
            exit_price: Exit price
            exit_timestamp: Exit timestamp
            reason: Exit reason (e.g., 'stop_loss', 'take_profit', 'manual')
        
        Returns:
            Closed Trade object or None if no open trade exists
        """
        if symbol not in self.open_trades:
            return None
        
        trade = self.open_trades.pop(symbol)
        trade.update_exit(exit_price, exit_timestamp, reason)
        self.closed_trades.append(trade)
        
        return trade
    
    def check_stops(self, symbol: str, current_high: float, current_low: float) -> Optional[tuple[str, float]]:
        """
        Check if stop loss or take profit has been hit.
        
        Args:
            symbol: Trading symbol
            current_high: Current bar high
            current_low: Current bar low
        
        Returns:
            (exit_reason, exit_price) if stop hit, None otherwise
        """
        if symbol not in self.open_trades:
            return None
        
        trade = self.open_trades[symbol]
        
        if trade.direction == 'long':
            # Check stop loss
            if current_low <= trade.stop_loss:
                return ('stop_loss', trade.stop_loss)
            
            # Check take profit
            if current_high >= trade.take_profit:
                return ('take_profit', trade.take_profit)
        
        else:  # short
            # Check stop loss
            if current_high >= trade.stop_loss:
                return ('stop_loss', trade.stop_loss)
            
            # Check take profit
            if current_low <= trade.take_profit:
                return ('take_profit', trade.take_profit)
        
        return None
    
    def get_open_positions(self) -> list[Dict]:
        """Get list of open positions"""
        return [trade.to_dict() for trade in self.open_trades.values()]
    
    def get_closed_trades(self) -> list[Dict]:
        """Get list of closed trades"""
        return [trade.to_dict() for trade in self.closed_trades]
    
    def has_open_position(self, symbol: str) -> bool:
        """Check if symbol has an open position"""
        return symbol in self.open_trades
