# Installation Guide

## Prerequisites

- Python 3.10 or higher
- pip package manager
- Git (for cloning repository)

## Step-by-Step Installation

### 1. Clone Repository

```bash
git clone https://github.com/rckn42/LoopyLoef.git
cd LoopyLoef
```

### 2. Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Verify Installation

```bash
python -c "import pandas, numpy, ccxt, yaml; print('All dependencies installed successfully!')"
```

## Configuration

### For Backtesting (No API Keys Required)

1. Review `config.yaml` and adjust parameters as needed
2. Ensure `mode: backtest` is set
3. You're ready to run!

### For Paper/Live Trading (API Keys Required)

1. Create a `.env` file in the project root:

```bash
touch .env
```

2. Add your Binance API credentials:

```
BINANCE_API_KEY=your_api_key_here
BINANCE_SECRET_KEY=your_secret_key_here
```

3. **Important**: Never commit `.env` file to version control!

### Getting Binance API Keys

1. Log in to Binance
2. Go to API Management
3. Create New Key
4. **For testing**: Use Binance Testnet
5. **For live**: Enable spot trading only, restrict IP if possible
6. Save API Key and Secret securely

## Directory Structure

The system will create these directories automatically:

- `logs/` - System logs, equity curves, trade logs
- `data/` - Downloaded historical data (CSV files)

## Troubleshooting

### Issue: Module not found

**Solution**: Ensure you're in the virtual environment and all dependencies are installed:
```bash
pip install -r requirements.txt
```

### Issue: Binance connection error

**Solution**: 
- Check your internet connection
- Verify API keys are correct
- Check if Binance API is accessible in your region
- For testing, use Binance Testnet

### Issue: Permission denied on logs/data directories

**Solution**: 
```bash
mkdir -p logs data
chmod 755 logs data
```

## Next Steps

After installation:

1. Review the [Configuration Guide](config.yaml)
2. Read the [Usage Examples](README.md#usage)
3. Run your first backtest
4. Analyze results in `logs/`

## Updating

To update to the latest version:

```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

## Uninstallation

To completely remove:

```bash
# Deactivate virtual environment
deactivate

# Remove project directory
cd ..
rm -rf LoopyLoef
```
