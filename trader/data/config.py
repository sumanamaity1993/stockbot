# Configuration for Enhanced Data Fetcher

ENHANCED_DATA_CONFIG = {
    # API Keys (set these in .env file)
    "ALPHA_VANTAGE_API_KEY": None,  # Get from https://www.alphavantage.co/
    "POLYGON_API_KEY": None,        # Get from https://polygon.io/
    
    # Data Source Priority (order matters - first is tried first)
    "DATA_SOURCES": [
        "yfinance",        # Free, reliable, good for most use cases
        "alpha_vantage",   # Free tier with API key, good for US stocks
        "polygon",         # Paid, high-quality, real-time data
    ],
    
    # Caching Settings
    "CACHE_ENABLED": True,
    "CACHE_DURATION": 300,  # 5 minutes in seconds
    
    # Retry Settings
    "MAX_RETRIES": 3,
    "RETRY_DELAY": 1,  # Base delay in seconds (exponential backoff)
    
    # Data Validation Settings
    "MIN_DATA_POINTS": 10,      # Minimum data points required (reduced for testing)
    "MAX_PRICE_CHANGE": 0.5,    # Maximum allowed price change (50%)
    
    # Default Data Settings
    "DEFAULT_INTERVAL": "1d",   # Default interval for data fetching
    "DEFAULT_PERIOD": "6mo",    # Default period for data fetching
    
    # Rate Limiting (to avoid API limits)
    "RATE_LIMIT_DELAY": 0.1,    # Delay between API calls in seconds
    "MAX_REQUESTS_PER_MINUTE": 60,  # Maximum requests per minute
    
    # Data Quality Settings
    "ENABLE_DATA_CLEANING": True,
    "REMOVE_OUTLIERS": True,
    "FILL_MISSING_DATA": True,
    
    # Logging Settings
    "LOG_LEVEL": "INFO",
    "LOG_TO_FILE": True,
    "LOG_TO_CONSOLE": True,
    
    # Performance Settings
    "ENABLE_PARALLEL_FETCHING": False,  # Fetch multiple symbols in parallel
    "MAX_CONCURRENT_REQUESTS": 5,       # Maximum concurrent API requests
    
    # Market Hours (for real-time data)
    "MARKET_HOURS": {
        "start": "09:30",
        "end": "16:00",
        "timezone": "US/Eastern"
    },
    
    # Data Source Specific Settings
    "YFINANCE_SETTINGS": {
        "progress": False,  # Disable progress bar
        "auto_adjust": True,  # Auto-adjust for splits/dividends
        "prepost": False,  # Include pre/post market data
    },
    
    "ALPHA_VANTAGE_SETTINGS": {
        "outputsize": "compact",  # 'compact' or 'full'
        "datatype": "json",       # 'json' or 'csv'
    },
    
    "POLYGON_SETTINGS": {
        "multiplier": 1,
        "timespan": "day",
    },
}

# Data source availability check
def check_data_source_availability(config):
    """
    Check which data sources are available based on API keys
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Dict: Available data sources and their status
    """
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    availability = {
        "yfinance": {
            "available": True,
            "requires_key": False,
            "status": "Available"
        },
        "alpha_vantage": {
            "available": bool(os.getenv('ALPHA_VANTAGE_API_KEY') or config.get('ALPHA_VANTAGE_API_KEY')),
            "requires_key": True,
            "status": "Available" if bool(os.getenv('ALPHA_VANTAGE_API_KEY') or config.get('ALPHA_VANTAGE_API_KEY')) else "API key required"
        },
        "polygon": {
            "available": bool(os.getenv('POLYGON_API_KEY') or config.get('POLYGON_API_KEY')),
            "requires_key": True,
            "status": "Available" if bool(os.getenv('POLYGON_API_KEY') or config.get('POLYGON_API_KEY')) else "API key required"
        }
    }
    
    return availability

# Get available data sources
def get_available_sources(config):
    """
    Get list of available data sources
    
    Args:
        config: Configuration dictionary
        
    Returns:
        List: Available data source names
    """
    availability = check_data_source_availability(config)
    return [source for source, info in availability.items() if info['available']] 