# Configuration for rule-based trading

RULE_BASED_CONFIG = {
    # Engine Configuration
    "ENGINE_TYPE": "multi_source",  # Options: "classic", "multi_source", "ml_enhanced" (future)
    "ENGINE_CONFIG": {
        # Classic Engine Settings
        "USE_ENHANCED_FETCHER": True,  # Use enhanced fetcher in classic engine
        "FALLBACK_TO_ORIGINAL": True,  # Fallback to original methods if enhanced fails
        
        # Multi-Source Engine Settings
        "ENABLE_DB_CACHE": True,  # Use database caching for faster access
        "DATA_FRESHNESS_DAYS": 1,  # Consider data fresh for N days
        "FORCE_API_FETCH": False,  # Force fetch from API even if DB has data
        
        # Data Sources Priority (for multi-source engine)
        "DATA_SOURCES": ["yfinance", "alpha_vantage", "polygon"],  # Order of preference
        "ENABLE_CONSENSUS": True,  # Generate consensus signals across sources
        
        # ML Integration Settings (for future use)
        "ML_ENABLED": False,  # Enable ML-enhanced signals
        "ML_MODEL_PATH": None,  # Path to trained ML model
        "ML_CONFIDENCE_THRESHOLD": 0.7,  # Minimum confidence for ML signals
        "ML_FEATURE_SOURCES": ["technical", "sentiment", "fundamental"],  # Feature sources
    },
    "DATA_SOURCE": "yfinance",  # Options: 'yfinance', 'kite'
    "DB_DUMP": True,  # If True, dump fetched data to DB and reuse if available
    "DATA_PERIOD": "6mo",  # Period for historical data (e.g., '6mo', '1y')
    
    # Strategy Configuration
    "STRATEGIES": [
        {
            "name": "SimpleMovingAverageStrategy",
            "params": {
                "short_window": 20,
                "long_window": 50
            }
        },
        {
            "name": "ExponentialMovingAverageStrategy", 
            "params": {
                "short_window": 12,
                "long_window": 26
            }
        },
        {
            "name": "RSIStrategy",
            "params": {
                "period": 14,
                "oversold": 30,
                "overbought": 70
            }
        },
        {
            "name": "MACDStrategy",
            "params": {
                "fast_period": 12,
                "slow_period": 26,
                "signal_period": 9
            }
        }
    ],
    
    # Logging
    "LOG_LEVEL": "INFO",  # DEBUG, INFO, WARNING, ERROR
    "LOG_TO_FILE": True,
    "LOG_TO_CONSOLE": True,
    
    # Automation/Scheduling (for future use)
    "RUN_FREQUENCY": "daily",  # Options: 'daily', 'intraday', 'weekly', etc.
    "RUN_TIME": "16:00",       # Time of day to run (24h format, e.g., '16:00' for 4 PM)
    
    # Retry Settings
    "MAX_RETRIES": 2,
    "RETRY_DELAY": 1,  # Base delay in seconds (exponential backoff)
    
    "SYMBOLS": [
        # 🏆 MEGA CAP TECH (The Magnificent 7 + More)
        "AAPL",     # Apple Inc.
        "MSFT",     # Microsoft Corporation
        "GOOGL",    # Alphabet Inc. (Google)
        "META",     # Meta Platforms (Facebook)
        "TSLA",     # Tesla Inc.
        "ADBE",     # Adobe Inc.
        "UBER",     # Uber Technologies Inc.
        "NTAP",     # NetApp Inc.
        "SPOT",     # Spotify Technology S.A.
        "PLTR",     # Palantir Technologies Inc.
        
        # 🇮🇳 INDIAN MARKET LEADERS (NSE)
                
        # 📊 MAJOR INDIAN ETFs & INDICES
        "NIFTYBEES.NS",    # NIFTY BEES ETF
        "SETFNIF50.NS",    # SBI ETF NIFTY 50
        "HDFCNIFTY.NS",    # HDFC NIFTY 50 ETF
        # "ICICINIFTY.NS",   # ICICI Prudential NIFTY 50 ETF
        
        # 🏦 BANKING & FINANCIAL SERVICES
        "ICICIBANK.NS",    # ICICI Bank Ltd
        "SBIN.NS",         # State Bank of India
        "AXISBANK.NS",     # Axis Bank Ltd
        "KOTAKBANK.NS",    # Kotak Mahindra Bank Ltd
        
        "BAJFINANCE.NS",   # Bajaj Finance Ltd
        "BAJAJFINSV.NS",   # Bajaj Finserv Ltd
        "SUNPHARMA.NS",    # Sun Pharmaceutical Industries Ltd
        "ONGC.NS",         # Oil & Natural Gas Corporation Ltd
        "ADANIENT.NS",     # Adani Enterprises Ltd
        "ADANIPORTS.NS",   # Adani Ports & Special Economic Zone Ltd
        "ADANIPOWER.NS",   # Adani Power Ltd
        "ADANIGREEN.NS",   # Adani Green Energy Ltd
        "M&M.NS",          # Mahindra & Mahindra Ltd
        "BAJAJ-AUTO.NS",   # Bajaj Auto Ltd
        "PERSISTENT.NS",   # Persistent Systems Ltd
        "HINDUNILVR.NS",   # Hindustan Unilever Ltd
        "NESTLEIND.NS",    # Nestle India Ltd
        "TCS.NS",          # Tata Consultancy Services Ltd
        "TECHM.NS",        # Tech Mahindra Ltd
        "PERSISTENT.NS",   # Persistent Systems Ltd
        "BHARTIARTL.NS",   # Bharti Airtel Ltd
        "IDEA.NS",         # Vodafone Idea Ltd
        "TATAPOWER.NS",    # Tata Power Company Ltd
        "KAJARIACER.NS",   # Kajaria Ceramics Ltd
        "SAIL.NS",         # Steel Authority of India Ltd
    ],
}