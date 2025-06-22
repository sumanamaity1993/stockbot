import pandas as pd
from datetime import datetime, timedelta
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

def get_polygon_client():
    """Get Polygon.io client with API key"""
    try:
        from polygon import RESTClient
        
        api_key = os.getenv('POLYGON_API_KEY')
        if not api_key:
            return None
            
        return RESTClient(api_key)
    except ImportError:
        return None
    except Exception as e:
        return None

def fetch_ohlc(symbol, interval='day', period='6mo'):
    """
    Fetch OHLC data for a symbol using Polygon.io.
    Returns a pandas DataFrame with columns: ['date', 'open', 'high', 'low', 'close', 'volume']
    """
    logger = get_logger(__name__, log_file_prefix="polygon_fetcher")
    
    try:
        logger.info(f"Fetching data for {symbol} (interval: {interval}, period: {period})")
        
        # Get Polygon client
        client = get_polygon_client()
        if not client:
            logger.error("Polygon.io client not available. Check API key and installation.")
            return None
        
        # Calculate date range based on period
        end_date = datetime.now()
        if period == '6mo':
            start_date = end_date - timedelta(days=180)
        elif period == '1y':
            start_date = end_date - timedelta(days=365)
        elif period == '3mo':
            start_date = end_date - timedelta(days=90)
        elif period == '1mo':
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=30)  # Default to 1 month
        
        # Convert interval to Polygon format
        interval_map = {'day': 'day', 'hour': 'hour', 'minute': 'minute'}
        polygon_interval = interval_map.get(interval, 'day')
        
        # Fetch data from Polygon.io
        data = client.get_aggs(
            ticker=symbol,
            multiplier=1,
            timespan=polygon_interval,
            from_=start_date.strftime('%Y-%m-%d'),
            to=end_date.strftime('%Y-%m-%d')
        )
        
        if not data:
            logger.warning(f"No data returned for {symbol}")
            return None
        
        # Convert to DataFrame
        df_data = []
        for bar in data:
            df_data.append({
                'date': pd.to_datetime(bar.timestamp, unit='ms'),
                'open': bar.open,
                'high': bar.high,
                'low': bar.low,
                'close': bar.close,
                'volume': bar.volume
            })
        
        df = pd.DataFrame(df_data)
        
        if df.empty:
            logger.warning(f"Empty DataFrame for {symbol}")
            return None
        
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

def fetch_ohlc_with_db_cache(symbol, interval='day', period='6mo', force_fetch=False):
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
    logger = get_logger(__name__, log_file_prefix="polygon_fetcher")
    
    try:
        # Check if we should use cached data
        if not force_fetch:
            # Check if data exists and is fresh in DB
            if check_data_freshness(symbol, 'polygon', days_threshold=1):
                logger.info(f"Using cached data for {symbol} from database")
                df = load_ohlcv_data(symbol, 'polygon')
                if df is not None and not df.empty:
                    return df
        
        # Fetch fresh data from API
        logger.info(f"Fetching fresh data for {symbol} from Polygon.io API")
        df = fetch_ohlc(symbol, interval, period)
        
        if df is not None and not df.empty:
            # Store in database
            logger.info(f"Storing {len(df)} records for {symbol} in database")
            store_ohlcv_data(df, 'polygon', symbol)
        
        return df
        
    except Exception as e:
        logger.error(f"Error in fetch_ohlc_with_db_cache for {symbol}: {e}")
        return None

def fetch_ohlc_enhanced(symbol, interval='day', period='6mo', validate_data=True):
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
    logger = get_logger(__name__, log_file_prefix="polygon_fetcher")
    
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
    logger = get_logger(__name__, log_file_prefix="polygon_fetcher")
    
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
    Get comprehensive stock information from Polygon.io
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Dict or None: Stock information
    """
    logger = get_logger(__name__, log_file_prefix="polygon_fetcher")
    
    try:
        client = get_polygon_client()
        if not client:
            return None
        
        # Get ticker details
        ticker_details = client.get_ticker_details(symbol)
        
        if not ticker_details:
            logger.warning(f"No ticker details available for {symbol}")
            return None
        
        # Extract key information
        stock_info = {
            'symbol': symbol,
            'name': ticker_details.name,
            'sector': getattr(ticker_details, 'sector', None),
            'industry': getattr(ticker_details, 'industry', None),
            'market_cap': getattr(ticker_details, 'market_cap', None),
            'currency': getattr(ticker_details, 'currency_name', None),
            'exchange': getattr(ticker_details, 'primary_exchange', None),
            'country': getattr(ticker_details, 'locale', None),
            'timestamp': datetime.now()
        }
        
        logger.info(f"Retrieved stock info for {symbol}")
        return stock_info
        
    except Exception as e:
        logger.error(f"Error getting stock info for {symbol}: {e}")
        return None

def get_real_time_price(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Get real-time price information from Polygon.io
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Dict or None: Real-time price data
    """
    logger = get_logger(__name__, log_file_prefix="polygon_fetcher")
    
    try:
        client = get_polygon_client()
        if not client:
            return None
        
        # Get last trade
        last_trade = client.get_last_trade(symbol)
        
        if not last_trade:
            logger.warning(f"No real-time price available for {symbol}")
            return None
        
        price_data = {
            'symbol': symbol,
            'price': last_trade.price,
            'volume': last_trade.size,
            'timestamp': datetime.now()
        }
        
        logger.debug(f"Retrieved real-time price for {symbol}: ${price_data['price']}")
        return price_data
        
    except Exception as e:
        logger.error(f"Error getting real-time price for {symbol}: {e}")
        return None 