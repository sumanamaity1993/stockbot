# Stockbot - Modular Automated Trading Bot Framework

A Python-based automated trading system supporting:
- **Systematic Investment Plans (SIP)** automation for stocks, ETFs, and mutual funds
- **Rule-Based Trading** with multiple strategies (SMA, EMA, RSI, MACD crossovers)
- **(Planned) Machine Learning-Based Trading** for advanced signal generation

Built for flexibility, modularity, and easy extension to new strategies and data sources.

## 🚀 Features

- **Automated SIP Orders**: Place regular and AMO orders automatically
- **Multiple Trading Strategies**: SMA, EMA, RSI, MACD with configurable parameters
- **Multi-Strategy Support**: Run multiple strategies simultaneously on the same data
- **Smart Signal Summary**: Automatic summary of trading opportunities with buy/sell counts
- **Moving Average Crossover Strategy**: Golden Cross (buy) and Death Cross (sell) signals
- **Dry Run Mode**: Test and analyze without placing real orders
- **Market Hours Logic**: Handles regular market hours (9:15 AM - 3:30 PM) and AMO hours (5:30 AM - 9:00 AM)
- **Database Logging**: Track all orders and their status
- **Comprehensive Logging**: File and console logging with detailed information
- **Modular Architecture**: Clean separation of concerns, reusable for Django/FastAPI
- **Pluggable Data Sources**: Fetch data from yfinance, Kite, or your own APIs
- **Ready for ML Expansion**: Structure supports future machine learning modules

## 📋 Prerequisites

