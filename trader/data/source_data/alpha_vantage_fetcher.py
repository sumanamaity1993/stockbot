import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any
from logger import get_logger
import os
from dotenv import load_dotenv
import sys

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from postgres import store_ohlcv_data, load_ohlcv_data, check_data_freshness

# Load environment variables
load_dotenv()

def get_alpha_vantage_client():
    """Get Alpha Vantage client with API key"""
    try:
        from alpha_vantage.timeseries import TimeSeries
        
        api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        if not api_key:
            return None
            
        return TimeSeries(key=api_key, output_format='pandas')
    except ImportError:
        return None
    except Exception as e:
        return None

def fetch_ohlc(symbol, interval='daily', period='6mo'):
    """
    Fetch OHLC data for a symbol using Alpha Vantage.
    Returns a pandas DataFrame with columns: ['date', 'open', 'high', 'low', 'close', 'volume']
    """
    logger = get_logger(__name__, log_file_prefix="alpha_vantage_fetcher")
    
    try:
        logger.info(f"Fetching data for {symbol} (interval: {interval}, period: {period})")
        
        # Get Alpha Vantage client
        client = get_alpha_vantage_client()
        if not client:
            logger.error("Alpha Vantage client not available. Check API key and installation.")
            return None
        
        # Fetch data from Alpha Vantage
        if interval == 'daily':
            df, meta = client.get_daily(symbol, outputsize='compact')
        elif interval == 'intraday':
            df, meta = client.get_intraday(symbol, outputsize='compact')
        else:
            logger.warning(f"Unsupported interval: {interval}. Using daily.")
            df, meta = client.get_daily(symbol, outputsize='compact')
        
        if df is None or df.empty:
            logger.warning(f"No data returned for {symbol}")
            return None
        
        # Reset index to make date a column
        df = df.reset_index()
        
        # Rename columns to standard format
        column_mapping = {
            '1. open': 'open',
            '2. high': 'high', 
            '3. low': 'low',
            '4. close': 'close',
            '5. volume': 'volume'
        }
        
        # Only rename columns that exist
        existing_columns = {k: v for k, v in column_mapping.items() if k in df.columns}
        df.rename(columns=existing_columns, inplace=True)
        
        # Ensure date column is datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        
        # Convert numeric columns
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Remove rows with null values
        df.dropna(subset=['open', 'high', 'low', 'close'], inplace=True)
        
        # Sort by date
        df = df.sort_values('date').reset_index(drop=True)
        
        # Select only required columns
        required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        available_columns = [col for col in required_columns if col in df.columns]
        df = df[available_columns]
        
        logger.info(f"Successfully fetched {len(df)} data points for {symbol}")
        return df
        
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {e}")
        return None

def fetch_ohlc_with_db_cache(symbol, interval='daily', period='6mo', force_fetch=False):
    """
    Fetch OHLC data with database caching.
    First checks if data exists in DB and is fresh, otherwise fetches from API.
    
    Args:
        symbol: Stock symbol
        interval: Data interval
        period: Data period
        force_fetch: Force fetch from API even if data exists in DB
        
    Returns:
        pandas DataFrame or None: OHLCV data
    """
    logger = get_logger(__name__, log_file_prefix="alpha_vantage_fetcher")
    
    try:
        # Check if we should use cached data
        if not force_fetch:
            # Check if data exists and is fresh in DB
            if check_data_freshness(symbol, 'alpha_vantage', days_threshold=1):
                logger.info(f"Using cached data for {symbol} from database")
                df = load_ohlcv_data(symbol, 'alpha_vantage')
                if df is not None and not df.empty:
                    return df
        
        # Fetch fresh data from API
        logger.info(f"Fetching fresh data for {symbol} from Alpha Vantage API")
        df = fetch_ohlc(symbol, interval, period)
        
        if df is not None and not df.empty:
            # Store in database
            logger.info(f"Storing {len(df)} records for {symbol} in database")
            store_ohlcv_data(df, 'alpha_vantage', symbol)
        
        return df
        
    except Exception as e:
        logger.error(f"Error in fetch_ohlc_with_db_cache for {symbol}: {e}")
        return None

def fetch_ohlc_enhanced(symbol, interval='daily', period='6mo', validate_data=True):
    """
    Enhanced version of fetch_ohlc with data validation and quality checks.
    
    Args:
        symbol: Stock symbol
        interval: Data interval
        period: Data period
        validate_data: Whether to perform data validation
        
    Returns:
        pandas DataFrame or None: OHLCV data
    """
    logger = get_logger(__name__, log_file_prefix="alpha_vantage_fetcher")
    
    try:
        # Use DB cache version
        df = fetch_ohlc_with_db_cache(symbol, interval, period)
        
        if df is None or df.empty:
            return None
        
        # Data validation
        if validate_data:
            if not _validate_ohlc_data(df, symbol):
                logger.warning(f"Data validation failed for {symbol}")
                return None
        
        return df
        
    except Exception as e:
        logger.error(f"Error in enhanced fetch for {symbol}: {e}")
        return None

