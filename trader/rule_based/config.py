# Configuration for rule-based trading

RULE_BASED_CONFIG = {
    "SYMBOLS": [
        # Large Cap Stocks (Nifty 50)
        "RELIANCE.NS",      # Reliance Industries
        "TCS.NS",           # Tata Consultancy Services
        "HDFCBANK.NS",      # HDFC Bank
        "INFY.NS",          # Infosys
        "ICICIBANK.NS",     # ICICI Bank
        "HINDUNILVR.NS",    # Hindustan Unilever
        "ITC.NS",           # ITC Limited
        "SBIN.NS",          # State Bank of India
        "BHARTIARTL.NS",    # Bharti Airtel
        "AXISBANK.NS",      # Axis Bank
        "KOTAKBANK.NS",     # Kotak Mahindra Bank
        "ASIANPAINT.NS",    # Asian Paints
        "MARUTI.NS",        # Maruti Suzuki
        "HCLTECH.NS",       # HCL Technologies
        "SUNPHARMA.NS",     # Sun Pharmaceutical
        "TATACONSUM.NS",    # Tata Consumer Products
        "WIPRO.NS",         # Wipro
        "ULTRACEMCO.NS",    # UltraTech Cement
        "TECHM.NS",         # Tech Mahindra
        "POWERGRID.NS",     # Power Grid Corporation
        "NESTLEIND.NS",     # Nestle India
        "TITAN.NS",         # Titan Company
        "BAJFINANCE.NS",    # Bajaj Finance
        "ADANIENT.NS",      # Adani Enterprises
        "JSWSTEEL.NS",      # JSW Steel
        "ONGC.NS",          # Oil & Natural Gas Corporation
        "COALINDIA.NS",     # Coal India
        "NTPC.NS",          # NTPC
        "HINDALCO.NS",      # Hindalco Industries
        "TATAMOTORS.NS",    # Tata Motors
        "BRITANNIA.NS",     # Britannia Industries
        "CIPLA.NS",         # Cipla
        "DRREDDY.NS",       # Dr Reddy's Laboratories
        "EICHERMOT.NS",     # Eicher Motors
        "HEROMOTOCO.NS",    # Hero MotoCorp
        "DIVISLAB.NS",      # Divis Laboratories
        "SHREECEM.NS",      # Shree Cement
        "BAJAJFINSV.NS",    # Bajaj Finserv
        "GRASIM.NS",        # Grasim Industries
        "TATASTEEL.NS",     # Tata Steel
        "ADANIPORTS.NS",    # Adani Ports & SEZ
        "INDUSINDBK.NS",    # IndusInd Bank
        "APOLLOHOSP.NS",    # Apollo Hospitals
        "BAJAJ-AUTO.NS",    # Bajaj Auto
        "HCLTECH.NS",       # HCL Technologies
        "SBILIFE.NS",       # SBI Life Insurance
        "HDFCLIFE.NS",      # HDFC Life Insurance
        "ICICIPRULI.NS",    # ICICI Prudential Life Insurance
        
        # Mid Cap Stocks (Nifty Midcap 100)
        "VEDL.NS",          # Vedanta
        "PIDILITIND.NS",    # Pidilite Industries
        "DABUR.NS",         # Dabur India
        "COLPAL.NS",        # Colgate Palmolive
        "BERGEPAINT.NS",    # Berger Paints
        "MARICO.NS",        # Marico
        "GODREJCP.NS",      # Godrej Consumer Products
        "UBL.NS",           # United Breweries
        "UNITDSPR.NS",         # United Spirits
        "HAVELLS.NS",       # Havells India
        "CROMPTON.NS",      # Crompton Greaves Consumer
        "VOLTAS.NS",        # Voltas
        "BLUEDART.NS",      # Blue Dart Express
        "DEEPAKNTR.NS",     # Deepak Nitrite
        "ALKEM.NS",         # Alkem Laboratories
        "TORNTPHARM.NS",    # Torrent Pharmaceuticals
        "BIOCON.NS",        # Biocon
        "LUPIN.NS",         # Lupin
        "ZYDUSLIFE.NS",     # Cadila Healthcare
        "AUROPHARMA.NS",    # Aurobindo Pharma
        "MUTHOOTFIN.NS",    # Muthoot Finance
        "CHOLAFIN.NS",      # Cholamandalam Investment
        "BAJAJHLDNG.NS",    # Bajaj Holdings
        "GODREJIND.NS",     # Godrej Industries
        "TATACHEM.NS",      # Tata Chemicals
        "UPL.NS",           # UPL
        "COROMANDEL.NS",    # Coromandel International
        "PIIND.NS",         # PI Industries
        "DEEPAKFERT.NS",    # Deepak Fertilisers
        "GMMPFAUDLR.NS",    # GMM Pfaudler
        "KAJARIACER.NS",    # Kajaria Ceramics
        "ASIANTILES.NS",    # Asian Granito
        "SOMANYCERA.NS",    # Somany Ceramics
        "PRESTIGE.NS",      # Prestige Estates
        "GODREJPROP.NS",    # Godrej Properties
        "DLF.NS",           # DLF
        "SUNTV.NS",         # Sun TV Network
        "ZEEL.NS",          # Zee Entertainment
        "PEL.NS",           # Piramal Enterprises
        "TORNTPOWER.NS",    # Torrent Power
        "TATAPOWER.NS",     # Tata Power
        "ADANIGREEN.NS",    # Adani Green Energy
        "TATACOMM.NS",      # Tata Communications
        "BHARATFORG.NS",    # Bharat Forge
        "ESCORTS.NS",       # Escorts
        "ASHOKLEY.NS",      # Ashok Leyland
        "M&M.NS",           # Mahindra & Mahindra
        "TVSMOTOR.NS",      # TVS Motor Company
        "HEROMOTOCO.NS",    # Hero MotoCorp
        "EICHERMOT.NS",     # Eicher Motors
        "MARUTI.NS",        # Maruti Suzuki
        "TATAMOTORS.NS",    # Tata Motors
        
        # Small Cap Stocks (Popular Small Caps)
        "IRCTC.NS",         # IRCTC
        "RAJESHEXPO.NS",    # Rajesh Exports
        "METROPOLIS.NS",    # Metropolis Healthcare
        "APLAPOLLO.NS",     # APL Apollo Tubes
        "KPRMILL.NS",       # KPR Mill
        "TRIDENT.NS",       # Trident
        "VARDHACRLC.NS",    # Vardhman Textiles
        "KANSAINER.NS",     # Kansai Nerolac
        "AKZOINDIA.NS",     # Akzo Nobel India
        "ASIANPAINT.NS",    # Asian Paints
        "BERGEPAINT.NS",    # Berger Paints
        "INDIGO.NS",        # InterGlobe Aviation
        "SPICEJET.NS",      # SpiceJet
        "JETAIRWAYS.NS",    # Jet Airways
        "TATAAIA.NS",       # Tata AIA Life Insurance
        "HDFCAMC.NS",       # HDFC Asset Management
        "UTIAMC.NS",        # UTI Asset Management
        
        # ETFs (Exchange Traded Funds)
        "NIFTYBEES.NS",     # Nifty 50 ETF
        "SETFNIF50.NS",     # SBI Nifty 50 ETF
        "HDFCNIFTY.NS",     # HDFC Nifty 50 ETF
        "NIFTYIETF.NS",    # ICICI Nifty 50 ETF
        "SETFNIFBK.NS",     # SBI Nifty Bank ETF
        "HDFCBANKETF.NS",   # HDFC Bank ETF
        "ICICIBANKETF.NS",  # ICICI Bank ETF
        "SETFGOLD.NS",      # SBI Gold ETF
        "HDFCGOLD.NS",      # HDFC Gold ETF
        "ICICIGOLD.NS",     # ICICI Gold ETF
        "HDFCSENSEX.NS",    # HDFC Sensex ETF
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
        "USE_EMA": True,  # Enable/disable EMA strategy
        "EMA_SHORT_WINDOW": 12,  # Short-term EMA period
        "EMA_LONG_WINDOW": 26,   # Long-term EMA period
        
        # RSI Strategy
        "USE_RSI": True,  # Enable/disable RSI strategy
        "RSI_PERIOD": 14,  # RSI calculation period
        "RSI_OVERSOLD": 30,  # Oversold threshold for buy signals
        "RSI_OVERBOUGHT": 70,  # Overbought threshold for sell signals
        
        # MACD Strategy
        "USE_MACD": True,  # Enable/disable MACD strategy
        "MACD_FAST_PERIOD": 12,  # Fast EMA period
        "MACD_SLOW_PERIOD": 26,  # Slow EMA period
        "MACD_SIGNAL_PERIOD": 9,  # Signal line period
        
        # Strategy Combinations Examples:
        # Conservative: USE_SMA=True, USE_EMA=False, USE_RSI=False, USE_MACD=False
        # Balanced: USE_SMA=True, USE_EMA=True, USE_RSI=False, USE_MACD=False
        # Aggressive: USE_SMA=True, USE_EMA=True, USE_RSI=True, USE_MACD=True
    },
    
    # Logging
    "LOG_LEVEL": "INFO",  # DEBUG, INFO, WARNING, ERROR
    "LOG_TO_FILE": True,
    "LOG_TO_CONSOLE": True,
    
    # Automation/Scheduling (for future use)
    "RUN_FREQUENCY": "daily",  # Options: 'daily', 'intraday', 'weekly', etc.
    "RUN_TIME": "16:00",       # Time of day to run (24h format, e.g., '16:00' for 4 PM)
} 