import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any
from logger import get_logger

def fetch_ohlc(symbol, interval='1d', period='6mo'):
    """
    Fetch OHLC data for a symbol using yfinance.
    Returns a pandas DataFrame with columns: ['date', 'open', 'high', 'low', 'close', 'volume']
    """
    logger = get_logger(__name__, log_file_prefix="yfinance_fetcher")
    
    try:
        logger.info(f"Fetching data for {symbol} (interval: {interval}, period: {period})")
        
        # Fetch data from yfinance
        df = yf.download(symbol, interval=interval, period=period, progress=False)
        
        if df is None or df.empty:
            logger.warning(f"No data returned for {symbol}")
            return None
        
        # Reset index to make date a column
        df = df.reset_index()
        
        # Rename columns to lowercase
        df.rename(columns={
            'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume', 'Date': 'date'
        }, inplace=True)
        
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

def fetch_ohlc_enhanced(symbol, interval='1d', period='6mo', validate_data=True):
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
    logger = get_logger(__name__, log_file_prefix="yfinance_fetcher")
    
    try:
        # Fetch basic data
        df = fetch_ohlc(symbol, interval, period)
        
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
    logger = get_logger(__name__, log_file_prefix="yfinance_fetcher")
    
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
            invalid_low = df['low'] > df[['open', 'close']].min(axis=1)
            
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
    Get comprehensive stock information
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Dict or None: Stock information
    """
    logger = get_logger(__name__, log_file_prefix="yfinance_fetcher")
    
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        if not info or len(info) < 5:  # Basic check for valid info
            logger.warning(f"No valid info returned for {symbol}")
            return None
        
        # Extract key information
        stock_info = {
            'symbol': symbol,
            'name': info.get('longName', info.get('shortName', symbol)),
            'sector': info.get('sector'),
            'industry': info.get('industry'),
            'market_cap': info.get('marketCap'),
            'current_price': info.get('currentPrice', info.get('regularMarketPrice')),
            'pe_ratio': info.get('trailingPE'),
            'pb_ratio': info.get('priceToBook'),
            'dividend_yield': info.get('dividendYield'),
            'volume': info.get('volume'),
            'avg_volume': info.get('averageVolume'),
            'fifty_two_week_high': info.get('fiftyTwoWeekHigh'),
            'fifty_two_week_low': info.get('fiftyTwoWeekLow'),
            'currency': info.get('currency'),
            'exchange': info.get('exchange'),
            'country': info.get('country'),
            'timestamp': datetime.now()
        }
        
        logger.info(f"Retrieved stock info for {symbol}")
        return stock_info
        
    except Exception as e:
        logger.error(f"Error getting stock info for {symbol}: {e}")
        return None

def get_real_time_price(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Get real-time price information
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Dict or None: Real-time price data
    """
    logger = get_logger(__name__, log_file_prefix="yfinance_fetcher")
    
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        if 'regularMarketPrice' in info and info['regularMarketPrice']:
            price_data = {
                'symbol': symbol,
                'price': info['regularMarketPrice'],
                'change': info.get('regularMarketChange', 0),
                'change_percent': info.get('regularMarketChangePercent', 0),
                'volume': info.get('volume', 0),
                'market_cap': info.get('marketCap'),
                'pe_ratio': info.get('trailingPE'),
                'timestamp': datetime.now()
            }
            
            logger.debug(f"Retrieved real-time price for {symbol}: ${price_data['price']}")
            return price_data
        
        logger.warning(f"No real-time price available for {symbol}")
        return None
        
    except Exception as e:
        logger.error(f"Error getting real-time price for {symbol}: {e}")
        return None 