def _validate_ohlc_data(df: pd.DataFrame, symbol: str) -> bool:
    """
    Validate OHLC data for consistency and quality
    
    Args:
        df: DataFrame to validate
        symbol: Symbol for logging
        
    Returns:
        bool: True if data is valid
    """
    logger = get_logger(__name__, log_file_prefix="alpha_vantage_fetcher")
    
    try:
        # Check minimum data points
        if len(df) < 10:
            logger.warning(f"{symbol}: Insufficient data points ({len(df)})")
            return False
        
        # Check for required columns
        required_columns = ['date', 'open', 'high', 'low', 'close']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"{symbol}: Missing required columns: {missing_columns}")
            return False
        
        # Check for null values
        null_counts = df[required_columns].isnull().sum()
        if null_counts.any():
            logger.warning(f"{symbol}: Found null values: {null_counts.to_dict()}")
            return False
        
        # Check for negative prices
        for col in ['open', 'high', 'low', 'close']:
            if (df[col] <= 0).any():
                logger.error(f"{symbol}: Found negative or zero prices in {col}")
                return False
        
        # Check OHLC consistency
        if all(col in df.columns for col in ['open', 'high', 'low', 'close']):
            # High should be >= max of open, close
            # Low should be <= min of open, close
            invalid_high = df['high'] < df[['open', 'close']].max(axis=1)
            invalid_low = df['low'] > df[['open', 'low', 'close']].min(axis=1)
            
            if invalid_high.any() or invalid_low.any():
                logger.warning(f"{symbol}: Found OHLC inconsistencies")
                # Fix inconsistencies
                df['high'] = df[['open', 'high', 'close']].max(axis=1)
                df['low'] = df[['open', 'low', 'close']].min(axis=1)
        
        # Check for volume anomalies
        if 'volume' in df.columns:
            if (df['volume'] < 0).any():
                logger.error(f"{symbol}: Found negative volume")
                return False
        
        logger.debug(f"{symbol}: Data validation passed")
        return True
        
    except Exception as e:
        logger.error(f"{symbol}: Data validation error: {e}")
        return False

def get_stock_info(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Get comprehensive stock information from Alpha Vantage
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Dict or None: Stock information
    """
    logger = get_logger(__name__, log_file_prefix="alpha_vantage_fetcher")
    
    try:
        client = get_alpha_vantage_client()
        if not client:
            return None
        
        # Get company overview
        overview, _ = client.get_company_overview(symbol)
        
        if not overview:
            logger.warning(f"No company overview available for {symbol}")
            return None
        
        # Extract key information
        stock_info = {
            'symbol': symbol,
            'name': overview.get('Name', symbol),
            'sector': overview.get('Sector'),
            'industry': overview.get('Industry'),
            'market_cap': overview.get('MarketCapitalization'),
            'current_price': overview.get('LatestPrice'),
            'pe_ratio': overview.get('PERatio'),
            'pb_ratio': overview.get('PriceToBookRatio'),
            'dividend_yield': overview.get('DividendYield'),
            'volume': overview.get('Volume'),
            'currency': overview.get('Currency'),
            'exchange': overview.get('Exchange'),
            'country': overview.get('Country'),
            'timestamp': datetime.now()
        }
        
        logger.info(f"Retrieved stock info for {symbol}")
        return stock_info
        
    except Exception as e:
        logger.error(f"Error getting stock info for {symbol}: {e}")
        return None

def get_real_time_price(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Get real-time price information from Alpha Vantage
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Dict or None: Real-time price data
    """
    logger = get_logger(__name__, log_file_prefix="alpha_vantage_fetcher")
    
    try:
        client = get_alpha_vantage_client()
        if not client:
            return None
        
        # Get real-time quote
        quote, _ = client.get_quote_endpoint(symbol)
        
        if not quote:
            logger.warning(f"No real-time quote available for {symbol}")
            return None
        
        price_data = {
            'symbol': symbol,
            'price': float(quote['05. price']),
            'change': float(quote['09. change']),
            'change_percent': float(quote['10. change percent'].rstrip('%')),
            'volume': int(quote['06. volume']),
            'timestamp': datetime.now()
        }
        
        logger.debug(f"Retrieved real-time price for {symbol}: ${price_data['price']}")
        return price_data
        
    except Exception as e:
        logger.error(f"Error getting real-time price for {symbol}: {e}")
        return None

class AlphaVantageFetcher:
    @staticmethod
    def fetch_ohlc(symbol, interval='daily', period='6mo'):
        return fetch_ohlc(symbol, interval, period)

    @staticmethod
    def fetch_ohlc_with_db_cache(symbol, interval='daily', period='6mo', force_fetch=False):
        return fetch_ohlc_with_db_cache(symbol, interval, period, force_fetch)

    @staticmethod
    def fetch_ohlc_enhanced(symbol, interval='daily', period='6mo', validate_data=True):
        return fetch_ohlc_enhanced(symbol, interval, period, validate_data)

    @staticmethod
    def get_stock_info(symbol):
        return get_stock_info(symbol)

    @staticmethod
    def get_real_time_price(symbol):
        return get_real_time_price(symbol) 