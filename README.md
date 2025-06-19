# Stockbot - Automated SIP Trading System

A Python-based automated trading system for Systematic Investment Plans (SIP) using Zerodha Kite API.

## 🚀 Features

- **Automated SIP Orders**: Place regular and AMO orders automatically
- **Dry Run Mode**: Test and analyze without placing real orders
- **Market Hours Logic**: Handles regular market hours (9:15 AM - 3:30 PM) and AMO hours (5:30 AM - 9:00 AM)
- **Database Logging**: Track all orders and their status
- **Comprehensive Logging**: File and console logging with detailed information
- **Modular Architecture**: Clean separation of concerns

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
Edit `sip_config.json` with your desired symbols and quantities:
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
python -m scripts.auto_sip
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

Edit `config.py` to switch between modes:

```python
# DRY RUN MODE
# Set to True for testing/analysis (no real orders placed)
# Set to False for real trading
DRY_RUN = True
```

#### To Enable Real Trading:
1. Open `config.py`
2. Change `DRY_RUN = False`
3. Ensure you're running during market hours
4. Run the script: `python -m scripts.auto_sip`

#### To Enable Dry Run (Testing):
1. Open `config.py`
2. Change `DRY_RUN = True`
3. Run the script anytime: `python -m scripts.auto_sip`

### Logging Configuration

In `config.py`, you can customize logging:

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