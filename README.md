# Stockbot - Automated SIP Trading System

A Python-based automated trading system for Systematic Investment Plans (SIP) using Zerodha Kite API.

## 🚀 Features

- **Automated SIP Orders**: Place regular and AMO orders automatically
- **Dry Run Mode**: Test and analyze without placing real orders
- **Market Hours Logic**: Handles regular market hours (9:15 AM - 3:30 PM) and AMO hours (5:30 AM - 9:00 AM)
- **Database Logging**: Track all orders and their status
- **Comprehensive Logging**: File and console logging with detailed information
- **Modular Architecture**: Clean separation of concerns, reusable for Django/FastAPI

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
Edit `sip_trader/sip_config.json` with your desired symbols and quantities:
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

### Running the SIP Automation

#### From Project Root Directory:
```bash
python -m sip_trader
```

#### Important Notes:
- **Always run from the project root directory** (`stockbot/`)
- **Use the `-m` flag** to ensure proper module imports
- **Check market hours** before running for real orders

### Market Hours

| Order Type | Time Window | Description |
|------------|-------------|-------------|
| **Regular Orders** | 9:15 AM - 3:30 PM | Immediate execution at market price |
| **AMO Orders** | 5:30 AM - 9:00 AM | After Market Orders, execute at next day's opening |
| **Outside Hours** | Other times | Orders are logged but not placed |

## ⚙️ Configuration

### Dry Run vs Real Trading Mode

Edit `sip_trader/config.py` to switch between modes:

```python
# DRY RUN MODE
# Set to True for testing/analysis (no real orders placed)
# Set to False for real trading
DRY_RUN = True
```

#### To Enable Real Trading:
1. Open `sip_trader/config.py`
2. Change `DRY_RUN = False`
3. Ensure you're running during market hours
4. Run the script: `python -m sip_trader`

#### To Enable Dry Run (Testing):
1. Open `sip_trader/config.py`
2. Change `DRY_RUN = True`
3. Run the script anytime: `python -m sip_trader`

### Logging Configuration

In `logger.py` and `sip_trader/config.py`, you can customize logging:

```python
# LOGGING
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_TO_FILE = True
LOG_TO_CONSOLE = True
```

## 📊 Output and Logging

### Console Output
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

### Log Files
- Location: `logs/sip_YYYYMMDD.log`
- Contains detailed execution logs
- Useful for analysis and debugging

### Database Logs
- Table: `sip_orders`
- Fields: `id`, `timestamp`, `symbol`, `amount`, `quantity`, `order_type`, `platform`, `status`
- Track all order attempts and results

## 🔧 Troubleshooting

### Common Issues

#### 1. Module Import Error
```
ModuleNotFoundError: No module named 'postgres'
```
**Solution:** Always run from project root with `python -m sip_trader`

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

### Database Setup
If you need to manually create the database table:
```sql
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
```

## 📁 Project Structure

```
stockbot/
├── sip_trader/
│   ├── sip_engine.py         # Main SIP engine class
│   ├── __main__.py           # Entry point for running the bot (python -m sip_trader)
│   ├── config.py             # Configuration settings
│   └── sip_config.json       # SIP symbols and quantities
├── postgres/
│   └── __init__.py           # PostgreSQL DB connection and table setup
├── logger.py                 # Reusable logger utility
├── logs/                     # Log files (auto-created)
├── .env                      # Environment variables
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## 🔒 Security Notes

- **Never commit** your `.env` file to version control
- **Keep API keys secure** and rotate them regularly
- **Use dry run mode** for testing
- **Start with small quantities** when switching to real trading

## 🚀 Next Steps

- Set up automated scheduling (Windows Task Scheduler / cron)
- Add email/Telegram notifications
- Build FastAPI backend for web interface
- Implement ML-based stock screening
- Add portfolio analytics and reporting

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs in `logs/` directory
3. Ensure all prerequisites are met
4. Verify configuration files are correct

---

**⚠️ Disclaimer:** This is for educational purposes. Always test thoroughly before using with real money. Trading involves risk.