"""
Performance metrics calculator.
Calculates comprehensive trading performance statistics.
"""
import pandas as pd
import numpy as np
from typing import Dict, List


class PerformanceMetrics:
    """Calculate trading performance metrics"""
    
    def __init__(self, equity_curve: List[Dict], trades: List[Dict], initial_capital: float):
        """
        Initialize metrics calculator.
        
        Args:
            equity_curve: List of equity snapshots with timestamp and equity
            trades: List of closed trade dictionaries
            initial_capital: Starting capital
        """
        self.equity_curve = equity_curve
        self.trades = trades
        self.initial_capital = initial_capital
        
        # Convert to DataFrames for easier analysis
        if equity_curve:
            self.equity_df = pd.DataFrame(equity_curve)
            if 'timestamp' in self.equity_df.columns:
                self.equity_df.set_index('timestamp', inplace=True)
        else:
            self.equity_df = pd.DataFrame()
        
        if trades:
            self.trades_df = pd.DataFrame(trades)
        else:
            self.trades_df = pd.DataFrame()
    
    def calculate_all_metrics(self) -> Dict:
        """Calculate all performance metrics"""
        metrics = {
            # Returns
            'total_return': self.calculate_total_return(),
            'cagr': self.calculate_cagr(),
            
            # Risk metrics
            'sharpe_ratio': self.calculate_sharpe_ratio(),
            'sortino_ratio': self.calculate_sortino_ratio(),
            'max_drawdown': self.calculate_max_drawdown(),
            'max_drawdown_duration': self.calculate_max_drawdown_duration(),
            
            # Trade statistics
            'total_trades': len(self.trades),
            'winning_trades': self.count_winning_trades(),
            'losing_trades': self.count_losing_trades(),
            'win_rate': self.calculate_win_rate(),
            
            # P&L metrics
            'profit_factor': self.calculate_profit_factor(),
            'expectancy': self.calculate_expectancy(),
            'average_win': self.calculate_average_win(),
            'average_loss': self.calculate_average_loss(),
            'largest_win': self.calculate_largest_win(),
            'largest_loss': self.calculate_largest_loss(),
            
            # R-multiple statistics
            'average_r_multiple': self.calculate_average_r_multiple(),
            'median_r_multiple': self.calculate_median_r_multiple(),
            
            # System quality
            'sqn': self.calculate_sqn()
        }
        
        return metrics
    
    def calculate_total_return(self) -> float:
        """Calculate total return percentage"""
        if self.equity_df.empty:
            return 0.0
        
        final_equity = self.equity_df['equity'].iloc[-1]
        return (final_equity - self.initial_capital) / self.initial_capital
    
    def calculate_cagr(self) -> float:
        """Calculate Compound Annual Growth Rate"""
        if self.equity_df.empty or len(self.equity_df) < 2:
            return 0.0
        
        total_return = self.calculate_total_return()
        
        # Calculate time period in years
        start_date = self.equity_df.index[0]
        end_date = self.equity_df.index[-1]
        days = (end_date - start_date).days
        years = days / 365.25
        
        if years == 0:
            return 0.0
        
        cagr = (1 + total_return) ** (1 / years) - 1
        return cagr
    
    def calculate_sharpe_ratio(self, risk_free_rate: float = 0.0) -> float:
        """Calculate Sharpe ratio"""
        if self.equity_df.empty or len(self.equity_df) < 2:
            return 0.0
        
        returns = self.equity_df['equity'].pct_change().dropna()
        
        if returns.std() == 0:
            return 0.0
        
        excess_returns = returns - risk_free_rate / 252  # Daily risk-free rate
        sharpe = excess_returns.mean() / returns.std() * np.sqrt(252)  # Annualized
        
        return sharpe
    
    def calculate_sortino_ratio(self, risk_free_rate: float = 0.0) -> float:
        """Calculate Sortino ratio (only penalizes downside volatility)"""
        if self.equity_df.empty or len(self.equity_df) < 2:
            return 0.0
        
        returns = self.equity_df['equity'].pct_change().dropna()
        excess_returns = returns - risk_free_rate / 252
        
        # Only consider negative returns for downside deviation
        negative_returns = returns[returns < 0]
        
        if len(negative_returns) == 0 or negative_returns.std() == 0:
            return 0.0
        
        downside_std = negative_returns.std()
        sortino = excess_returns.mean() / downside_std * np.sqrt(252)  # Annualized
        
        return sortino
    
    def calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown percentage"""
        if self.equity_df.empty:
            return 0.0
        
        equity = self.equity_df['equity']
        cummax = equity.cummax()
        drawdown = (equity - cummax) / cummax
        
        return drawdown.min()
    
    def calculate_max_drawdown_duration(self) -> int:
        """Calculate maximum drawdown duration in days"""
        if self.equity_df.empty:
            return 0
        
        equity = self.equity_df['equity']
        cummax = equity.cummax()
        drawdown = (equity - cummax) / cummax
        
        # Find periods in drawdown
        in_drawdown = drawdown < 0
        
        if not in_drawdown.any():
            return 0
        
        # Calculate consecutive drawdown periods
        drawdown_periods = []
        current_period = 0
        
        for is_dd in in_drawdown:
            if is_dd:
                current_period += 1
            else:
                if current_period > 0:
                    drawdown_periods.append(current_period)
                current_period = 0
        
        if current_period > 0:
            drawdown_periods.append(current_period)
        
        return max(drawdown_periods) if drawdown_periods else 0
    
    def count_winning_trades(self) -> int:
        """Count winning trades"""
        if self.trades_df.empty:
            return 0
        return (self.trades_df['pnl'] > 0).sum()
    
    def count_losing_trades(self) -> int:
        """Count losing trades"""
        if self.trades_df.empty:
            return 0
        return (self.trades_df['pnl'] < 0).sum()
    
    def calculate_win_rate(self) -> float:
        """Calculate win rate"""
        total = len(self.trades)
        if total == 0:
            return 0.0
        
        winning = self.count_winning_trades()
        return winning / total
    
    def calculate_profit_factor(self) -> float:
        """Calculate profit factor (gross profit / gross loss)"""
        if self.trades_df.empty:
            return 0.0
        
        gross_profit = self.trades_df[self.trades_df['pnl'] > 0]['pnl'].sum()
        gross_loss = abs(self.trades_df[self.trades_df['pnl'] < 0]['pnl'].sum())
        
        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0
        
        return gross_profit / gross_loss
    
    def calculate_expectancy(self) -> float:
        """Calculate expectancy (average profit per trade)"""
        if self.trades_df.empty:
            return 0.0
        
        return self.trades_df['pnl'].mean()
    
    def calculate_average_win(self) -> float:
        """Calculate average winning trade"""
        if self.trades_df.empty:
            return 0.0
        
        wins = self.trades_df[self.trades_df['pnl'] > 0]['pnl']
        return wins.mean() if len(wins) > 0 else 0.0
    
    def calculate_average_loss(self) -> float:
        """Calculate average losing trade"""
        if self.trades_df.empty:
            return 0.0
        
        losses = self.trades_df[self.trades_df['pnl'] < 0]['pnl']
        return losses.mean() if len(losses) > 0 else 0.0
    
    def calculate_largest_win(self) -> float:
        """Calculate largest winning trade"""
        if self.trades_df.empty:
            return 0.0
        
        wins = self.trades_df[self.trades_df['pnl'] > 0]['pnl']
        return wins.max() if len(wins) > 0 else 0.0
    
    def calculate_largest_loss(self) -> float:
        """Calculate largest losing trade"""
        if self.trades_df.empty:
            return 0.0
        
        losses = self.trades_df[self.trades_df['pnl'] < 0]['pnl']
        return losses.min() if len(losses) > 0 else 0.0
    
    def calculate_average_r_multiple(self) -> float:
        """Calculate average R-multiple"""
        if self.trades_df.empty or 'r_multiple' not in self.trades_df.columns:
            return 0.0
        
        return self.trades_df['r_multiple'].mean()
    
    def calculate_median_r_multiple(self) -> float:
        """Calculate median R-multiple"""
        if self.trades_df.empty or 'r_multiple' not in self.trades_df.columns:
            return 0.0
        
        return self.trades_df['r_multiple'].median()
    
    def calculate_sqn(self) -> float:
        """
        Calculate System Quality Number (SQN).
        SQN = sqrt(N) * (avg R / stdev R)
        """
        if self.trades_df.empty or 'r_multiple' not in self.trades_df.columns:
            return 0.0
        
        r_multiples = self.trades_df['r_multiple']
        n = len(r_multiples)
        
        if n == 0 or r_multiples.std() == 0:
            return 0.0
        
        sqn = np.sqrt(n) * (r_multiples.mean() / r_multiples.std())
        return sqn
