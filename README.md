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

### Engine Types

#### Classic Engine (`engine.py`)
- **Purpose**: Single-source analysis with intelligent fallback
- **Data Flow**: Enhanced Fetcher → Priority-based source selection → Individual source table
- **Use Case**: Fast analysis with reliable data source
- **Database**: Stores in `ohlcv_[best_source]` table

#### Multi-Source Engine (`multi_source_engine.py`)
- **Purpose**: All-source analysis with consensus signals
- **Data Flow**: Individual Fetchers → All sources → Consensus analysis
- **Use Case**: Comprehensive analysis with signal comparison
- **Database**: Stores in individual `ohlcv_[source]` tables

### Database Structure
```
# Market Data Tables
ohlcv_yfinance          # yfinance data
ohlcv_alpha_vantage     # Alpha Vantage data
ohlcv_polygon          # Polygon.io data
ohlcv_fyers            # Fyers API data

# News & Sentiment Tables
news_articles           # News articles from all sources
sentiment_scores        # Sentiment analysis results
trading_signals         # Generated trading signals

# Trading Tables
sip_orders             # SIP order history
```

## 🛠️ Usage Examples

### Enhanced Data Fetcher
```python
from trader.data.source_data import EnhancedDataFetcher
from trader.data.source_data import SOURCE_DATA_FETCHER_CONFIG

# Initialize with unified configuration
fetcher = EnhancedDataFetcher(SOURCE_DATA_FETCHER_CONFIG)

# Fetch data with fallback
result = fetcher.fetch_ohlc('AAPL', period='6mo')
if result:
    df = result['data']
    source = result['source']
    print(f"Data from {source}: {len(df)} rows")

# Get real-time price
price_data = fetcher.get_real_time_price('AAPL')
```

### News Data Fetching
```python
from trader.data.news_data.gnews_fetcher import GNewsFetcher
from trader.data.news_data.config import NEWS_DATA_CONFIG

# Initialize news fetcher
gnews_fetcher = GNewsFetcher(NEWS_DATA_CONFIG)

# Fetch news articles
articles = gnews_fetcher.fetch_articles('AAPL', max_results=10)
for article in articles:
    print(f"Title: {article['title']}")
    print(f"Published: {article['published_at']}")
```

### Data Quality Analysis
```python
from trader.data.source_data import DataQualityAnalyzer

analyzer = DataQualityAnalyzer()
analysis = analyzer.analyze_data_quality(df, 'AAPL')

print(f"Quality Score: {analysis['quality_score']:.2f}")
print(f"Completeness: {analysis['completeness_score']:.2f}")
print(f"Consistency: {analysis['consistency_score']:.2f}")
print(f"Recommendations: {analysis['recommendations']}")
```

### Multi-Source Analysis
```python
from trader.rule_based.multi_source_engine import MultiSourceEngine

engine = MultiSourceEngine()
signals = engine.run_analysis(['AAPL', 'MSFT'])

# Access consensus signals
for symbol, consensus in signals['consensus_signals'].items():
    print(f"{symbol}: {consensus['action']} (confidence: {consensus['confidence']:.2f})")
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
python tests/test_all_fetchers.py
python tests/test_configurable_engine.py
python tests/test_multi_source_db.py
```

### Individual Component Tests
```bash
python tests/test_alpha_vantage.py
python tests/test_enhanced_fetcher.py
```

## 📈 Performance Metrics

### Data Quality
- **Completeness**: 95%+ data coverage
- **Consistency**: 90%+ OHLC validation
- **Anomaly Detection**: <5% false positives
- **Cache Performance**: 10x speed improvement

### Trading Performance
- **Signal Accuracy**: Configurable strategy parameters
- **Risk Management**: Built-in validation and checks
- **Portfolio Tracking**: Comprehensive order history
- **Multi-Source Consensus**: Improved signal reliability

## 🚀 Advanced Features

### Database Caching
- **Individual Source Tables**: Clean data separation
- **Freshness Checking**: Automatic data refresh
- **Performance Optimization**: Reduced API calls

### Error Handling
- **Retry Logic**: Exponential backoff
- **Fallback System**: Automatic source switching
- **Data Validation**: Comprehensive quality checks

### Extensibility
- **Plugin Architecture**: Easy strategy addition
- **Configurable Sources**: Dynamic data source management
- **Engine Framework**: Support for future ML engines

## 🔐 Security Features

### Environment Variable Management
- **No Hardcoded Credentials**: All API keys stored in .env file
- **Centralized Configuration**: Single source of truth for all settings
- **Secure Defaults**: Sensitive data never committed to repository

### API Key Management
- **Individual Source Configs**: Separate configs for different data types
- **Graceful Degradation**: System works with available APIs
- **Access Control**: Environment-based credential loading

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