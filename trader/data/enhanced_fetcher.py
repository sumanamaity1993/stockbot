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
        self.max_retries = self.config.get('MAX_RETRIES', 2)
        self.retry_delay = self.config.get('RETRY_DELAY', 1)
        
        # Data validation settings
        self.min_data_points = self.config.get('MIN_DATA_POINTS', 10)
        self.max_price_change = self.config.get('MAX_PRICE_CHANGE', 0.5)  # 50% max change
        
        # SMART: Adaptive rate limiting
        self.rate_limit_history = {
            'yfinance': {'success': 0, 'rate_limited': 0, 'last_rate_limit': None},
            'alpha_vantage': {'success': 0, 'rate_limited': 0, 'last_rate_limit': None},
            'polygon': {'success': 0, 'rate_limited': 0, 'last_rate_limit': None}
        }
        self.adaptive_delays = {
            'yfinance': self.config.get('RATE_LIMIT_DELAY', 0.1),
            'alpha_vantage': self.config.get('RATE_LIMIT_DELAY', 0.1),
            'polygon': self.config.get('RATE_LIMIT_DELAY', 0.1)
        }
        
        self.logger.info("Enhanced Data Fetcher initialized with adaptive rate limiting")

    def _init_api_clients(self):
        """Initialize API clients for different data sources"""
        try:
            # yfinance is always available (no API key needed)
            self.logger.info("yfinance client initialized")
            
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

    def fetch_ohlc_incremental(self, symbol: str, interval: str = '1d', period: str = '6mo', 
                              sources: Optional[List[str]] = None, use_cache: bool = True, 
                              save_to_db: bool = True) -> Optional[Dict[str, Any]]:
        """
        Smart incremental OHLC data fetching - only fetch missing data
        SCALABLE: Minimizes API calls, handles rate limits, parallel processing
        
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
            sources = self.config.get('DATA_SOURCES', ['yfinance', 'alpha_vantage', 'polygon'])
        
        # Calculate target date range
        end_date = datetime.now()
        if period == '6mo':
            target_start_date = end_date - timedelta(days=180)
        elif period == '1y':
            target_start_date = end_date - timedelta(days=365)
        else:
            target_start_date = end_date - timedelta(days=30)
        
        self.logger.info(f"🔄 SCALABLE Incremental fetch for {symbol}: Target period {target_start_date.date()} to {end_date.date()}")
        
        # Check existing data in DB for each source (parallel check for scale)
        existing_data = {}
        missing_periods = {}
        
        for source in sources:
            try:
                from postgres import load_ohlcv_data, check_data_freshness
                
                # Load existing data from DB
                df_existing = load_ohlcv_data(symbol, source)
                if df_existing is not None and not df_existing.empty:
                    existing_data[source] = df_existing
                    
                    # Find missing periods (optimized for large datasets)
                    df_existing['date'] = pd.to_datetime(df_existing['date'])
                    existing_dates = set(df_existing['date'].dt.date)
                    
                    # Calculate missing dates (efficient date range check)
                    missing_dates = []
                    current_date = target_start_date.date()
                    while current_date <= end_date.date():
                        if current_date not in existing_dates:
                            missing_dates.append(current_date)
                        current_date += timedelta(days=1)
                    
                    if missing_dates:
                        missing_start = min(missing_dates)
                        missing_end = max(missing_dates)
                        missing_periods[source] = {
                            'start_date': missing_start,
                            'end_date': missing_end,
                            'days_missing': len(missing_dates),
                            'completion_percentage': (len(existing_dates) / (len(existing_dates) + len(missing_dates))) * 100
                        }
                        self.logger.info(f"📊 {source}: Missing {len(missing_dates)} days ({missing_start} to {missing_end}) - {missing_periods[source]['completion_percentage']:.1f}% complete")
                    else:
                        self.logger.info(f"✅ {source}: Complete data available in DB (100% complete)")
                        
            except Exception as e:
                self.logger.warning(f"⚠️ {source}: Error checking existing data: {e}")
        
        # SCALING OPTIMIZATION: Prioritize sources with highest completion percentage
        prioritized_sources = sorted(
            missing_periods.items(), 
            key=lambda x: x[1]['completion_percentage'], 
            reverse=True
        )
        
        if prioritized_sources:
            self.logger.info(f"🎯 SCALING: Prioritizing sources by completion: {[f'{s[0]}({s[1]['completion_percentage']:.1f}%)' for s in prioritized_sources]}")
        
        # Try to fetch missing data from APIs (with rate limit awareness)
        fetched_data = {}
        rate_limited_sources = []
        
        for source, missing_info in prioritized_sources:
            self.logger.info(f"🔄 Fetching missing data for {symbol} from {source}: {missing_info['days_missing']} days")
            
            try:
                # Add delay between API calls to respect rate limits
                if len(fetched_data) > 0:
                    time.sleep(self.adaptive_delays[source])
                
                if source == 'yfinance':
                    # For yfinance, we need to fetch the full period and merge
                    df_new = self._fetch_with_retry(self.fetch_from_yfinance, symbol, interval, period)
                elif source == 'alpha_vantage':
                    df_new = self._fetch_with_retry(self.fetch_from_alpha_vantage, symbol)
                elif source == 'polygon':
                    df_new = self._fetch_with_retry(
                        self.fetch_from_polygon,
                        symbol,
                        missing_info['start_date'].strftime('%Y-%m-%d'),
                        missing_info['end_date'].strftime('%Y-%m-%d'),
                        interval
                    )
                
                if df_new is not None and not df_new.empty:
                    fetched_data[source] = df_new
                    self.logger.info(f"✅ {source}: Fetched {len(df_new)} new records for {symbol}")
                    self.rate_limit_history[source]['success'] += 1
                else:
                    self.logger.warning(f"❌ {source}: Failed to fetch missing data for {symbol}")
                    self.rate_limit_history[source]['rate_limited'] += 1
                    
            except Exception as e:
                error_msg = str(e).lower()
                if "rate limit" in error_msg or "429" in error_msg:
                    rate_limited_sources.append(source)
                    self.logger.warning(f"⚠️ {source}: Rate limited for {symbol}, will use existing data")
                    self.rate_limit_history[source]['rate_limited'] += 1
                else:
                    self.logger.error(f"❌ {source}: Error fetching missing data for {symbol}: {e}")
        
        # SCALING OPTIMIZATION: Smart data combination with conflict resolution
        combined_data = {}
        
        for source in sources:
            if source in existing_data:
                df_existing = existing_data[source]
                
                if source in fetched_data:
                    # Merge existing + new data with conflict resolution
                    df_new = fetched_data[source]
                    
                    # Remove duplicates and conflicts (new data takes precedence)
                    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
                    df_combined = df_combined.drop_duplicates(subset=['date'], keep='last')
                    df_combined = df_combined.sort_values('date')
                    
                    # Validate combined data integrity
                    if len(df_combined) >= len(df_existing):
                        self.logger.info(f"🔄 {source}: Combined {len(df_existing)} existing + {len(df_new)} new = {len(df_combined)} total records")
                        combined_data[source] = df_combined
                        
                        # Save combined data to DB
                        if save_to_db:
                            self._save_to_source_db(symbol, df_combined, source)
                    else:
                        self.logger.warning(f"⚠️ {source}: Data combination failed, using existing data")
                        combined_data[source] = df_existing
                        
                else:
                    # Use existing data only (rate limited or failed)
                    if source in rate_limited_sources:
                        self.logger.info(f"📊 {source}: Using existing data due to rate limits ({len(df_existing)} records)")
                    else:
                        self.logger.info(f"📊 {source}: Using existing data only ({len(df_existing)} records)")
                    combined_data[source] = df_existing
                    
            elif source in fetched_data:
                # Only new data available
                df_new = fetched_data[source]
                combined_data[source] = df_new
                
                # Save new data to DB
                if save_to_db:
                    self._save_to_source_db(symbol, df_new, source)
        
        # SCALING OPTIMIZATION: Return best available data with quality scoring
        best_source = None
        best_score = 0
        
        for source in sources:
            if source in combined_data:
                df = combined_data[source]
                if self._validate_data(df, symbol):
                    # Calculate quality score based on completeness and recency
                    completeness = len(df) / 180 if period == '6mo' else len(df) / 365 if period == '1y' else len(df) / 30
                    recency = 1.0 if df['date'].max().date() >= end_date.date() else 0.5
                    quality_score = (completeness * 0.7) + (recency * 0.3)
                    
                    if quality_score > best_score:
                        best_score = quality_score
                        best_source = source
        
        if best_source:
            df = combined_data[best_source]
            self.logger.info(f"✅ SCALABLE Incremental fetch completed for {symbol} from {best_source}: {len(df)} total records (quality score: {best_score:.2f})")
            return {'data': df, 'source': best_source}
        
        self.logger.error(f"❌ SCALABLE Incremental fetch failed for {symbol} from all sources")
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

    def fetch_ohlc_batch(self, symbols: List[str], interval: str = '1d', period: str = '6mo',
                        sources: Optional[List[str]] = None, max_concurrent: int = 5,
                        rate_limit_delay: float = 0.1) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        SCALABLE: Batch fetch OHLC data for multiple symbols with rate limiting
        
        Args:
            symbols: List of stock symbols
            interval: Data interval
            period: Data period
            sources: List of data sources to try
            max_concurrent: Maximum concurrent API requests
            rate_limit_delay: Delay between requests to respect rate limits
            
        Returns:
            Dict mapping symbol to fetch result
        """
        if sources is None:
            sources = self.config.get('DATA_SOURCES', ['yfinance', 'alpha_vantage', 'polygon'])
        
        self.logger.info(f"🚀 SCALABLE Batch fetch: {len(symbols)} symbols, {len(sources)} sources, max {max_concurrent} concurrent")
        
        results = {}
        successful = 0
        failed = 0
        rate_limited = 0
        
        # Process symbols in batches to respect rate limits
        for i in range(0, len(symbols), max_concurrent):
            batch = symbols[i:i + max_concurrent]
            self.logger.info(f"📦 Processing batch {i//max_concurrent + 1}: {batch}")
            
            for symbol in batch:
                try:
                    # Add delay between symbols to respect rate limits
                    if len(results) > 0:
                        time.sleep(rate_limit_delay)
                    
                    result = self.fetch_ohlc_incremental(
                        symbol, interval, period, sources, 
                        use_cache=True, save_to_db=True
                    )
                    
                    if result is not None:
                        results[symbol] = result
                        successful += 1
                        self.logger.info(f"✅ {symbol}: Batch fetch successful")
                    else:
                        results[symbol] = None
                        failed += 1
                        self.logger.warning(f"❌ {symbol}: Batch fetch failed")
                        
                except Exception as e:
                    error_msg = str(e).lower()
                    if "rate limit" in error_msg or "429" in error_msg:
                        rate_limited += 1
                        self.logger.warning(f"⚠️ {symbol}: Rate limited in batch")
                    else:
                        failed += 1
                        self.logger.error(f"❌ {symbol}: Batch fetch error: {e}")
                    
                    results[symbol] = None
            
            # Add delay between batches
            if i + max_concurrent < len(symbols):
                time.sleep(rate_limit_delay * 2)
        
        # Summary
        self.logger.info(f"📊 SCALABLE Batch fetch completed:")
        self.logger.info(f"   ✅ Successful: {successful}")
        self.logger.info(f"   ❌ Failed: {failed}")
        self.logger.info(f"   ⚠️ Rate limited: {rate_limited}")
        self.logger.info(f"   📈 Success rate: {(successful/len(symbols)*100):.1f}%")
        
        return results

    def _update_adaptive_delays(self, source: str, was_rate_limited: bool):
        """
        SMART: Update adaptive delays based on API response patterns
        """
        try:
            history = self.rate_limit_history[source]
            
            if was_rate_limited:
                history['rate_limited'] += 1
                history['last_rate_limit'] = datetime.now()
                
                # Increase delay if rate limited
                current_delay = self.adaptive_delays[source]
                self.adaptive_delays[source] = min(current_delay * 1.5, 2.0)  # Max 2 seconds
                
                self.logger.info(f"🧠 {source}: Rate limited, increased delay to {self.adaptive_delays[source]:.2f}s")
            else:
                history['success'] += 1
                
                # Gradually decrease delay on success (but not too quickly)
                if history['success'] % 10 == 0:  # Every 10 successful calls
                    current_delay = self.adaptive_delays[source]
                    base_delay = self.config.get('RATE_LIMIT_DELAY', 0.1)
                    
                    # Don't go below base delay
                    if current_delay > base_delay:
                        self.adaptive_delays[source] = max(current_delay * 0.9, base_delay)
                        self.logger.info(f"🧠 {source}: Success streak, decreased delay to {self.adaptive_delays[source]:.2f}s")
            
            # Calculate success rate
            total_calls = history['success'] + history['rate_limited']
            if total_calls > 0:
                success_rate = history['success'] / total_calls
                
                # Reset delays if success rate is very high
                if success_rate > 0.95 and total_calls > 20:
                    self.adaptive_delays[source] = self.config.get('RATE_LIMIT_DELAY', 0.1)
                    self.logger.info(f"🧠 {source}: High success rate ({success_rate:.1%}), reset delay to base")
                    
        except Exception as e:
            self.logger.warning(f"⚠️ Error updating adaptive delays for {source}: {e}")

    def get_adaptive_stats(self) -> Dict[str, Any]:
        """
        Get adaptive rate limiting statistics
        """
        stats = {}
        for source, history in self.rate_limit_history.items():
            total_calls = history['success'] + history['rate_limited']
            success_rate = history['success'] / total_calls if total_calls > 0 else 0
            
            stats[source] = {
                'success_count': history['success'],
                'rate_limited_count': history['rate_limited'],
                'total_calls': total_calls,
                'success_rate': success_rate,
                'current_delay': self.adaptive_delays[source],
                'last_rate_limit': history['last_rate_limit']
            }
        
        return stats

    def predict_and_prefetch_data(self, symbols: List[str], prediction_hours: int = 24) -> Dict[str, Any]:
        """
        SMART: Predictive data fetching - anticipate data needs and pre-fetch during low traffic
        
        Args:
            symbols: List of symbols to predict for
            prediction_hours: Hours ahead to predict
            
        Returns:
            Prediction results and prefetch recommendations
        """
        try:
            from datetime import datetime, timedelta
            import random
            
            # Get current market status
            market_status = self.get_market_status()
            current_hour = datetime.now().hour
            
            # Predict optimal prefetch times (low traffic periods)
            low_traffic_hours = [2, 3, 4, 5, 6, 22, 23]  # Off-market hours
            is_low_traffic = current_hour in low_traffic_hours
            
            # Calculate data freshness predictions
            predictions = {}
            prefetch_recommendations = []
            
            for symbol in symbols:
                try:
                    # Check current data freshness for each source
                    source_freshness = {}
                    for source in self.config.get('DATA_SOURCES', ['yfinance', 'alpha_vantage', 'polygon']):
                        from postgres import check_data_freshness
                        
                        # Check if data will be stale in prediction_hours
                        will_be_stale = not check_data_freshness(symbol, source, days_threshold=prediction_hours/24)
                        
                        source_freshness[source] = {
                            'will_be_stale': will_be_stale,
                            'recommend_prefetch': will_be_stale and is_low_traffic
                        }
                    
                    # Calculate prefetch priority score
                    priority_score = sum(1 for s in source_freshness.values() if s['will_be_stale'])
                    
                    predictions[symbol] = {
                        'source_freshness': source_freshness,
                        'priority_score': priority_score,
                        'recommend_prefetch': priority_score > 0 and is_low_traffic
                    }
                    
                    if predictions[symbol]['recommend_prefetch']:
                        prefetch_recommendations.append({
                            'symbol': symbol,
                            'priority_score': priority_score,
                            'reason': f"Data will be stale in {prediction_hours} hours"
                        })
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ Error predicting for {symbol}: {e}")
            
            # Sort recommendations by priority
            prefetch_recommendations.sort(key=lambda x: x['priority_score'], reverse=True)
            
            # Execute prefetch for high-priority symbols (limit to avoid overwhelming APIs)
            max_prefetch = min(10, len(prefetch_recommendations))
            prefetched_symbols = []
            
            if prefetch_recommendations and is_low_traffic:
                self.logger.info(f"🧠 SMART: Predictive prefetch during low traffic (hour {current_hour})")
                
                for i, rec in enumerate(prefetch_recommendations[:max_prefetch]):
                    try:
                        self.logger.info(f"🔄 Prefetching {rec['symbol']} (priority: {rec['priority_score']})")
                        
                        result = self.fetch_ohlc_incremental(
                            rec['symbol'], 
                            interval='1d', 
                            period='6mo',
                            sources=self.config.get('DATA_SOURCES', ['yfinance', 'alpha_vantage', 'polygon']),
                            use_cache=True,
                            save_to_db=True
                        )
                        
                        if result is not None:
                            prefetched_symbols.append(rec['symbol'])
                            self.logger.info(f"✅ Prefetched {rec['symbol']} successfully")
                        
                        # Add delay between prefetch requests (use default source for adaptive delay)
                        default_source = 'yfinance'  # Use yfinance as default for adaptive delays
                        time.sleep(self.adaptive_delays.get(default_source, 0.1))
                        
                    except Exception as e:
                        self.logger.warning(f"⚠️ Prefetch failed for {rec['symbol']}: {e}")
            
            return {
                'predictions': predictions,
                'prefetch_recommendations': prefetch_recommendations,
                'prefetched_symbols': prefetched_symbols,
                'is_low_traffic': is_low_traffic,
                'current_hour': current_hour,
                'market_status': market_status
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error in predictive prefetch: {e}")
            return {}

    def _smart_cache_warming(self, symbols: List[str], sources: List[str]):
        """
        SMART: Warm cache with frequently accessed data during low traffic
        """
        try:
            from datetime import datetime
            current_hour = datetime.now().hour
            
            # Only warm cache during low traffic hours
            low_traffic_hours = [2, 3, 4, 5, 6, 22, 23]
            if current_hour not in low_traffic_hours:
                return
            
            self.logger.info(f"🔥 SMART: Warming cache for {len(symbols)} symbols during low traffic")
            
            # Warm cache for high-priority symbols (first 20)
            priority_symbols = symbols[:20]
            
            for symbol in priority_symbols:
                try:
                    # Check if symbol is already cached
                    cache_key = self._get_cache_key(symbol, '1d', '6mo', '_'.join(sources))
                    
                    if not self._is_cache_valid(cache_key):
                        # Load from DB and cache
                        for source in sources:
                            try:
                                from postgres import load_ohlcv_data
                                df = load_ohlcv_data(symbol, source)
                                
                                if df is not None and not df.empty:
                                    self._cache_data(cache_key, df)
                                    self.logger.info(f"🔥 Cached {symbol} from {source}")
                                    break  # Cache from first available source
                                    
                            except Exception as e:
                                continue
                    
                    # Add delay between cache warming requests
                    time.sleep(0.05)  # Very short delay for cache warming
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Error warming cache for {symbol}: {e}")
            
            self.logger.info(f"🔥 Cache warming completed for {len(priority_symbols)} symbols")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error in cache warming: {e}")

    def _intelligent_cache_invalidation(self):
        """
        SMART: Intelligently invalidate cache based on data freshness and usage patterns
        """
        try:
            current_time = datetime.now()
            invalidated_keys = []
            
            for cache_key, (cache_time, data) in self._cache.items():
                # Calculate cache age
                cache_age = (current_time - cache_time).total_seconds()
                
                # Invalidate old cache entries (older than cache_duration)
                if cache_age > self.cache_duration:
                    invalidated_keys.append(cache_key)
                    continue
                
                # Invalidate cache for market hours if data is from previous day
                current_hour = current_time.hour
                if 9 <= current_hour <= 16:  # Market hours
                    cache_hour = cache_time.hour
                    if cache_hour < 9:  # Data from before market open
                        invalidated_keys.append(cache_key)
                        continue
            
            # Remove invalidated keys
            for key in invalidated_keys:
                del self._cache[key]
            
            if invalidated_keys:
                self.logger.info(f"🧠 SMART: Invalidated {len(invalidated_keys)} cache entries")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error in cache invalidation: {e}")

    def get_cache_analytics(self) -> Dict[str, Any]:
        """
        Get detailed cache analytics and performance metrics
        """
        try:
            total_cache_size = len(self._cache)
            total_memory_usage = sum(
                data.memory_usage(deep=True).sum() if hasattr(data, 'memory_usage') else 0
                for _, (_, data) in self._cache.items()
            )
            
            # Calculate cache hit rate (would need to track cache hits/misses)
            cache_stats = {
                'total_entries': total_cache_size,
                'total_memory_mb': total_memory_usage / (1024 * 1024),
                'cache_duration': self.cache_duration,
                'cache_enabled': self.cache_enabled,
                'adaptive_delays': self.adaptive_delays.copy(),
                'rate_limit_stats': self.get_adaptive_stats()
            }
            
            return cache_stats
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error getting cache analytics: {e}")
            return {}

    def compress_and_optimize_data(self, df: pd.DataFrame, symbol: str, source: str) -> pd.DataFrame:
        """
        SMART: Compress and optimize data for efficient storage and retrieval
        
        Args:
            df: DataFrame to compress
            symbol: Stock symbol
            source: Data source
            
        Returns:
            Optimized DataFrame
        """
        try:
            if df is None or df.empty:
                return df
            
            # Make a copy to avoid modifying original
            df_optimized = df.copy()
            
            # Optimize data types for storage efficiency
            if 'date' in df_optimized.columns:
                df_optimized['date'] = pd.to_datetime(df_optimized['date'])
            
            # Convert price columns to float32 for memory efficiency (sufficient precision for prices)
            price_columns = ['open', 'high', 'low', 'close']
            for col in price_columns:
                if col in df_optimized.columns:
                    df_optimized[col] = df_optimized[col].astype('float32')
            
            # Convert volume to int32 (sufficient for volume data)
            if 'volume' in df_optimized.columns:
                df_optimized['volume'] = df_optimized['volume'].astype('int32')
            
            # Remove unnecessary precision (round to 4 decimal places for prices)
            for col in price_columns:
                if col in df_optimized.columns:
                    df_optimized[col] = df_optimized[col].round(4)
            
            # Calculate compression ratio
            original_size = df.memory_usage(deep=True).sum()
            optimized_size = df_optimized.memory_usage(deep=True).sum()
            compression_ratio = (1 - optimized_size / original_size) * 100
            
            self.logger.info(f"🧠 {source}: Data compression for {symbol}: {compression_ratio:.1f}% size reduction")
            
            return df_optimized
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error compressing data for {symbol}: {e}")
            return df

    def detect_and_remove_outliers(self, df: pd.DataFrame, symbol: str, method: str = 'iqr') -> pd.DataFrame:
        """
        SMART: Detect and remove statistical outliers from price data
        
        Args:
            df: DataFrame with price data
            symbol: Stock symbol
            method: Outlier detection method ('iqr', 'zscore', 'isolation_forest')
            
        Returns:
            DataFrame with outliers removed
        """
        try:
            if df is None or df.empty:
                return df
            
            df_clean = df.copy()
            original_count = len(df_clean)
            
            if method == 'iqr':
                # IQR method for outlier detection
                for col in ['open', 'high', 'low', 'close']:
                    if col in df_clean.columns:
                        Q1 = df_clean[col].quantile(0.25)
                        Q3 = df_clean[col].quantile(0.75)
                        IQR = Q3 - Q1
                        
                        # Define outlier bounds
                        lower_bound = Q1 - 1.5 * IQR
                        upper_bound = Q3 + 1.5 * IQR
                        
                        # Count outliers
                        outliers = df_clean[(df_clean[col] < lower_bound) | (df_clean[col] > upper_bound)]
                        
                        if len(outliers) > 0:
                            self.logger.info(f"🧠 {symbol}: Detected {len(outliers)} outliers in {col} using IQR method")
                            
                            # Remove outliers
                            df_clean = df_clean[(df_clean[col] >= lower_bound) & (df_clean[col] <= upper_bound)]
            
            elif method == 'zscore':
                # Z-score method for outlier detection
                for col in ['open', 'high', 'low', 'close']:
                    if col in df_clean.columns:
                        z_scores = np.abs((df_clean[col] - df_clean[col].mean()) / df_clean[col].std())
                        outliers = df_clean[z_scores > 3]  # 3 standard deviations
                        
                        if len(outliers) > 0:
                            self.logger.info(f"🧠 {symbol}: Detected {len(outliers)} outliers in {col} using Z-score method")
                            df_clean = df_clean[z_scores <= 3]
            
            # Calculate cleaning statistics
            removed_count = original_count - len(df_clean)
            if removed_count > 0:
                removal_percentage = (removed_count / original_count) * 100
                self.logger.info(f"🧠 {symbol}: Removed {removed_count} outliers ({removal_percentage:.1f}% of data)")
            
            return df_clean
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error removing outliers for {symbol}: {e}")
            return df

    def get_optimal_concurrency(self, source: str) -> Dict[str, Any]:
        """
        SMART: Get optimal concurrency settings for a specific data source
        """
        try:
            # Get source-specific settings
            source_limits = self.config.get('SOURCE_CONCURRENCY_LIMITS', {})
            source_config = source_limits.get(source, {
                'max_concurrent': 5,
                'rate_limit_delay': 0.1,
                'batch_size': 10,
                'priority': 2
            })
            
            # Get adaptive settings
            adaptive_config = self.config.get('ADAPTIVE_CONCURRENCY', {})
            adaptive_enabled = adaptive_config.get('enabled', True)
            
            if adaptive_enabled:
                # Get current success rate for this source
                stats = self.get_adaptive_stats()
                source_stats = stats.get(source, {})
                success_rate = source_stats.get('success_rate', 0.8)
                
                # Adjust concurrency based on success rate
                base_concurrent = source_config['max_concurrent']
                adjustment_factor = adaptive_config.get('adjustment_factor', 1.2)
                
                if success_rate > adaptive_config.get('success_threshold', 0.9):
                    # Increase concurrency on high success rate
                    adjusted_concurrent = min(
                        int(base_concurrent * adjustment_factor),
                        adaptive_config.get('max_concurrent', 20)
                    )
                    source_config['max_concurrent'] = adjusted_concurrent
                    self.logger.info(f"🧠 {source}: High success rate ({success_rate:.1%}), increased concurrency to {adjusted_concurrent}")
                    
                elif success_rate < adaptive_config.get('failure_threshold', 0.7):
                    # Decrease concurrency on low success rate
                    adjusted_concurrent = max(
                        int(base_concurrent / adjustment_factor),
                        adaptive_config.get('min_concurrent', 1)
                    )
                    source_config['max_concurrent'] = adjusted_concurrent
                    self.logger.info(f"🧠 {source}: Low success rate ({success_rate:.1%}), decreased concurrency to {adjusted_concurrent}")
            
            return source_config
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error getting optimal concurrency for {source}: {e}")
            return {'max_concurrent': 5, 'rate_limit_delay': 0.1, 'batch_size': 10, 'priority': 2}

    def fetch_ohlc_batch_smart(self, symbols: List[str], interval: str = '1d', period: str = '6mo',
                              sources: Optional[List[str]] = None) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        SMART: Batch fetch with source-specific concurrency optimization
        """
        if sources is None:
            sources = self.config.get('DATA_SOURCES', ['yfinance', 'alpha_vantage', 'polygon'])
        
        # Sort sources by priority (highest priority first)
        source_priorities = {}
        for source in sources:
            concurrency_config = self.get_optimal_concurrency(source)
            source_priorities[source] = concurrency_config['priority']
        
        sorted_sources = sorted(sources, key=lambda s: source_priorities[s])
        
        self.logger.info(f"🚀 SMART Batch fetch: {len(symbols)} symbols, sources by priority: {sorted_sources}")
        
        results = {}
        successful = 0
        failed = 0
        
        # Process each source with its optimal concurrency
        for source in sorted_sources:
            concurrency_config = self.get_optimal_concurrency(source)
            max_concurrent = concurrency_config['max_concurrent']
            rate_limit_delay = concurrency_config['rate_limit_delay']
            batch_size = concurrency_config['batch_size']
            
            self.logger.info(f"📦 Processing {source} with concurrency {max_concurrent}, batch size {batch_size}")
            
            # Process symbols in optimal batches for this source
            for i in range(0, len(symbols), batch_size):
                batch = symbols[i:i + batch_size]
                
                for symbol in batch:
                    if symbol in results and results[symbol] is not None:
                        continue  # Skip if already successful
                    
                    try:
                        # Add source-specific delay
                        if len(results) > 0:
                            time.sleep(rate_limit_delay)
                        
                        result = self.fetch_ohlc_incremental(
                            symbol, interval, period, [source], 
                            use_cache=True, save_to_db=True
                        )
                        
                        if result is not None:
                            results[symbol] = result
                            successful += 1
                            self.logger.info(f"✅ {symbol}: SMART batch fetch successful from {source}")
                        else:
                            if symbol not in results:
                                results[symbol] = None
                                failed += 1
                            
                    except Exception as e:
                        if symbol not in results:
                            results[symbol] = None
                            failed += 1
                        self.logger.error(f"❌ {symbol}: SMART batch fetch error from {source}: {e}")
                
                # Add delay between batches
                if i + batch_size < len(symbols):
                    time.sleep(rate_limit_delay * 2)
        
        # Summary
        self.logger.info(f"📊 SMART Batch fetch completed:")
        self.logger.info(f"   ✅ Successful: {successful}")
        self.logger.info(f"   ❌ Failed: {failed}")
        self.logger.info(f"   📈 Success rate: {(successful/len(symbols)*100):.1f}%")
        
        return results 