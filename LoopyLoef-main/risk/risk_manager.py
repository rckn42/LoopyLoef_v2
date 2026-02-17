"""
Risk manager module.
Enforces risk limits and implements kill switch.
"""
from typing import Dict, List
from datetime import datetime, timedelta


class RiskManager:
    """Manage risk limits and exposure"""
    
    def __init__(
        self,
        max_gross_alloc: float = 0.275,
        max_open_trades: int = 5,
        max_daily_loss: float = 0.05
    ):
        """
        Initialize risk manager.
        
        Args:
            max_gross_alloc: Maximum total exposure as % of equity (e.g., 0.275 = 27.5%)
            max_open_trades: Maximum number of concurrent open positions
            max_daily_loss: Maximum daily loss % that triggers kill switch
        """
        self.max_gross_alloc = max_gross_alloc
        self.max_open_trades = max_open_trades
        self.max_daily_loss = max_daily_loss
        
        # Track daily performance
        self.daily_pnl = 0.0
        self.daily_start_equity = 0.0
        self.current_date = None
        self.kill_switch_active = False
    
    def check_new_trade(
        self,
        equity: float,
        position_value: float,
        open_positions: List[Dict]
    ) -> tuple[bool, str]:
        """
        Check if a new trade is allowed based on risk limits.
        
        Args:
            equity: Current account equity
            position_value: Value of proposed new position
            open_positions: List of currently open positions
        
        Returns:
            (allowed: bool, reason: str)
        """
        # Check kill switch
        if self.kill_switch_active:
            return False, "Kill switch active (max daily loss exceeded)"
        
        # Check max open trades
        if len(open_positions) >= self.max_open_trades:
            return False, f"Maximum open trades reached ({self.max_open_trades})"
        
        # Calculate current exposure
        current_exposure = sum(pos.get('position_value', 0) for pos in open_positions)
        total_exposure = current_exposure + position_value
        exposure_pct = total_exposure / equity
        
        # Check max gross allocation
        if exposure_pct > self.max_gross_alloc:
            return False, f"Maximum gross allocation exceeded ({exposure_pct:.1%} > {self.max_gross_alloc:.1%})"
        
        return True, "Trade allowed"
    
    def update_daily_pnl(self, current_equity: float, current_date: datetime):
        """
        Update daily P&L tracking and check for kill switch trigger.
        
        Args:
            current_equity: Current account equity
            current_date: Current trading date
        """
        # Reset daily tracking on new day
        if self.current_date is None or current_date.date() != self.current_date.date():
            self.current_date = current_date
            self.daily_start_equity = current_equity
            self.daily_pnl = 0.0
            self.kill_switch_active = False
        
        # Calculate daily P&L
        self.daily_pnl = current_equity - self.daily_start_equity
        daily_return = self.daily_pnl / self.daily_start_equity
        
        # Check kill switch threshold
        if daily_return <= -self.max_daily_loss:
            self.kill_switch_active = True
    
    def activate_kill_switch(self):
        """Manually activate kill switch (emergency stop)"""
        self.kill_switch_active = True
    
    def deactivate_kill_switch(self):
        """Deactivate kill switch (for next trading day)"""
        self.kill_switch_active = False
    
    def get_max_position_value(self, equity: float, open_positions: List[Dict]) -> float:
        """
        Calculate maximum allowed position value for new trade.
        
        Args:
            equity: Current account equity
            open_positions: List of currently open positions
        
        Returns:
            Maximum position value allowed
        """
        # Calculate current exposure
        current_exposure = sum(pos.get('position_value', 0) for pos in open_positions)
        
        # Calculate remaining allocation
        max_total = equity * self.max_gross_alloc
        remaining = max_total - current_exposure
        
        return max(0, remaining)
    
    def get_risk_status(self, equity: float, open_positions: List[Dict]) -> Dict:
        """
        Get current risk status.
        
        Args:
            equity: Current account equity
            open_positions: List of currently open positions
        
        Returns:
            Dict with risk metrics
        """
        current_exposure = sum(pos.get('position_value', 0) for pos in open_positions)
        exposure_pct = current_exposure / equity if equity > 0 else 0
        
        daily_return = self.daily_pnl / self.daily_start_equity if self.daily_start_equity > 0 else 0
        
        return {
            'equity': equity,
            'open_positions': len(open_positions),
            'current_exposure': current_exposure,
            'exposure_percentage': exposure_pct,
            'max_exposure_percentage': self.max_gross_alloc,
            'remaining_slots': max(0, self.max_open_trades - len(open_positions)),
            'daily_pnl': self.daily_pnl,
            'daily_return': daily_return,
            'kill_switch_active': self.kill_switch_active,
            'max_daily_loss': self.max_daily_loss
        }
