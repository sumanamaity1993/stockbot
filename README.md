# StockBot - Advanced Trading Bot with Configurable Engines

A comprehensive stock trading bot featuring configurable rule-based engines, multi-source data fetching, news sentiment analysis, SIP automation, and advanced data quality analysis.

## 🚀 Key Features

### 🔧 Configurable Trading Engines
- **Classic Engine**: Single-source with intelligent fallback
- **Multi-Source Engine**: All-source analysis with consensus signals
- **Future-Ready**: Extensible architecture for ML engines
- **Command-Line Control**: Easy engine switching and configuration

### 📊 Enhanced Data Fetching System
- **Multi-Source Integration**: yfinance, Alpha Vantage, Polygon.io, Fyers API
- **Intelligent Fallback**: Automatic source switching on failures
- **Database Caching**: Individual source tables for clean data separation
- **Data Quality Assurance**: Comprehensive validation and cleaning
- **Real-Time Data**: Live price fetching and market status
- **Performance Optimization**: Intelligent caching and retry logic

### 🧩 Unified Source Manager (NEW)
- **Centralized Access**: All engines use a single Source Manager for data
- **Unified API**: Consistent interface for all data operations
- **Easy Extensibility**: Add new sources in one place
- **Cleaner Engines**: Engines focus on strategy, not data plumbing

### 📰 News & Sentiment Analysis
- **Multi-Source News**: GNews API, NewsAPI, Reddit sentiment
- **Sentiment Scoring**: VADER, FinBERT, and custom models
- **Real-Time Monitoring**: Live news tracking for trading signals
- **Database Storage**: Structured news articles and sentiment scores
- **Trading Integration**: News sentiment as additional signal factor

### 📈 Rule-Based Trading Strategies
- **Simple Moving Average (SMA)**: Golden/Death cross detection
- **Exponential Moving Average (EMA)**: Trend following
- **RSI Strategy**: Overbought/Oversold signals
- **MACD Strategy**: Momentum and trend analysis
- **Multi-Strategy Portfolio**: Combined signal analysis
- **Visual Signal Indicators**: Colored dots for easy signal identification

### 💰 SIP (Systematic Investment Plan) Automation
- **Automated Orders**: Scheduled investment execution
- **Multiple Platforms**: Kite Connect integration
- **Risk Management**: Order validation and monitoring
- **Portfolio Tracking**: Comprehensive order history

### 🔍 Data Quality & Analysis
- **Quality Scoring**: Comprehensive data assessment
- **Anomaly Detection**: Statistical outlier identification
- **Performance Metrics**: Detailed analysis reports
- **Recommendations**: Actionable improvement suggestions

### 🔐 Security & Configuration
- **Environment Variables**: All sensitive credentials managed via .env
- **Unified Configuration**: Centralized SOURCE_DATA_FETCHER_CONFIG for all data sources
- **Secure API Management**: No hardcoded credentials in codebase
- **Modular Architecture**: Clean separation of concerns

## 🧠 Smart Features & Optimizations

### 🚀 Performance Optimizations
- **Incremental Data Fetching**: Only fetches missing data periods
- **Adaptive Rate Limiting**: Dynamically adjusts API delays based on success rates
- **Predictive Prefetching**: Anticipates data needs and prefetches for optimal performance
- **Data Compression**: 20-40% size reduction for improved memory efficiency
- **Outlier Detection & Removal**: IQR-based statistical cleaning for better signal quality
- **Smart Concurrency Management**: Source-specific concurrency limits with adaptive adjustments

### 🎯 Intelligent Data Processing
- **Quality-Based Source Selection**: Prioritizes high-quality data sources
- **Batch Processing**: Efficient handling of multiple symbols
- **Parallel Fetching**: Concurrent data retrieval from multiple sources
- **Smart Caching**: Intelligent cache management with memory optimization
- **Data Compression**: Reduces memory usage while maintaining data integrity
- **Predictive Analytics**: Forecasts data needs for proactive fetching

