# Configuration for rule-based trading

RULE_BASED_CONFIG = {
    # Engine Configuration
    "ENGINE_TYPE": "classic",  # Options: "classic", "multi_source", "ml_enhanced" (future)
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
    
    "SYMBOLS": [
        # 🏆 MEGA CAP TECH (The Magnificent 7 + More)
        "AAPL",     # Apple Inc.
        "MSFT",     # Microsoft Corporation
        "GOOGL",    # Alphabet Inc. (Google)
        "AMZN",     # Amazon.com Inc.
        "NVDA",     # NVIDIA Corporation
        "META",     # Meta Platforms (Facebook)
        "TSLA",     # Tesla Inc.
        
        # 💰 FINANCIAL GIANTS
        "JPM",      # JPMorgan Chase & Co.
        "BAC",      # Bank of America Corp.
        "WFC",      # Wells Fargo & Company
        "GS",       # Goldman Sachs Group Inc.
        
        # 🏥 HEALTHCARE LEADERS
        "JNJ",      # Johnson & Johnson
        "PFE",      # Pfizer Inc.
        "UNH",      # UnitedHealth Group Inc.
        "ABBV",     # AbbVie Inc.
        
        # 🛢️ ENERGY & INDUSTRIALS
        "XOM",      # Exxon Mobil Corporation
        "CVX",      # Chevron Corporation
        "PG",       # Procter & Gamble Co.
        
        # 🛒 CONSUMER & RETAIL
        "WMT",      # Walmart Inc.
        "HD",       # Home Depot Inc.
        "DIS",      # Walt Disney Company
        "NFLX",     # Netflix Inc.
        
        # 📱 TRENDING TECH
        "AMD",      # Advanced Micro Devices
        "CRM",      # Salesforce Inc.
        "ADBE",     # Adobe Inc.
        "PYPL",     # PayPal Holdings Inc.
        "UBER",     # Uber Technologies Inc.
        "SPOT",     # Spotify Technology S.A.
        
        # 🚀 AI & SEMICONDUCTOR TRENDS
        "AI",       # C3.ai Inc.
        "PLTR",     # Palantir Technologies Inc.
        "PATH",     # UiPath Inc.
        "CRWD",     # CrowdStrike Holdings Inc.
        
        # 📊 MAJOR ETFs
        "SPY",      # SPDR S&P 500 ETF
        "QQQ",      # Invesco QQQ Trust (NASDAQ-100)
        "VTI",      # Vanguard Total Stock Market ETF
        "VOO",      # Vanguard S&P 500 ETF
        "IWM",      # iShares Russell 2000 ETF
        "GLD",      # SPDR Gold Shares
        "SLV",      # iShares Silver Trust
    ],
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
} 