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
        
        # 🇮🇳 INDIAN MARKET LEADERS (NSE)
                
        # 📊 MAJOR INDIAN ETFs & INDICES
        "NIFTYBEES.NS",    # NIFTY BEES ETF
        "SETFNIF50.NS",    # SBI ETF NIFTY 50
        "HDFCNIFTY.NS",    # HDFC NIFTY 50 ETF
        # "ICICINIFTY.NS",   # ICICI Prudential NIFTY 50 ETF
        
        # 🏭 RELIANCE GROUP & CONGLOMERATES
        "RELIANCE.NS",     # Reliance Industries Ltd
        "TATAMOTORS.NS",   # Tata Motors Ltd
        "TATASTEEL.NS",    # Tata Steel Ltd
        "TATACONSUM.NS",   # Tata Consumer Products Ltd
        "TATAPOWER.NS",    # Tata Power Company Ltd
        "TATACOMM.NS",     # Tata Communications Ltd
        
        # 🏦 BANKING & FINANCIAL SERVICES
        "HDFCBANK.NS",     # HDFC Bank Ltd
        "ICICIBANK.NS",    # ICICI Bank Ltd
        "SBIN.NS",         # State Bank of India
        "AXISBANK.NS",     # Axis Bank Ltd
        "KOTAKBANK.NS",    # Kotak Mahindra Bank Ltd
        # "HDFC.NS",         # HDFC Ltd
        "BAJFINANCE.NS",   # Bajaj Finance Ltd
        "BAJAJFINSV.NS",   # Bajaj Finserv Ltd
        "HDFCLIFE.NS",     # HDFC Life Insurance Company Ltd
        "ICICIPRULI.NS",   # ICICI Prudential Life Insurance Co Ltd
        "SBILIFE.NS",      # SBI Life Insurance Company Ltd
        
        # 🏥 PHARMACEUTICALS & HEALTHCARE
        "SUNPHARMA.NS",    # Sun Pharmaceutical Industries Ltd
        "DRREDDY.NS",      # Dr Reddy's Laboratories Ltd
        "CIPLA.NS",        # Cipla Ltd
        "DIVISLAB.NS",     # Divi's Laboratories Ltd
        "APOLLOHOSP.NS",   # Apollo Hospitals Enterprise Ltd
        "BIOCON.NS",       # Biocon Ltd
        "ALKEM.NS",        # Alkem Laboratories Ltd
        
        # 🛢️ OIL & GAS
        "ONGC.NS",         # Oil & Natural Gas Corporation Ltd
        "IOC.NS",          # Indian Oil Corporation Ltd
        "BPCL.NS",         # Bharat Petroleum Corporation Ltd
        # "HPCL.NS",         # Hindustan Petroleum Corporation Ltd
        "GAIL.NS",         # GAIL (India) Ltd
        
        # 🏗️ INFRASTRUCTURE & CONSTRUCTION
        "LT.NS",           # Larsen & Toubro Ltd
        "ADANIENT.NS",     # Adani Enterprises Ltd
        "ADANIPORTS.NS",   # Adani Ports & Special Economic Zone Ltd
        "ADANIPOWER.NS",   # Adani Power Ltd
        "ADANIGREEN.NS",   # Adani Green Energy Ltd
        # "ADANITRANS.NS",   # Adani Transmission Ltd
        "ULTRACEMCO.NS",   # UltraTech Cement Ltd
        "SHREECEM.NS",     # Shree Cement Ltd
        "ACC.NS",          # ACC Ltd
        "AMBUJACEM.NS",    # Ambuja Cements Ltd
        
        # 🚗 AUTOMOBILES & AUTO COMPONENTS
        "MARUTI.NS",       # Maruti Suzuki India Ltd
        "M&M.NS",          # Mahindra & Mahindra Ltd
        "BAJAJ-AUTO.NS",   # Bajaj Auto Ltd
        "HEROMOTOCO.NS",   # Hero MotoCorp Ltd
        "EICHERMOT.NS",    # Eicher Motors Ltd
        "ASHOKLEY.NS",     # Ashok Leyland Ltd
        # "MOTHERSUMI.NS",   # Motherson Sumi Systems Ltd
        "BHARATFORG.NS",   # Bharat Forge Ltd
        
        # 🏠 REAL ESTATE & CONSTRUCTION
        "DLF.NS",          # DLF Ltd
        "GODREJPROP.NS",   # Godrej Properties Ltd
        "SUNTV.NS",        # Sun TV Network Ltd
        "PERSISTENT.NS",   # Persistent Systems Ltd
        
        # 🛒 CONSUMER GOODS & RETAIL
        "ITC.NS",          # ITC Ltd
        "HINDUNILVR.NS",   # Hindustan Unilever Ltd
        "NESTLEIND.NS",    # Nestle India Ltd
        "BRITANNIA.NS",    # Britannia Industries Ltd
        "MARICO.NS",       # Marico Ltd
        "DABUR.NS",        # Dabur India Ltd
        "COLPAL.NS",       # Colgate-Palmolive (India) Ltd
        "GODREJCP.NS",     # Godrej Consumer Products Ltd
        "UBL.NS",          # United Breweries Ltd
        
        # 📱 TECHNOLOGY & IT SERVICES
        "TCS.NS",          # Tata Consultancy Services Ltd
        "INFY.NS",         # Infosys Ltd
        "WIPRO.NS",        # Wipro Ltd
        "HCLTECH.NS",      # HCL Technologies Ltd
        "TECHM.NS",        # Tech Mahindra Ltd
        # "MINDTREE.NS",     # Mindtree Ltd
        # "LTI.NS",          # Larsen & Toubro Infotech Ltd
        "MPHASIS.NS",      # Mphasis Ltd
        "COFORGE.NS",      # Coforge Ltd
        "PERSISTENT.NS",   # Persistent Systems Ltd
        
        # 📡 TELECOM & MEDIA
        "BHARTIARTL.NS",   # Bharti Airtel Ltd
        "IDEA.NS",         # Vodafone Idea Ltd
        "ZEEL.NS",         # Zee Entertainment Enterprises Ltd
        
        # ⚡ POWER & UTILITIES
        "NTPC.NS",         # NTPC Ltd
        "POWERGRID.NS",    # Power Grid Corporation of India Ltd
        "TATAPOWER.NS",    # Tata Power Company Ltd
        
        # 🏥 HOSPITALITY & TRAVEL
        "INDIGO.NS",       # InterGlobe Aviation Ltd (IndiGo)
        # "SPICEJET.NS",     # SpiceJet Ltd
        
        # 🚀 TRENDING & HIGH-GROWTH STOCKS
        "PAYTM.NS",        # One 97 Communications Ltd (Paytm)
        "NAUKRI.NS",       # Info Edge (India) Ltd (Naukri.com)
        "JUSTDIAL.NS",     # Just Dial Ltd
        "REDINGTON.NS",    # Redington India Ltd
        "VBL.NS",          # Varun Beverages Ltd
        "DIXON.NS",        # Dixon Technologies India Ltd
        "VOLTAS.NS",       # Voltas Ltd
        "HAVELLS.NS",      # Havells India Ltd
        "CROMPTON.NS",     # Crompton Greaves Consumer Electricals Ltd
        "KAJARIACER.NS",   # Kajaria Ceramics Ltd
        "ASIANPAINT.NS",   # Asian Paints Ltd
        "BERGEPAINT.NS",   # Berger Paints India Ltd
        "PIDILITIND.NS",   # Pidilite Industries Ltd
        "PEL.NS",          # Piramal Enterprises Ltd
        "TORNTPHARM.NS",   # Torrent Pharmaceuticals Ltd
        "ALKEM.NS",        # Alkem Laboratories Ltd
        "LUPIN.NS",        # Lupin Ltd
        # "CADILAHC.NS",     # Cadila Healthcare Ltd
        "TORNTPOWER.NS",   # Torrent Power Ltd
        "TATACOMM.NS",     # Tata Communications Ltd
        # "BHARATIARTL.NS",  # Bharti Airtel Ltd
        "JSWSTEEL.NS",     # JSW Steel Ltd
        "VEDL.NS",         # Vedanta Ltd
        "HINDALCO.NS",     # Hindalco Industries Ltd
        "COALINDIA.NS",    # Coal India Ltd
        "NMDC.NS",         # NMDC Ltd
        "SAIL.NS",         # Steel Authority of India Ltd
    ],
}