import os
import time
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Union
import pandas as pd
import numpy as np
import requests
from dotenv import load_dotenv
import yfinance as yf
from alpha_vantage.timeseries import TimeSeries
from polygon import RESTClient
from logger import get_logger

load_dotenv()

class DataValidationError(Exception):
    """Custom exception for data validation errors"""
    pass

class DataSourceError(Exception):
    """Custom exception for data source errors"""
    pass

class EnhancedDataFetcher:
    """
    Enhanced data fetcher with multiple sources, error handling, and data validation.
    
    Supports:
    - yfinance (free, reliable)
    - Alpha Vantage (free tier with API key)
    - Polygon.io (paid, high-quality)
    - Kite Connect (for Indian markets)
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the enhanced data fetcher
        
        Args:
            config: Configuration dictionary with API keys and settings
        """
        self.config = config or {}
        self.logger = get_logger(__name__, log_file_prefix="data_fetcher")
        
        # API Keys
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY') or self.config.get('ALPHA_VANTAGE_API_KEY')
        self.polygon_api_key = os.getenv('POLYGON_API_KEY') or self.config.get('POLYGON_API_KEY')
        
        # Initialize API clients
        self._init_api_clients()
        
        # Cache settings
        self.cache_enabled = self.config.get('CACHE_ENABLED', True)
        self.cache_duration = self.config.get('CACHE_DURATION', 300)  # 5 minutes
        self._cache = {}
        
        # Retry settings
        self.max_retries = self.config.get('MAX_RETRIES', 3)
        self.retry_delay = self.config.get('RETRY_DELAY', 1)
        
        # Data validation settings
        self.min_data_points = self.config.get('MIN_DATA_POINTS', 10)
        self.max_price_change = self.config.get('MAX_PRICE_CHANGE', 0.5)  # 50% max change
        
        self.logger.info("Enhanced Data Fetcher initialized")

    def _init_api_clients(self):
        """Initialize API clients for different data sources"""
        try:
            if self.alpha_vantage_key:
                self.alpha_vantage = TimeSeries(key=self.alpha_vantage_key, output_format='pandas')
                self.logger.info("Alpha Vantage client initialized")
            else:
                self.alpha_vantage = None
                self.logger.warning("Alpha Vantage API key not found")
                
            if self.polygon_api_key:
                self.polygon = RESTClient(self.polygon_api_key)
                self.logger.info("Polygon.io client initialized")
            else:
                self.polygon = None
                self.logger.warning("Polygon.io API key not found")
                
        except Exception as e:
            self.logger.error(f"Error initializing API clients: {e}")

    def _get_cache_key(self, symbol: str, interval: str, period: str, source: str) -> str:
        """Generate cache key for data"""
        cache_data = f"{symbol}_{interval}_{period}_{source}"
        return hashlib.md5(cache_data.encode()).hexdigest()

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if not self.cache_enabled or cache_key not in self._cache:
            return False
        
        cache_time, _ = self._cache[cache_key]
        return (datetime.now() - cache_time).seconds < self.cache_duration

    def _cache_data(self, cache_key: str, data: pd.DataFrame):
        """Cache data with timestamp"""
        if self.cache_enabled:
            self._cache[cache_key] = (datetime.now(), data)

    def _get_cached_data(self, cache_key: str) -> Optional[pd.DataFrame]:
        """Get cached data if valid"""
        if self._is_cache_valid(cache_key):
            _, data = self._cache[cache_key]
            self.logger.debug(f"Using cached data for key: {cache_key}")
            return data
        return None

    def _validate_data(self, df: pd.DataFrame, symbol: str) -> bool:
        """
        Validate data quality and consistency
        
        Args:
            df: DataFrame to validate
            symbol: Symbol for logging purposes
            
        Returns:
            bool: True if data is valid
        """
        try:
            # Check for minimum data points
            if len(df) < self.min_data_points:
                self.logger.warning(f"{symbol}: Insufficient data points ({len(df)} < {self.min_data_points})")
                return False
            
            # Check for required columns
            required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.logger.error(f"{symbol}: Missing required columns: {missing_columns}")
                return False
            
            # Check for null values
            null_counts = df[required_columns].isnull().sum()
            if null_counts.any():
                self.logger.warning(f"{symbol}: Found null values: {null_counts.to_dict()}")
                # Remove rows with null values
                df.dropna(subset=required_columns, inplace=True)
                if len(df) < self.min_data_points:
                    self.logger.error(f"{symbol}: Too many null values, insufficient data after cleaning")
                    return False
            
            # Check for price anomalies
            for col in ['open', 'high', 'low', 'close']:
                if col in df.columns:
                    # Check for negative prices
                    if (df[col] <= 0).any():
                        self.logger.error(f"{symbol}: Found negative or zero prices in {col}")
                        return False
                    
                    # Check for extreme price changes
                    price_changes = df[col].pct_change().abs()
                    if (price_changes > self.max_price_change).any():
                        self.logger.warning(f"{symbol}: Found extreme price changes in {col}: {price_changes.max():.2%}")
            
            # Check for volume anomalies
            if 'volume' in df.columns:
                if (df['volume'] < 0).any():
                    self.logger.error(f"{symbol}: Found negative volume")
                    return False
            
            # Check for OHLC consistency
            if all(col in df.columns for col in ['open', 'high', 'low', 'close']):
                # High should be >= max of open, close
                # Low should be <= min of open, close
                invalid_high = df['high'] < df[['open', 'close']].max(axis=1)
                invalid_low = df['low'] > df[['open', 'low', 'close']].min(axis=1)
                
                if invalid_high.any() or invalid_low.any():
                    self.logger.warning(f"{symbol}: Found OHLC inconsistencies")
                    # Fix inconsistencies
                    df['high'] = df[['open', 'high', 'close']].max(axis=1)
                    df['low'] = df[['open', 'low', 'close']].min(axis=1)
            
            self.logger.debug(f"{symbol}: Data validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"{symbol}: Data validation error: {e}")
            return False

    def _normalize_dataframe(self, df: pd.DataFrame, source: str) -> pd.DataFrame:
        """
        Normalize DataFrame to standard format
        
        Args:
            df: Raw DataFrame from data source
            source: Data source name for logging
            
        Returns:
            pd.DataFrame: Normalized DataFrame
        """
        try:
            # Make a copy to avoid modifying original
            df = df.copy()
            
            # Handle yfinance multi-level columns
            if source == 'yfinance' and isinstance(df.columns, pd.MultiIndex):
                # Flatten multi-level columns
                df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
            
            # Reset index if date is in index
            if df.index.name == 'Date' or 'Date' in str(df.index.name):
                df = df.reset_index()
            
            # Standardize column names
            column_mapping = {
                # yfinance
                'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume', 'Date': 'date',
                # Alpha Vantage
                '1. open': 'open', '2. high': 'high', '3. low': 'low', '4. close': 'close', '5. volume': 'volume',
                # Polygon
                'o': 'open', 'h': 'high', 'l': 'low', 'c': 'close', 'v': 'volume', 't': 'date',
                # Generic
                'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close', 'volume': 'volume', 'date': 'date'
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
            
            # Sort by date
            if 'date' in df.columns:
                df = df.sort_values('date').reset_index(drop=True)
            
            # Select only required columns
            required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
            available_columns = [col for col in required_columns if col in df.columns]
            df = df[available_columns]
            
            self.logger.debug(f"Data normalized from {source}: {len(df)} rows, columns: {list(df.columns)}")
            return df
            
        except Exception as e:
            self.logger.error(f"Error normalizing data from {source}: {e}")
            raise DataValidationError(f"Data normalization failed for {source}: {e}")

    def _fetch_with_retry(self, fetch_func, *args, **kwargs) -> Optional[pd.DataFrame]:
        """
        Fetch data with retry logic
        
        Args:
            fetch_func: Function to call for fetching data
            *args, **kwargs: Arguments for fetch_func
            
        Returns:
            pd.DataFrame or None: Fetched data or None if failed
        """
        for attempt in range(self.max_retries):
            try:
                data = fetch_func(*args, **kwargs)
                if data is not None and not data.empty:
                    return data
                else:
                    self.logger.warning(f"Empty data returned on attempt {attempt + 1}")
                    
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                    
        self.logger.error(f"All {self.max_retries} attempts failed")
        return None

    def fetch_from_yfinance(self, symbol: str, interval: str = '1d', period: str = '6mo') -> Optional[pd.DataFrame]:
        """
        Fetch data from yfinance
        
        Args:
            symbol: Stock symbol
            interval: Data interval
            period: Data period
            
        Returns:
            pd.DataFrame or None: OHLCV data
        """
        try:
            self.logger.debug(f"Fetching from yfinance: {symbol}")
            df = yf.download(symbol, interval=interval, period=period, progress=False)
            
            if df is None or df.empty:
                self.logger.warning(f"No data returned from yfinance for {symbol}")
                return None
            
            df = self._normalize_dataframe(df, 'yfinance')
            return df
            
        except Exception as e:
            self.logger.error(f"yfinance fetch error for {symbol}: {e}")
            return None

    def fetch_from_alpha_vantage(self, symbol: str, interval: str = 'daily', outputsize: str = 'compact') -> Optional[pd.DataFrame]:
        """
        Fetch data from Alpha Vantage
        
        Args:
            symbol: Stock symbol
            interval: Data interval
            outputsize: Data size ('compact' or 'full')
            
        Returns:
            pd.DataFrame or None: OHLCV data
        """
        if not self.alpha_vantage:
            self.logger.warning("Alpha Vantage not available")
            return None
            
        try:
            self.logger.debug(f"Fetching from Alpha Vantage: {symbol}")
            
            if interval == 'daily':
                df, meta = self.alpha_vantage.get_daily(symbol, outputsize=outputsize)
            elif interval == 'intraday':
                df, meta = self.alpha_vantage.get_intraday(symbol, outputsize=outputsize)
            else:
                self.logger.warning(f"Unsupported interval for Alpha Vantage: {interval}")
                return None
            
            if df is None or df.empty:
                self.logger.warning(f"No data returned from Alpha Vantage for {symbol}")
                return None
            
            # Alpha Vantage returns data with date as index, need to reset it
            if df.index.name is None or 'date' in str(df.index.name).lower():
                df = df.reset_index()
                # Rename the first column to 'date' if it's not already named
                if len(df.columns) > 0 and df.columns[0] != 'date':
                    df.rename(columns={df.columns[0]: 'date'}, inplace=True)
            
            df = self._normalize_dataframe(df, 'alpha_vantage')
            return df
            
        except Exception as e:
            self.logger.error(f"Alpha Vantage fetch error for {symbol}: {e}")
            return None

    def fetch_from_polygon(self, symbol: str, from_date: str, to_date: str, interval: str = 'day') -> Optional[pd.DataFrame]:
        """
        Fetch data from Polygon.io
        
        Args:
            symbol: Stock symbol
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            interval: Data interval
            
        Returns:
            pd.DataFrame or None: OHLCV data
        """
        if not self.polygon:
            self.logger.warning("Polygon.io not available")
            return None
            
        try:
            self.logger.debug(f"Fetching from Polygon.io: {symbol}")
            
            # Convert interval to Polygon format
            interval_map = {'day': 'day', 'hour': 'hour', 'minute': 'minute'}
            polygon_interval = interval_map.get(interval, 'day')
            
            # Get historical data
            data = self.polygon.get_aggs(
                ticker=symbol,
                multiplier=1,
                timespan=polygon_interval,
                from_=from_date,
                to=to_date
            )
            
            if not data:
                self.logger.warning(f"No data returned from Polygon.io for {symbol}")
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
            df = self._normalize_dataframe(df, 'polygon')
            return df
            
        except Exception as e:
            self.logger.error(f"Polygon.io fetch error for {symbol}: {e}")
            return None

    def fetch_ohlc(self, symbol: str, interval: str = '1d', period: str = '6mo', 
                   sources: Optional[List[str]] = None, use_cache: bool = True, 
                   save_to_db: bool = True) -> Optional[Dict[str, Any]]:
        """
        Fetch OHLC data from multiple sources with fallback
        
        Args:
            symbol: Stock symbol
            interval: Data interval
            period: Data period
            sources: List of data sources to try (in order)
            use_cache: Whether to use caching
            save_to_db: Whether to save data to database
            
        Returns:
            Dict with 'data' (DataFrame) and 'source' (str) or None
        """
        if sources is None:
            # Get sources from config, fallback to default
            sources = self.config.get('DATA_SOURCES', ['yfinance', 'alpha_vantage', 'polygon'])
        
        # Check cache first
        if use_cache:
            cache_key = self._get_cache_key(symbol, interval, period, '_'.join(sources))
            cached_data = self._get_cached_data(cache_key)
            if cached_data is not None:
                return {'data': cached_data, 'source': 'cache'}
        
        self.logger.info(f"Fetching data for {symbol} from sources: {sources}")
        
        # Try each source in order
        for source in sources:
            try:
                if source == 'yfinance':
                    df = self._fetch_with_retry(self.fetch_from_yfinance, symbol, interval, period)
                elif source == 'alpha_vantage':
                    df = self._fetch_with_retry(self.fetch_from_alpha_vantage, symbol)
                elif source == 'polygon':
                    # Calculate date range for Polygon
                    end_date = datetime.now()
                    if period == '6mo':
                        start_date = end_date - timedelta(days=180)
                    elif period == '1y':
                        start_date = end_date - timedelta(days=365)
                    else:
                        start_date = end_date - timedelta(days=30)
                    
                    df = self._fetch_with_retry(
                        self.fetch_from_polygon, 
                        symbol, 
                        start_date.strftime('%Y-%m-%d'),
                        end_date.strftime('%Y-%m-%d'),
                        interval
                    )
                else:
                    self.logger.warning(f"Unknown data source: {source}")
                    continue
                
                if df is not None and not df.empty:
                    # Validate data
                    if self._validate_data(df, symbol):
                        # Save to individual source table if requested
                        if save_to_db:
                            self._save_to_source_db(symbol, df, source)
                        
                        # Cache the data
                        if use_cache:
                            cache_key = self._get_cache_key(symbol, interval, period, '_'.join(sources))
                            self._cache_data(cache_key, df)
                        
                        self.logger.info(f"Successfully fetched data for {symbol} from {source}: {len(df)} rows")
                        return {'data': df, 'source': source}
                    else:
                        self.logger.warning(f"Data validation failed for {symbol} from {source}")
                        
            except Exception as e:
                self.logger.error(f"Error fetching from {source} for {symbol}: {e}")
                continue
        
        self.logger.error(f"Failed to fetch data for {symbol} from all sources")
        return None

    def _save_to_source_db(self, symbol: str, df: pd.DataFrame, source: str):
        """
        Save data to individual source table
        
        Args:
            symbol: Stock symbol
            df: DataFrame with OHLCV data
            source: Data source used
        """
        try:
            from postgres import store_ohlcv_data
            
            # Save to individual source table
            store_ohlcv_data(df, source, symbol)
            
        except Exception as e:
            self.logger.error(f"Error saving data to {source} database: {e}")

    def load_from_source_db(self, symbol: str, source: str, days_fresh: int = 1) -> Optional[Dict[str, Any]]:
        """
        Load data from individual source database
        
        Args:
            symbol: Stock symbol
            source: Data source name
            days_fresh: Consider data fresh for N days
            
        Returns:
            Dict with 'data' (DataFrame) and 'source' (str) or None
        """
        try:
            from postgres import load_ohlcv_data, check_data_freshness
            
            # Check if data is fresh
            if check_data_freshness(symbol, source, days_fresh):
                df = load_ohlcv_data(symbol, source)
                if df is not None and not df.empty:
                    self.logger.info(f"Loaded {len(df)} records for {symbol} from {source} DB")
                    return {'data': df, 'source': source}
            
            self.logger.info(f"No fresh data found in {source} DB for {symbol}")
            return None
                
        except Exception as e:
            self.logger.error(f"Error loading from {source} database: {e}")
            return None

    def get_real_time_price(self, symbol: str, source: str = 'yfinance') -> Optional[Dict[str, Any]]:
        """
        Get real-time price for a symbol
        
        Args:
            symbol: Stock symbol
            source: Data source to use
            
        Returns:
            Dict or None: Real-time price data
        """
        try:
            if source == 'yfinance':
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                if 'regularMarketPrice' in info and info['regularMarketPrice']:
                    return {
                        'symbol': symbol,
                        'price': info['regularMarketPrice'],
                        'change': info.get('regularMarketChange', 0),
                        'change_percent': info.get('regularMarketChangePercent', 0),
                        'volume': info.get('volume', 0),
                        'timestamp': datetime.now(),
                        'source': source
                    }
            
            elif source == 'alpha_vantage' and self.alpha_vantage:
                # Alpha Vantage real-time quote
                quote, _ = self.alpha_vantage.get_quote_endpoint(symbol)
                if quote:
                    return {
                        'symbol': symbol,
                        'price': float(quote['05. price']),
                        'change': float(quote['09. change']),
                        'change_percent': float(quote['10. change percent'].rstrip('%')),
                        'volume': int(quote['06. volume']),
                        'timestamp': datetime.now(),
                        'source': source
                    }
            
            self.logger.warning(f"Real-time price not available for {symbol} from {source}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting real-time price for {symbol} from {source}: {e}")
            return None

    def get_market_status(self) -> Dict[str, Any]:
        """
        Get current market status
        
        Returns:
            Dict: Market status information
        """
        try:
            # Check if market is open (simplified logic)
            now = datetime.now()
            is_weekend = now.weekday() >= 5
            is_market_hours = now.time() >= datetime.strptime("09:30", "%H:%M").time() and now.time() <= datetime.strptime("16:00", "%H:%M").time()
            
            return {
                'is_open': not is_weekend and is_market_hours,
                'current_time': now,
                'is_weekend': is_weekend,
                'is_market_hours': is_market_hours
            }
            
        except Exception as e:
            self.logger.error(f"Error getting market status: {e}")
            return {'is_open': False, 'error': str(e)}

    def clear_cache(self):
        """Clear the data cache"""
        self._cache.clear()
        self.logger.info("Data cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'cache_enabled': self.cache_enabled,
            'cache_size': len(self._cache),
            'cache_duration': self.cache_duration
        } 