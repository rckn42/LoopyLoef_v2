"""
Simple validation test for the SR Trading System.
Tests that all components load and basic functionality works.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    try:
        from config.config_loader import get_config
        from data.data_loader import DataLoader
        from strategy.indicators import calculate_atr, calculate_ema
        from strategy.sr_detection import SRDetector
        from strategy.trend_filter import TrendFilter
        from strategy.regime_filter import RegimeFilter
        from strategy.sr_strategy import SRStrategy
        from risk.position_sizer import PositionSizer
        from risk.risk_manager import RiskManager
        from execution.order_manager import OrderManager
        from execution.paper_trader import PaperTrader
        from backtest.backtest_engine import BacktestEngine
        from backtest.metrics import PerformanceMetrics
        
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_config():
    """Test configuration loading"""
    print("\nTesting configuration...")
    
    try:
        from config.config_loader import get_config
        
        config = get_config()
        
        assert config['mode'] == 'backtest'
        assert len(config['symbols']) > 0
        assert config['risk_per_trade'] > 0
        
        print("✓ Configuration loaded successfully")
        print(f"  Mode: {config['mode']}")
        print(f"  Symbols: {config['symbols']}")
        print(f"  Risk per trade: {config['risk_per_trade']}")
        return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False


def test_indicators():
    """Test indicator calculations"""
    print("\nTesting indicators...")
    
    try:
        import pandas as pd
        import numpy as np
        from strategy.indicators import calculate_atr, calculate_ema, detect_swing_highs
        
        # Create sample data
        dates = pd.date_range('2024-01-01', periods=100, freq='1h')
        prices = 100 + np.random.randn(100).cumsum()
        
        df = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': prices + np.random.rand(100),
            'low': prices - np.random.rand(100),
            'close': prices + np.random.randn(100) * 0.5,
            'volume': np.random.randint(1000, 10000, 100)
        })
        
        # Calculate indicators
        atr = calculate_atr(df['high'], df['low'], df['close'])
        ema = calculate_ema(df['close'], 20)
        swings = detect_swing_highs(df['high'], 5)
        
        assert len(atr) == len(df)
        assert len(ema) == len(df)
        assert len(swings) == len(df)
        
        print("✓ Indicators calculated successfully")
        print(f"  ATR range: {atr.min():.2f} - {atr.max():.2f}")
        print(f"  EMA range: {ema.min():.2f} - {ema.max():.2f}")
        print(f"  Swing highs detected: {swings.sum()}")
        return True
    except Exception as e:
        print(f"✗ Indicator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_position_sizing():
    """Test position sizing"""
    print("\nTesting position sizing...")
    
    try:
        from risk.position_sizer import PositionSizer
        
        sizer = PositionSizer(risk_per_trade=0.02)
        
        position = sizer.calculate_position_size(
            equity=10000,
            entry_price=100,
            stop_loss=95
        )
        
        assert position['quantity'] > 0
        assert position['risk_amount'] > 0
        assert position['risk_percentage'] <= 0.02
        
        print("✓ Position sizing works correctly")
        print(f"  Equity: $10,000")
        print(f"  Position size: {position['quantity']:.2f} shares")
        print(f"  Risk amount: ${position['risk_amount']:.2f}")
        return True
    except Exception as e:
        print(f"✗ Position sizing test failed: {e}")
        return False


def test_risk_manager():
    """Test risk manager"""
    print("\nTesting risk manager...")
    
    try:
        from risk.risk_manager import RiskManager
        
        risk_mgr = RiskManager(
            max_gross_alloc=0.3,
            max_open_trades=5,
            max_daily_loss=0.05
        )
        
        # Test new trade check
        allowed, reason = risk_mgr.check_new_trade(
            equity=10000,
            position_value=1000,
            open_positions=[]
        )
        
        assert allowed == True
        
        # Test max trades limit
        fake_positions = [{'position_value': 1000} for _ in range(5)]
        allowed, reason = risk_mgr.check_new_trade(
            equity=10000,
            position_value=1000,
            open_positions=fake_positions
        )
        
        assert allowed == False
        
        print("✓ Risk manager works correctly")
        print(f"  Max trades limit enforced")
        return True
    except Exception as e:
        print(f"✗ Risk manager test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("="*60)
    print("SR Trading System Validation Tests")
    print("="*60)
    
    tests = [
        test_imports,
        test_config,
        test_indicators,
        test_position_sizing,
        test_risk_manager
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"Passed: {sum(results)}/{len(results)}")
    print(f"Failed: {len(results) - sum(results)}/{len(results)}")
    
    if all(results):
        print("\n✓ All tests passed! System is ready.")
        return 0
    else:
        print("\n✗ Some tests failed. Please fix before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