- Python 3.8+
- PostgreSQL database
- Zerodha Kite account with API access
- Windows/Linux/macOS

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd stockbot
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up PostgreSQL
- Install PostgreSQL from [postgresql.org](https://www.postgresql.org/download/)
- Create a database named `stockbot`
- Note down your database credentials
- **Validate your connection:**
  ```sh
  psql -U postgres -h localhost -W
  ```
  Enter your password when prompted. You should see the `psql` prompt if the connection is successful.

### 4. Configure Environment Variables
Create a `.env` file in the project root:
```env
# Database Configuration
DB_NAME=stockbot
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432

# Zerodha API Configuration
API_KEY=your_kite_api_key
API_SECRET=your_kite_api_secret
```

### 5. Configure SIP Settings
Edit `trader/sip/sip_config.json` with your desired symbols and quantities:
```json
[
  {
    "symbol": "PARAGPARIKH",
    "amount": 3000,
    "type": "mutual_fund",
    "platform": "coin"
  },
  {
    "symbol": "NIFTYBEES",
    "quantity": 2,
    "type": "etf",
    "platform": "kite"
  },
  {
    "symbol": "RELIANCE",
    "quantity": 1,
    "type": "stock",
    "platform": "kite"
  }
]
```

## 🎯 Usage

### Run SIP Trader

```bash
python -m trader.sip
```

### Run Rule-Based Trader

```bash
python -m trader.rule_based
```

- Processes all symbols listed in `trader/rule_based/config.py`
- Fetches data from yfinance by default, falls back to Kite API if yfinance fails
- Dumps/loads data to/from the database if enabled
- Runs multiple strategies simultaneously and prints buy/sell signals for each symbol
- **Automatically generates a summary** of all trading opportunities at the end

### Example Rule-Based Config (`trader/rule_based/config.py`):
```python
RULE_BASED_CONFIG = {
    "SYMBOLS": [
        # Large Cap Stocks (Nifty 50)
        "RELIANCE.NS",      # Reliance Industries
        "TCS.NS",           # Tata Consultancy Services
        "HDFCBANK.NS",      # HDFC Bank
        "INFY.NS",          # Infosys
        "ICICIBANK.NS",     # ICICI Bank
        # ... 150+ symbols including Large Cap, Mid Cap, Small Cap, and ETFs
    ],
    "DATA_SOURCE": "yfinance",  # Options: 'yfinance', 'kite'
    "DB_DUMP": True,  # If True, dump fetched data to DB and reuse if available
    "DATA_PERIOD": "6mo",  # Period for historical data (e.g., '6mo', '1y')
    
    # Strategy Configuration
    "STRATEGY_CONFIG": {
        # Simple Moving Average Strategy (Default)
        "USE_SMA": True,  # Enable/disable SMA strategy
        "SMA_SHORT_WINDOW": 20,  # Short-term SMA period
        "SMA_LONG_WINDOW": 50,   # Long-term SMA period
        
        # Exponential Moving Average Strategy
        "USE_EMA": False,  # Enable/disable EMA strategy
        "EMA_SHORT_WINDOW": 12,  # Short-term EMA period
        "EMA_LONG_WINDOW": 26,   # Long-term EMA period
        
        # RSI Strategy
        "USE_RSI": False,  # Enable/disable RSI strategy
        "RSI_PERIOD": 14,  # RSI calculation period
        "RSI_OVERSOLD": 30,  # Oversold threshold for buy signals
        "RSI_OVERBOUGHT": 70,  # Overbought threshold for sell signals
        
        # MACD Strategy
        "USE_MACD": False,  # Enable/disable MACD strategy
        "MACD_FAST_PERIOD": 12,  # Fast EMA period
        "MACD_SLOW_PERIOD": 26,  # Slow EMA period
        "MACD_SIGNAL_PERIOD": 9,  # Signal line period
    },
    
    # Logging
    "LOG_LEVEL": "INFO",  # DEBUG, INFO, WARNING, ERROR
    "LOG_TO_FILE": True,
    "LOG_TO_CONSOLE": True,
}
```

## 📊 Trading Strategies

### **1. Simple Moving Average (SMA) Strategy**
- **Golden Cross (Buy):** Short SMA crosses above Long SMA
- **Death Cross (Sell):** Short SMA crosses below Long SMA
- **Default:** 20-day vs 50-day SMA
- **Best for:** Trend following, medium-term signals

### **2. Exponential Moving Average (EMA) Strategy**
- **Golden Cross (Buy):** Short EMA crosses above Long EMA
- **Death Cross (Sell):** Short EMA crosses below Long EMA
- **Default:** 12-day vs 26-day EMA
- **Best for:** More responsive to recent price changes

### **3. Relative Strength Index (RSI) Strategy**
- **Buy Signal:** RSI crosses above oversold threshold (30)
- **Sell Signal:** RSI crosses below overbought threshold (70)
- **Default:** 14-day RSI
- **Best for:** Identifying overbought/oversold conditions

### **4. Moving Average Convergence Divergence (MACD) Strategy**
- **Buy Signal:** MACD line crosses above Signal line
- **Sell Signal:** MACD line crosses below Signal line
- **Default:** 12/26/9 periods
- **Best for:** Momentum and trend confirmation

### **Strategy Combinations:**

#### **Conservative (Low Risk):**
```python
"USE_SMA": True, "USE_EMA": False, "USE_RSI": False, "USE_MACD": False
```

#### **Balanced (Medium Risk):**
```python
"USE_SMA": True, "USE_EMA": True, "USE_RSI": False, "USE_MACD": False
```

#### **Aggressive (High Risk):**
```python
"USE_SMA": True, "USE_EMA": True, "USE_RSI": True, "USE_MACD": True
```

### Important Notes:
- **Always run from the project root directory** (`stockbot/`)
- **Use the `-m` flag** to ensure proper module imports
- **Check market hours** before running for real orders
- **Rule-based trader only generates signals** - no automatic order placement
- **Multiple strategies can generate conflicting signals** - use for analysis, not automated trading
- **Summary automatically shows only symbols with signals** - no need to scroll through empty results

### Market Hours

| Order Type | Time Window | Description |
|------------|-------------|-------------|
| **Regular Orders** | 9:15 AM - 3:30 PM | Immediate execution at market price |
| **AMO Orders** | 5:30 AM - 9:00 AM | After Market Orders, execute at next day's opening |
| **Outside Hours** | Other times | Orders are logged but not placed |

## ⚙️ Configuration

### Dry Run vs Real Trading Mode

Edit `trader/sip/config.py` to switch between modes:

```python
# DRY RUN MODE
# Set to True for testing/analysis (no real orders placed)
# Set to False for real trading
DRY_RUN = True
```

#### To Enable Real Trading:
1. Open `trader/sip/config.py`
2. Change `DRY_RUN = False`
3. Ensure you're running during market hours
4. Run the script: `python -m trader.sip`

#### To Enable Dry Run (Testing):
1. Open `trader/sip/config.py`
2. Change `DRY_RUN = True`
3. Run the script anytime: `python -m trader.sip`

### Logging Configuration

In `logger.py` and config files, you can customize logging:

```python
# LOGGING
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_TO_FILE = True
LOG_TO_CONSOLE = True
```

## 📊 Output and Logging

### SIP Console Output
```
============================================================
📈 STOCKBOT SIP AUTOMATION STARTED
============================================================
✅ Using existing access token
🚀 Starting SIP automation for 3 symbols
🔧 Dry run mode: ENABLED
🔄 Attempting to place SIP order: PARAGPARIKH (mutual_fund)
💰 Mutual Fund SIP: PARAGPARIKH for ₹3000
🎯 DRY RUN: Would place REGULAR MF order for PARAGPARIKH for ₹3000
💾 Logged to database: PARAGPARIKH - ₹3000 - Qty: - - mutual_fund - coin - DRY_RUN: REGULAR MF order simulated
🏦 STOCK SIP: RELIANCE x 1 units
💹 LTP for RELIANCE: ₹2850 | Total Amount: ₹2850
🎯 DRY RUN: Would place REGULAR order for RELIANCE x 1 units
💾 Logged to database: RELIANCE - ₹2850 - Qty: 1 - stock - kite - DRY_RUN: REGULAR order simulated
🏁 SIP automation completed
============================================================
📈 STOCKBOT SIP AUTOMATION ENDED
============================================================
```

### Rule-Based Console Output (With Signals)
```
2025-06-20 02:14:47,143 - INFO - Running rule-based trading for symbols: ['RELIANCE.NS', 'TCS.NS', ...] using yfinance
2025-06-20 02:14:47,144 - INFO - Initialized with 1 strategies: ['SimpleMovingAverageStrategy']
2025-06-20 02:14:47,145 - INFO - Processing RELIANCE.NS
2025-06-20 02:14:47,868 - INFO - Loaded data from DB.
2025-06-20 02:14:47,943 - INFO - RELIANCE.NS Signals: [('buy', 'SimpleMovingAverageStrategy')]
2025-06-20 02:14:47,944 - INFO - Processing TCS.NS
2025-06-20 02:14:48,123 - INFO - Dumped data to DB.
2025-06-20 02:14:48,145 - INFO - TCS.NS Signals: []
2025-06-20 02:14:48,146 - INFO - Processing HDFCBANK.NS
2025-06-20 02:14:48,234 - INFO - HDFCBANK.NS Signals: [('sell', 'SimpleMovingAverageStrategy')]
...
================================================================================
📊 TRADING SIGNALS SUMMARY
================================================================================
🎯 Found 3 symbols with trading signals:
--------------------------------------------------------------------------------
📈 RELIANCE.NS: 🟢 BUY (SimpleMovingAverageStrategy)
📈 HDFCBANK.NS: 🔴 SELL (SimpleMovingAverageStrategy)
📈 INFY.NS: 🟢 BUY (SimpleMovingAverageStrategy)
--------------------------------------------------------------------------------
💡 Total trading opportunities: 3
🟢 Buy signals: 2
🔴 Sell signals: 1
--------------------------------------------------------------------------------
📊 Processing Summary:
   ✅ Successful: 150 symbols
   ❌ Failed: 5 symbols
   📈 Total analyzed: 155 symbols
================================================================================
```

### Rule-Based Console Output (No Signals)
```
2025-06-20 02:14:47,143 - INFO - Running rule-based trading for symbols: ['RELIANCE.NS', 'TCS.NS', ...] using yfinance
2025-06-20 02:14:47,144 - INFO - Initialized with 1 strategies: ['SimpleMovingAverageStrategy']
2025-06-20 02:14:47,145 - INFO - Processing RELIANCE.NS
2025-06-20 02:14:47,868 - INFO - Loaded data from DB.
2025-06-20 02:14:47,943 - INFO - RELIANCE.NS Signals: []
2025-06-20 02:14:47,944 - INFO - Processing TCS.NS
2025-06-20 02:14:48,123 - INFO - Dumped data to DB.
2025-06-20 02:14:48,145 - INFO - TCS.NS Signals: []
...
================================================================================
📊 TRADING SIGNALS SUMMARY
================================================================================
😴 No trading signals found in current market conditions
💡 Consider:
   • Using shorter moving average periods for more signals
   • Enabling additional strategies (EMA, RSI, MACD)
   • Checking different time periods
--------------------------------------------------------------------------------
📊 Processing Summary:
   ✅ Successful: 150 symbols
   ❌ Failed: 5 symbols
   📈 Total analyzed: 155 symbols
================================================================================
```

### Multi-Strategy Output Example
```
2025-06-20 02:14:47,144 - INFO - Initialized with 3 strategies: ['SimpleMovingAverageStrategy', 'RSIStrategy', 'MACDStrategy']
2025-06-20 02:14:47,145 - INFO - Processing RELIANCE.NS
2025-06-20 02:14:47,943 - INFO - RELIANCE.NS Signals: [('buy', 'RSIStrategy'), ('sell', 'MACDStrategy')]
...
================================================================================
📊 TRADING SIGNALS SUMMARY
================================================================================
🎯 Found 1 symbols with trading signals:
--------------------------------------------------------------------------------
📈 RELIANCE.NS: 🟢 BUY (RSIStrategy) | 🔴 SELL (MACDStrategy)
--------------------------------------------------------------------------------
💡 Total trading opportunities: 1
🟢 Buy signals: 1
🔴 Sell signals: 1
--------------------------------------------------------------------------------
📊 Processing Summary:
   ✅ Successful: 150 symbols
   ❌ Failed: 5 symbols
   📈 Total analyzed: 155 symbols
================================================================================
```

### Log Files
- **SIP Logs:** `logs/sip_YYYYMMDD.log`
- **Rule-Based Logs:** `logs/rule_based_YYYYMMDD.log`
- Contains detailed execution logs for analysis and debugging

### Database Logs
- **SIP Orders:** `sip_orders` table
- **OHLCV Data:** `ohlcv_data` table (for rule-based analysis)
- Track all order attempts, results, and historical price data

## 🔧 Troubleshooting

### Common Issues

#### 1. Module Import Error
```
ModuleNotFoundError: No module named 'postgres'
```
**Solution:** Always run from project root with `python -m trader.sip` or `python -m trader.rule_based`

#### 2. Database Connection Error
```
psycopg2.OperationalError: password authentication failed
```
**Solution:** Check your `.env` file and ensure PostgreSQL credentials are correct

#### 3. Market Hours Error
```
AMO orders cannot be placed till 5.30 AM due to scheduled maintenance
```
**Solution:** Run during proper market hours or AMO hours

#### 4. Authentication Error
```
Failed to generate session
```
**Solution:** Check your API credentials in `.env` file

#### 5. Symbol Not Found Error
```
YFPricesMissingError: possibly delisted; no price data found
```
**Solution:** Check if the symbol exists on Yahoo Finance, use `.NS` suffix for Indian stocks

#### 6. Strategy Import Error
```
ModuleNotFoundError: No module named 'trader.rule_based.strategies'
```
**Solution:** Ensure all strategy files are in the correct directory structure

#### 7. No Trading Signals
```
😴 No trading signals found in current market conditions
```
**Solutions:**
- Enable additional strategies in config
- Use shorter moving average periods
- Check different time periods
- Wait for market conditions to change

### Database Setup
If you need to manually create the database tables:
```sql
-- SIP Orders Table
CREATE TABLE IF NOT EXISTS sip_orders (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT NOW(),
    symbol VARCHAR(50),
    amount DECIMAL(10,2),
    quantity INTEGER,
    order_type VARCHAR(20),
    platform VARCHAR(20),
    status TEXT
);

-- OHLCV Data Table
CREATE TABLE IF NOT EXISTS ohlcv_data (
    symbol VARCHAR(50),
    date DATE,
    open DECIMAL(10,2),
    high DECIMAL(10,2),
    low DECIMAL(10,2),
    close DECIMAL(10,2),
    volume BIGINT,
    PRIMARY KEY (symbol, date)
);
```

## 📁 Project Structure

```
stockbot/
├── trader/
│   ├── sip/
│   │   ├── sip_engine.py         # Main SIP engine class
│   │   ├── __main__.py           # Entry point for running the bot (python -m trader.sip)
│   │   ├── config.py             # Configuration settings
│   │   └── sip_config.json       # SIP symbols and quantities
│   ├── rule_based/
│   │   ├── strategies/
│   │   │   ├── base.py               # Base strategy class
│   │   │   ├── simple_moving_average.py # SMA crossover strategy
│   │   │   ├── exponential_moving_average.py # EMA crossover strategy
│   │   │   ├── rsi_strategy.py        # RSI overbought/oversold strategy
│   │   │   └── macd_strategy.py       # MACD line crossover strategy
│   │   ├── indicators/
│   │   │   ├── ema.py                 # EMA calculation
│   │   │   ├── macd.py                # MACD calculation
│   │   │   └── rsi.py                 # RSI calculation
│   │   ├── engine.py             # Rule-based trading engine with summary
│   │   ├── __main__.py           # Entry point (python -m trader.rule_based)
│   │   └── config.py             # Rule-based configuration
│   ├── data/
│   │   ├── kite_fetcher.py       # Kite Connect data fetcher
│   │   └── yfinance_fetcher.py   # Yahoo Finance data fetcher
│   └── ml/                       # (Future) Machine learning models and logic
├── postgres/
│   └── __init__.py               # PostgreSQL DB connection and table setup
├── logger.py                     # Reusable logger utility
├── logs/                         # Log files (auto-created)
├── .env                          # Environment variables
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## 🔒 Security Notes

- **Never commit** your `.env` file to version control
- **Keep API keys secure** and rotate them regularly
- **Use dry run mode** for testing
- **Start with small quantities** when switching to real trading

## 🚀 Next Steps

- Set up automated scheduling (Windows Task Scheduler / cron)
- Add email/Telegram notifications for trading signals
- Build FastAPI backend for web interface
- Implement more advanced strategies (Bollinger Bands, Stochastic, etc.)
- Add portfolio tracking and performance analytics
- Create strategy backtesting and optimization tools
- Add risk management and position sizing
- Implement signal strength scoring and filtering