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

class PolygonFetcher:
    """
    Polygon.io data fetcher class for retrieving stock market data
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Polygon fetcher
        
        Args:
            config: Configuration dictionary (optional)
        """
        self.config = config or {}
        self.logger = get_logger(__name__, log_file_prefix="polygon_fetcher")
        self._client = None
        
    def _get_client(self):
        """Get Polygon.io client with API key"""
        if self._client is not None:
            return self._client
            
        try:
            from polygon import RESTClient
            
            api_key = os.getenv('POLYGON_API_KEY')
            if not api_key:
                self.logger.error("POLYGON_API_KEY not found in environment variables")
                return None
                
            self._client = RESTClient(api_key)
            return self._client
        except ImportError:
            self.logger.error("Polygon.io library not installed. Install with: pip install polygon-api-client")
            return None
        except Exception as e:
            self.logger.error(f"Error creating Polygon client: {e}")
            return None

    def fetch_ohlc(self, symbol: str, interval: str = 'day', period: str = '6mo') -> Optional[pd.DataFrame]:
        """
        Fetch OHLC data for a symbol using Polygon.io.
        Returns a pandas DataFrame with columns: ['date', 'open', 'high', 'low', 'close', 'volume']
        
        Args:
            symbol: Stock symbol
            interval: Data interval (e.g., 'day', 'hour', 'minute')
            period: Data period (e.g., '6mo', '1y')
            
        Returns:
            pandas DataFrame or None: OHLCV data
        """
        try:
            self.logger.info(f"Fetching data for {symbol} (interval: {interval}, period: {period})")
            
            # Get Polygon client
            client = self._get_client()
            if not client:
                self.logger.error("Polygon.io client not available. Check API key and installation.")
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
            
            # Get settings from config
            settings = self.config.get('POLYGON_SETTINGS', {})
            multiplier = settings.get('multiplier', 1)
            
            # Fetch data from Polygon.io
            data = client.get_aggs(
                ticker=symbol,
                multiplier=multiplier,
                timespan=polygon_interval,
                from_=start_date.strftime('%Y-%m-%d'),
                to=end_date.strftime('%Y-%m-%d')
            )
            
            if not data:
                self.logger.warning(f"No data returned for {symbol}")
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
                self.logger.warning(f"Empty DataFrame for {symbol}")
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
            
            self.logger.info(f"Successfully fetched {len(df)} data points for {symbol}")
            return df
            
        except Exception as e:
            self.logger.error(f"Error fetching data for {symbol}: {e}")
            return None

    def fetch_ohlc_with_db_cache(self, symbol: str, interval: str = 'day', period: str = '6mo', 
                                force_fetch: bool = False) -> Optional[pd.DataFrame]:
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
        try:
            # Check if we should use cached data
            if not force_fetch:
                # Check if data exists and is fresh in DB
                days_threshold = self.config.get('CACHE_DURATION', 1)
                if check_data_freshness(symbol, 'polygon', days_threshold=days_threshold):
                    self.logger.info(f"Using cached data for {symbol} from database")
                    df = load_ohlcv_data(symbol, 'polygon')
                    if df is not None and not df.empty:
                        return df
            
            # Fetch fresh data from API
            self.logger.info(f"Fetching fresh data for {symbol} from Polygon.io API")
            df = self.fetch_ohlc(symbol, interval, period)
            
            if df is not None and not df.empty:
                # Store in database
                self.logger.info(f"Storing {len(df)} records for {symbol} in database")
                store_ohlcv_data(df, 'polygon', symbol)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error in fetch_ohlc_with_db_cache for {symbol}: {e}")
            return None

    def fetch_ohlc_enhanced(self, symbol: str, interval: str = 'day', period: str = '6mo', 
                           validate_data: bool = True) -> Optional[pd.DataFrame]:
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
        try:
            # Use DB cache version
            df = self.fetch_ohlc_with_db_cache(symbol, interval, period)
            
            if df is None or df.empty:
                return None
            
            # Data validation
            if validate_data:
                if not self._validate_ohlc_data(df, symbol):
                    self.logger.warning(f"Data validation failed for {symbol}")
                    return None
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error in enhanced fetch for {symbol}: {e}")
            return None

    def _validate_ohlc_data(self, df: pd.DataFrame, symbol: str) -> bool:
        """
        Validate OHLC data for consistency and quality
        
        Args:
            df: DataFrame to validate
            symbol: Symbol for logging
            
        Returns:
            bool: True if data is valid
        """
        try:
            # Check minimum data points
            min_points = self.config.get('MIN_DATA_POINTS', 10)
            if len(df) < min_points:
                self.logger.warning(f"{symbol}: Insufficient data points ({len(df)})")
                return False
            
            # Check for required columns
            required_columns = ['date', 'open', 'high', 'low', 'close']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.logger.error(f"{symbol}: Missing required columns: {missing_columns}")
                return False
            
            # Check for null values
            null_counts = df[required_columns].isnull().sum()
            if null_counts.any():
                self.logger.warning(f"{symbol}: Found null values: {null_counts.to_dict()}")
                return False
            
            # Check for negative prices
            for col in ['open', 'high', 'low', 'close']:
                if (df[col] <= 0).any():
                    self.logger.error(f"{symbol}: Found negative or zero prices in {col}")
                    return False
            
            # Check OHLC consistency
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
            
            # Check for volume anomalies
            if 'volume' in df.columns:
                if (df['volume'] < 0).any():
                    self.logger.error(f"{symbol}: Found negative volume")
                    return False
            
            self.logger.debug(f"{symbol}: Data validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating data for {symbol}: {e}")
            return False

    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get stock information for a symbol
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dict or None: Stock information
        """
        try:
            self.logger.info(f"Fetching stock info for {symbol}")
            
            # Get Polygon client
            client = self._get_client()
            if not client:
                return None
            
            # Get ticker details
            ticker_details = client.get_ticker_details(symbol)
            
            if not ticker_details:
                self.logger.warning(f"No ticker details returned for {symbol}")
                return None
            
            stock_info = {
                'symbol': symbol,
                'name': getattr(ticker_details, 'name', symbol),
                'sector': getattr(ticker_details, 'sic_description', 'Unknown'),
                'industry': getattr(ticker_details, 'sic_description', 'Unknown'),
                'market_cap': getattr(ticker_details, 'market_cap', None),
                'currency': getattr(ticker_details, 'currency_name', 'USD'),
                'exchange': getattr(ticker_details, 'primary_exchange', 'Unknown'),
                'country': getattr(ticker_details, 'locale', 'Unknown'),
                'description': getattr(ticker_details, 'description', ''),
                'fetched_at': datetime.now().isoformat()
            }
            
            self.logger.info(f"Successfully fetched stock info for {symbol}")
            return stock_info
            
        except Exception as e:
            self.logger.error(f"Error fetching stock info for {symbol}: {e}")
            return None

    def get_real_time_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get real-time price for a symbol
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dict or None: Real-time price data
        """
        try:
            self.logger.info(f"Fetching real-time price for {symbol}")
            
            # Get Polygon client
            client = self._get_client()
            if not client:
                return None
            
            # Get latest trade
            latest_trade = client.get_last_trade(symbol)
            
            if not latest_trade:
                self.logger.warning(f"No real-time data for {symbol}")
                return None
            
            price_data = {
                'symbol': symbol,
                'price': float(latest_trade.price),
                'volume': int(latest_trade.size),
                'timestamp': datetime.now().isoformat(),
                'source': 'polygon'
            }
            
            self.logger.info(f"Successfully fetched real-time price for {symbol}: ${price_data['price']:.2f}")
            return price_data
            
        except Exception as e:
            self.logger.error(f"Error getting real-time price for {symbol}: {e}")
            return None 