### ⚡ Adaptive Performance
- **Source-Specific Concurrency**: Optimal concurrency per data source
- **Adaptive Rate Limiting**: Self-adjusting delays based on API performance
- **Success Rate Tracking**: Monitors and adapts to API reliability
- **Performance Analytics**: Real-time monitoring of system performance
- **Cache Analytics**: Memory usage and cache efficiency tracking
- **Concurrency Optimization**: Dynamic adjustment based on system load

### 🔧 Advanced Features
- **Incremental Updates**: Only fetches new data since last update
- **Data Freshness Validation**: Ensures data is current and relevant
- **Error Recovery**: Graceful handling of API failures and rate limits
- **Memory Management**: Efficient memory usage with data compression
- **Scalability**: Designed to handle large numbers of symbols efficiently
- **Monitoring**: Comprehensive logging and performance tracking

## 📊 Quick Start

### 1. Installation
```bash
git clone <repository-url>
cd stockbot
pip install -r requirements.txt
```

### 2. Configuration
Create a `.env` file with your API keys:
```env
# Database
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

# Market Data APIs
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
POLYGON_API_KEY=your_polygon_api_key
FYERS_API_KEY=your_fyers_api_key
FYERS_API_SECRET=your_fyers_api_secret
FYERS_ACCESS_TOKEN=your_fyers_access_token

# News & Sentiment APIs
GNEWS_API_KEY=your_gnews_api_key
NEWSAPI_KEY=your_newsapi_key
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=your_reddit_user_agent

# Trading APIs (Optional)
API_KEY=your_kite_api_key
API_SECRET=your_kite_api_secret
```

### 3. Run Trading Engines

#### Classic Engine (Single Source with Fallback)
```bash
# Use default configuration
python -m trader.rule_based --engine classic --symbols AAPL MSFT

# Custom period and sources
python -m trader.rule_based --engine classic --symbols AAPL --period 3mo --sources yfinance alpha_vantage
```

#### Multi-Source Engine (All Sources Analysis)
```bash
# Analyze all sources for consensus signals
python -m trader.rule_based --engine multi_source --symbols AAPL MSFT GOOGL

# Custom configuration
python -m trader.rule_based --engine multi_source --symbols AAPL --period 6mo --force-fetch
```

### 4. Demo Scripts
```bash
# Enhanced data fetcher demo
python demos/demo_enhanced_fetcher.py

# Configurable engine demo
python demos/demo_configurable_engines.py

# Rule-based signals demo
python demos/demo_rule_based_signals.py
```

### 5. SIP Automation
```bash
python -m trader.sip
```

## 🏗️ Architecture Overview

### Unified Data Access with Source Manager

All engines now use a single, centralized **Source Manager** for all data operations. This means:
- No more direct use of `EnhancedDataFetcher` or `DataQualityAnalyzer` in engines
- All data fetching, quality analysis, and optimization is done via the Source Manager
- Consistent, maintainable, and extensible data access

**Example:**
```python
from trader.data import get_source_manager

source_manager = get_source_manager()
result = source_manager.fetch_ohlc('AAPL', interval='daily', period='6mo')
if result:
    df = result['data']
    print(f"Fetched {len(df)} rows from {result['source']}")

# Data quality analysis
quality = source_manager.analyze_data_quality(df, 'AAPL')
print(f"Quality score: {quality['quality_score']}")
```

### Engine Example Usage

**Rule-Based Engine:**
```python
from trader.rule_based.engine import RuleBasedEngine

config = {
    "SYMBOLS": ["AAPL", "MSFT"],
    "ENGINE_CONFIG": {"DATA_SOURCES": ["yfinance", "alpha_vantage"]},
    # ... other config
}
engine = RuleBasedEngine(config)
# All data operations use source_manager internally
```

