"""
Event-driven backtesting engine.
Bar-by-bar simulation with no look-ahead bias.
"""
import pandas as pd
import json
from typing import Dict, List
from datetime import datetime
from pathlib import Path

from strategy.sr_strategy import SRStrategy
from risk.position_sizer import PositionSizer
from risk.risk_manager import RiskManager
from execution.paper_trader import PaperTrader
from backtest.metrics import PerformanceMetrics


class BacktestEngine:
    """Event-driven backtesting engine"""
    
    def __init__(self, config: Dict):
        """
        Initialize backtest engine.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        
        # Initialize components
        self.strategy = SRStrategy(config)
        self.position_sizer = PositionSizer(config['risk_per_trade'])
        self.risk_manager = RiskManager(
            max_gross_alloc=config['max_gross_alloc'],
            max_open_trades=config['max_open_trades'],
            max_daily_loss=config['max_daily_loss']
        )
        self.paper_trader = PaperTrader(
            initial_capital=config['initial_capital'],
            slippage_pct=config['slippage_pct'],
            maker_fee=config['maker_fee'],
            taker_fee=config['taker_fee']
        )
        
        # Track results
        self.results = []
    
    def run_backtest(self, df: pd.DataFrame, symbol: str) -> Dict:
        """
        Run backtest on OHLCV data.
        
        Args:
            df: OHLCV DataFrame with datetime index
            symbol: Trading symbol
        
        Returns:
            Dict with backtest results and metrics
        """
        print(f"\n{'='*60}")
        print(f"Running backtest for {symbol}")
        print(f"Period: {df.index[0]} to {df.index[-1]}")
        print(f"Bars: {len(df)}")
        print(f"Initial Capital: ${self.config['initial_capital']:,.2f}")
        print(f"{'='*60}\n")
        
        # Event-driven simulation (bar by bar)
        for idx in range(len(df)):
            current_bar = df.iloc[idx]
            current_timestamp = df.index[idx]
            current_price = current_bar['close']
            
            # Update risk manager daily tracking
            self.risk_manager.update_daily_pnl(
                self.paper_trader.get_equity(),
                current_timestamp
            )
            
            # Check existing positions for stops
            if self.paper_trader.order_manager.has_open_position(symbol):
                closed_trade = self.paper_trader.check_stops(
                    symbol,
                    current_bar['high'],
                    current_bar['low'],
                    current_timestamp
                )
                
                if closed_trade:
                    print(f"[{current_timestamp}] Trade closed: {closed_trade.exit_reason} | "
                          f"P&L: ${closed_trade.pnl:.2f} ({closed_trade.r_multiple:.2f}R) | "
                          f"Equity: ${self.paper_trader.get_equity():,.2f}")
            
            # Don't enter new trades if kill switch is active
            if self.risk_manager.kill_switch_active:
                continue
            
            # Check for new entry signals (only if no position)
            if not self.paper_trader.order_manager.has_open_position(symbol):
                # Check long setup
                long_signal = self.strategy.check_long_setup(df, idx)
                
                if long_signal:
                    self._process_entry_signal(long_signal, symbol, current_timestamp)
                else:
                    # Check short setup
                    short_signal = self.strategy.check_short_setup(df, idx)
                    
                    if short_signal:
                        self._process_entry_signal(short_signal, symbol, current_timestamp)
            
            # Update equity based on current prices
            self.paper_trader.update_equity({symbol: current_price}, current_timestamp)
        
        # Close any remaining open positions at end
        for symbol_pos in list(self.paper_trader.order_manager.open_trades.keys()):
            final_price = df['close'].iloc[-1]
            final_timestamp = df.index[-1]
            self.paper_trader.execute_exit(symbol_pos, final_price, final_timestamp, 'backtest_end')
        
        # Calculate final metrics
        metrics = self._calculate_metrics()
        
        # Print summary
        self._print_summary(metrics)
        
        return {
            'metrics': metrics,
            'equity_curve': self.paper_trader.get_equity_curve(),
            'trades': self.paper_trader.order_manager.get_closed_trades()
        }
    
    def _process_entry_signal(self, signal: Dict, symbol: str, timestamp: datetime):
        """Process entry signal and execute trade if risk checks pass"""
        
        # Get current equity
        equity = self.paper_trader.get_equity()
        
        # Calculate position size
        max_position_value = self.risk_manager.get_max_position_value(
            equity,
            self.paper_trader.order_manager.get_open_positions()
        )
        
        position_size = self.position_sizer.calculate_with_slippage_and_fees(
            equity=equity,
            entry_price=signal['entry_price'],
            stop_loss=signal['stop_loss'],
            slippage_pct=self.config['slippage_pct'],
            fee_pct=self.config['taker_fee'],
            max_position_value=max_position_value
        )
        
        if position_size['quantity'] == 0:
            return
        
        # Risk check
        allowed, reason = self.risk_manager.check_new_trade(
            equity,
            position_size['position_value'],
            self.paper_trader.order_manager.get_open_positions()
        )
        
        if not allowed:
            return
        
        # Execute entry
        trade = self.paper_trader.execute_entry(
            symbol=symbol,
            direction=signal['direction'],
            entry_price=signal['entry_price'],
            quantity=position_size['quantity'],
            stop_loss=signal['stop_loss'],
            take_profit=signal['take_profit'],
            timestamp=timestamp,
            order_type=self.config.get('order_type', 'market')
        )
        
        if trade:
            print(f"[{timestamp}] {signal['direction'].upper()} entry: {symbol} @ ${signal['entry_price']:.2f} | "
                  f"Size: {position_size['quantity']:.4f} | "
                  f"Stop: ${signal['stop_loss']:.2f} | "
                  f"Target: ${signal['take_profit']:.2f}")
    
    def _calculate_metrics(self) -> Dict:
        """Calculate performance metrics"""
        metrics_calc = PerformanceMetrics(
            equity_curve=self.paper_trader.get_equity_curve(),
            trades=self.paper_trader.order_manager.get_closed_trades(),
            initial_capital=self.config['initial_capital']
        )
        
        return metrics_calc.calculate_all_metrics()
    
    def _print_summary(self, metrics: Dict):
        """Print backtest summary"""
        print(f"\n{'='*60}")
        print("BACKTEST RESULTS")
        print(f"{'='*60}")
        
        print(f"\nPerformance:")
        print(f"  Total Return: {metrics['total_return']:.2%}")
        print(f"  CAGR: {metrics['cagr']:.2%}")
        print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"  Sortino Ratio: {metrics['sortino_ratio']:.2f}")
        print(f"  Max Drawdown: {metrics['max_drawdown']:.2%}")
        print(f"  Max DD Duration: {metrics['max_drawdown_duration']} bars")
        
        print(f"\nTrade Statistics:")
        print(f"  Total Trades: {metrics['total_trades']}")
        print(f"  Win Rate: {metrics['win_rate']:.2%}")
        print(f"  Profit Factor: {metrics['profit_factor']:.2f}")
        print(f"  Expectancy: ${metrics['expectancy']:.2f}")
        
        print(f"\nWinning Trades:")
        print(f"  Count: {metrics['winning_trades']}")
        print(f"  Average: ${metrics['average_win']:.2f}")
        print(f"  Largest: ${metrics['largest_win']:.2f}")
        
        print(f"\nLosing Trades:")
        print(f"  Count: {metrics['losing_trades']}")
        print(f"  Average: ${metrics['average_loss']:.2f}")
        print(f"  Largest: ${metrics['largest_loss']:.2f}")
        
        print(f"\nR-Multiple Statistics:")
        print(f"  Average: {metrics['average_r_multiple']:.2f}R")
        print(f"  Median: {metrics['median_r_multiple']:.2f}R")
        print(f"  SQN: {metrics['sqn']:.2f}")
        
        print(f"\n{'='*60}\n")
    
    def export_results(self, output_dir: str = "logs"):
        """Export results to CSV and JSON files"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Export equity curve
        if self.paper_trader.get_equity_curve():
            equity_df = pd.DataFrame(self.paper_trader.get_equity_curve())
            equity_file = output_path / "equity.csv"
            equity_df.to_csv(equity_file, index=False)
            print(f"Equity curve saved to {equity_file}")
        
        # Export trades
        if self.paper_trader.order_manager.get_closed_trades():
            trades_df = pd.DataFrame(self.paper_trader.order_manager.get_closed_trades())
            trades_file = output_path / "trades.csv"
            trades_df.to_csv(trades_file, index=False)
            print(f"Trades saved to {trades_file}")
        
        # Export metrics
        metrics = self._calculate_metrics()
        stats_file = output_path / "stats.json"
        with open(stats_file, 'w') as f:
            json.dump(metrics, f, indent=2, default=str)
        print(f"Statistics saved to {stats_file}")
