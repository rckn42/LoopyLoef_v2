"""
Position sizing module.
Calculates position size based on risk per trade and account equity.
"""
from typing import Dict


class PositionSizer:
    """Calculate position sizes based on risk parameters"""
    
    def __init__(self, risk_per_trade: float = 0.0275):
        """
        Initialize position sizer.
        
        Args:
            risk_per_trade: Percentage of equity to risk per trade (e.g., 0.0275 = 2.75%)
        """
        self.risk_per_trade = risk_per_trade
    
    def calculate_position_size(
        self,
        equity: float,
        entry_price: float,
        stop_loss: float,
        max_position_value: float = None
    ) -> Dict:
        """
        Calculate position size based on fixed risk percentage.
        
        Args:
            equity: Current account equity
            entry_price: Planned entry price
            stop_loss: Stop loss price
            max_position_value: Optional maximum position value cap
        
        Returns:
            Dict with position size details
        """
        # Calculate risk amount in dollars
        risk_amount = equity * self.risk_per_trade
        
        # Calculate risk per share
        risk_per_share = abs(entry_price - stop_loss)
        
        if risk_per_share == 0:
            return {
                'quantity': 0,
                'position_value': 0,
                'risk_amount': 0,
                'error': 'Invalid stop loss (risk_per_share = 0)'
            }
        
        # Calculate position size in shares
        quantity = risk_amount / risk_per_share
        
        # Calculate position value
        position_value = quantity * entry_price
        
        # Apply position value cap if specified
        if max_position_value and position_value > max_position_value:
            quantity = max_position_value / entry_price
            position_value = max_position_value
            actual_risk = quantity * risk_per_share
        else:
            actual_risk = risk_amount
        
        return {
            'quantity': quantity,
            'position_value': position_value,
            'risk_amount': actual_risk,
            'risk_percentage': actual_risk / equity,
            'risk_per_share': risk_per_share,
            'r_multiple': 1.0  # By definition, risking 1R
        }
    
    def calculate_with_slippage_and_fees(
        self,
        equity: float,
        entry_price: float,
        stop_loss: float,
        slippage_pct: float = 0.001,
        fee_pct: float = 0.001,
        max_position_value: float = None
    ) -> Dict:
        """
        Calculate position size accounting for slippage and fees.
        
        Args:
            equity: Current account equity
            entry_price: Planned entry price
            stop_loss: Stop loss price
            slippage_pct: Expected slippage percentage
            fee_pct: Trading fee percentage
            max_position_value: Optional maximum position value cap
        
        Returns:
            Dict with adjusted position size details
        """
        # Adjust entry price for slippage
        if entry_price > stop_loss:  # Long position
            adjusted_entry = entry_price * (1 + slippage_pct)
        else:  # Short position
            adjusted_entry = entry_price * (1 - slippage_pct)
        
        # Calculate base position size
        base_size = self.calculate_position_size(equity, adjusted_entry, stop_loss, max_position_value)
        
        if base_size['quantity'] == 0:
            return base_size
        
        # Calculate total fees (entry + exit)
        entry_fee = base_size['position_value'] * fee_pct
        exit_fee = base_size['position_value'] * fee_pct
        total_fees = entry_fee + exit_fee
        
        # Adjust risk to account for fees
        total_cost = base_size['risk_amount'] + total_fees
        
        # Recalculate position size with fees
        available_risk = equity * self.risk_per_trade
        if total_cost > available_risk:
            # Reduce position size to fit within risk budget
            adjustment_factor = available_risk / total_cost
            adjusted_quantity = base_size['quantity'] * adjustment_factor
        else:
            adjusted_quantity = base_size['quantity']
        
        adjusted_position_value = adjusted_quantity * adjusted_entry
        
        return {
            'quantity': adjusted_quantity,
            'position_value': adjusted_position_value,
            'entry_price': adjusted_entry,
            'risk_amount': base_size['risk_amount'],
            'risk_percentage': base_size['risk_amount'] / equity,
            'risk_per_share': base_size['risk_per_share'],
            'fees': total_fees,
            'slippage': adjusted_entry - entry_price,
            'r_multiple': 1.0
        }
