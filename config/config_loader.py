"""
Configuration loader and validator.
Loads config.yaml and validates all parameters.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any


class ConfigLoader:
    """Load and validate configuration from config.yaml"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        return config
    
    def _validate_config(self):
        """Validate configuration parameters"""
        # Validate mode
        valid_modes = ['backtest', 'paper', 'live']
        if self.config['mode'] not in valid_modes:
            raise ValueError(f"Invalid mode: {self.config['mode']}. Must be one of {valid_modes}")
        
        # Validate live trading safety
        if self.config['mode'] == 'live' and not self.config.get('enable_live', False):
            raise ValueError("Live trading requires enable_live: true in config")
        
        # Validate timeframe
        valid_tfs = ['30m', '1h', '2h', '3h', '4h']
        if self.config['base_tf'] not in valid_tfs:
            raise ValueError(f"Invalid base_tf: {self.config['base_tf']}. Must be one of {valid_tfs}")
        
        # Validate risk parameters
        if not 0 < self.config['risk_per_trade'] <= 0.1:
            raise ValueError("risk_per_trade must be between 0 and 0.1 (10%)")
        
        if not 0 < self.config['max_gross_alloc'] <= 1.0:
            raise ValueError("max_gross_alloc must be between 0 and 1.0 (100%)")
        
        if self.config['max_open_trades'] < 1:
            raise ValueError("max_open_trades must be at least 1")
        
        # Validate symbols
        if not self.config.get('symbols'):
            raise ValueError("At least one symbol must be specified")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        return self.config.get(key, default)
    
    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access"""
        return self.config[key]
    
    def get_api_credentials(self) -> tuple:
        """Get API credentials from environment variables"""
        api_key = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_SECRET_KEY')
        
        if self.config['mode'] == 'live' and (not api_key or not api_secret):
            raise ValueError("Live mode requires BINANCE_API_KEY and BINANCE_SECRET_KEY environment variables")
        
        return api_key, api_secret


# Global config instance
_config_instance = None


def get_config(config_path: str = "config.yaml") -> ConfigLoader:
    """Get global config instance (singleton pattern)"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigLoader(config_path)
    return _config_instance