**Multi-Source Engine:**
```python
from trader.rule_based.multi_source_engine import MultiSourceRuleBasedEngine

config = {
    "SYMBOLS": ["AAPL", "MSFT"],
    "ENGINE_CONFIG": {"DATA_SOURCES": ["yfinance", "alpha_vantage", "polygon"]},
    # ... other config
}
engine = MultiSourceRuleBasedEngine(config)
# All data operations use source_manager internally
```

**SIP Engine (with fallback):**
```python
from trader.sip.sip_engine import SIPEngine
sip_engine = SIPEngine()
# SIP engine uses source_manager as fallback for real-time prices
```

## 🛠️ Usage Examples

**Fetching Data (Unified):**
```python
from trader.data import get_source_manager
source_manager = get_source_manager()
result = source_manager.fetch_ohlc('AAPL', interval='daily', period='6mo')
```

**Data Quality:**
```python
quality = source_manager.analyze_data_quality(df, 'AAPL')
```

**Real-Time Price:**
```python
price_data = source_manager.get_real_time_price('AAPL')
```

## 🔧 Configuration

### Data Fetcher Configuration (`trader/data/source_data/config.py`)
```python
SOURCE_DATA_FETCHER_CONFIG = {
    "DATA_SOURCES": ["yfinance", "alpha_vantage", "polygon", "fyers"],
    "CACHE_ENABLED": True,
    "FORCE_API_FETCH": False,
    "DB_DUMP": True,
    "CACHE_DURATION": 300,
    "MAX_RETRIES": 2,
    "RETRY_DELAY": 1,
    # ... additional settings
}
```

### News Data Configuration (`trader/data/news_data/config.py`)
```python
NEWS_DATA_CONFIG = {
    'GNEWS_API_KEY': os.getenv('GNEWS_API_KEY'),
    'NEWSAPI_KEY': os.getenv('NEWSAPI_KEY'),
    'REDDIT_CLIENT_ID': os.getenv('REDDIT_CLIENT_ID'),
    'REDDIT_CLIENT_SECRET': os.getenv('REDDIT_CLIENT_SECRET'),
    'REDDIT_USER_AGENT': os.getenv('REDDIT_USER_AGENT'),
    'ENABLED_SOURCES': ['gnews', 'newsapi', 'reddit'],
    'FETCH_INTERVAL_MINUTES': 30,
}
```

### Command-Line Options
```bash
# Engine selection
--engine classic|multi_source

# Symbols and periods
--symbols AAPL MSFT GOOGL
--period 1mo|3mo|6mo|1y

# Data sources
--sources yfinance alpha_vantage polygon fyers

# Database and caching
--db-cache|--no-db-cache
--force-fetch

# Output and logging
--verbose
--quiet
```

## 📊 Signal Display

### Visual Signal Indicators
The trading summary includes colored indicators for easy signal identification:

```
📈 AAPL: 🟢 BUY (MACDStrategy)
📈 MSFT: 🔴 SELL (MACDStrategy)
📈 GOOGL: 🔴 SELL (SimpleMovingAverageStrategy) | 🔴 SELL (ExponentialMovingAverageStrategy)

🎯 CONSENSUS SIGNALS SUMMARY:
   📈 AAPL: 🟢 BUY (confidence: 0.75, buy: 3, sell: 0)
   📈 MSFT: 🔴 SELL (confidence: 0.60, buy: 1, sell: 2)
```

**Signal Legend:**
- 🟢 **Green dot** = BUY signal
- 🔴 **Red dot** = SELL signal
- ⚪ **White dot** = HOLD/Other signal types
- 📈 **Chart icon** = Stock symbol

## 🔍 Testing

### Run All Tests
```bash
python -m pytest tests/test_engine_source_manager_integration.py -v
python -m pytest tests/test_source_manager.py -v
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the documentation
2. Review existing issues
3. Create a new issue with detailed information

---

**Built with ❤️ for algorithmic trading enthusiasts**