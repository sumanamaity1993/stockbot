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

class FyersAPIFetcher:
    """
    Fyers API data fetcher class for retrieving stock market data
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Fyers API fetcher
        
        Args:
            config: Configuration dictionary (optional)
        """
        self.config = config or {}
        self.logger = get_logger(__name__, log_file_prefix="fyers_api_fetcher")
        self._client = None
        
    def _get_client(self):
        """Get Fyers client with API key and access token (placeholder)"""
        if self._client is not None:
            return self._client
            
        # TODO: Replace with actual Fyers API client initialization
        api_key = os.getenv('FYERS_API_KEY')
        api_secret = os.getenv('FYERS_API_SECRET')
        access_token = os.getenv('FYERS_ACCESS_TOKEN')
        
        if not (api_key and api_secret and access_token):
            self.logger.error("FYERS_API_KEY, FYERS_API_SECRET, or FYERS_ACCESS_TOKEN not found")
            return None
            
        self._client = {
            'api_key': api_key, 
            'api_secret': api_secret, 
            'access_token': access_token
        }
        return self._client

    def fetch_ohlc(self, symbol: str, interval: str = '1d', period: str = '6mo') -> Optional[pd.DataFrame]:
        """
        Fetch OHLC data for a symbol using Fyers API (placeholder).
        Returns a pandas DataFrame with columns: ['date', 'open', 'high', 'low', 'close', 'volume']
        
        Args:
            symbol: Stock symbol
            interval: Data interval (e.g., '1d', '1h')
            period: Data period (e.g., '6mo', '1y')
            
        Returns:
            pandas DataFrame or None: OHLCV data
        """
        try:
            self.logger.info(f"Fetching data for {symbol} (interval: {interval}, period: {period})")
            
            client = self._get_client()
            if not client:
                self.logger.error("Fyers client not available. Check API key, secret, and access token.")
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
                start_date = end_date - timedelta(days=30)
                
            # TODO: Replace with actual Fyers API call
            self.logger.info(f"[MOCK] Fetching OHLCV for {symbol} from {start_date.date()} to {end_date.date()} (interval: {interval})")
            
            # Return empty DataFrame as placeholder
            df = pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume'])
            return df
            
        except Exception as e:
            self.logger.error(f"Error fetching data for {symbol}: {e}")
            return None

    def fetch_ohlc_with_db_cache(self, symbol: str, interval: str = '1d', period: str = '6mo', 
                                force_fetch: bool = False) -> Optional[pd.DataFrame]:
        """
        Fetch OHLC data with database caching for Fyers.
        
        Args:
            symbol: Stock symbol
            interval: Data interval
            period: Data period
            force_fetch: Force fetch from API even if data exists in DB
            
        Returns:
            pandas DataFrame or None: OHLCV data
        """
        try:
            if not force_fetch:
                days_threshold = self.config.get('CACHE_DURATION', 1)
                if check_data_freshness(symbol, 'fyers', days_threshold=days_threshold):
                    self.logger.info(f"Using cached data for {symbol} from database")
                    df = load_ohlcv_data(symbol, 'fyers')
                    if df is not None and not df.empty:
                        return df
                        
            self.logger.info(f"Fetching fresh data for {symbol} from Fyers API")
            df = self.fetch_ohlc(symbol, interval, period)
            
            if df is not None and not df.empty:
                self.logger.info(f"Storing {len(df)} records for {symbol} in database")
                store_ohlcv_data(df, 'fyers', symbol)
                
            return df
            
        except Exception as e:
            self.logger.error(f"Error in fetch_ohlc_with_db_cache for {symbol}: {e}")
            return None

    def fetch_ohlc_enhanced(self, symbol: str, interval: str = '1d', period: str = '6mo', 
                           validate_data: bool = True) -> Optional[pd.DataFrame]:
        """
        Enhanced version of fetch_ohlc with data validation and quality checks for Fyers.
        
        Args:
            symbol: Stock symbol
            interval: Data interval
            period: Data period
            validate_data: Whether to perform data validation
            
        Returns:
            pandas DataFrame or None: OHLCV data
        """
        try:
            df = self.fetch_ohlc_with_db_cache(symbol, interval, period)
            
            if df is None or df.empty:
                return None
                
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
        Validate OHLC data for consistency and quality (same as other fetchers)
        
        Args:
            df: DataFrame to validate
            symbol: Symbol for logging
            
        Returns:
            bool: True if data is valid
        """
        try:
            min_points = self.config.get('MIN_DATA_POINTS', 10)
            if len(df) < min_points:
                self.logger.warning(f"{symbol}: Insufficient data points ({len(df)})")
                return False
                
            required_columns = ['date', 'open', 'high', 'low', 'close']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.logger.error(f"{symbol}: Missing required columns: {missing_columns}")
                return False
                
            null_counts = df[required_columns].isnull().sum()
            if null_counts.any():
                self.logger.warning(f"{symbol}: Found null values: {null_counts.to_dict()}")
                return False
                
            for col in ['open', 'high', 'low', 'close']:
                if (df[col] <= 0).any():
                    self.logger.error(f"{symbol}: Found negative or zero prices in {col}")
                    return False
                    
            self.logger.debug(f"{symbol}: Data validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating data for {symbol}: {e}")
            return False

    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get stock information for a symbol (placeholder)
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dict or None: Stock information
        """
        try:
            self.logger.info(f"Fetching stock info for {symbol}")
            
            # TODO: Implement actual Fyers API call for stock info
            self.logger.info(f"[MOCK] Fetching stock info for {symbol}")
            
            stock_info = {
                'symbol': symbol,
                'name': symbol,
                'sector': 'Unknown',
                'industry': 'Unknown',
                'currency': 'INR',
                'exchange': 'NSE',
                'country': 'India',
                'fetched_at': datetime.now().isoformat(),
                'source': 'fyers'
            }
            
            return stock_info
            
        except Exception as e:
            self.logger.error(f"Error fetching stock info for {symbol}: {e}")
            return None

    def get_real_time_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get real-time price for a symbol (placeholder)
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dict or None: Real-time price data
        """
        try:
            self.logger.info(f"Fetching real-time price for {symbol}")
            
            # TODO: Implement actual Fyers API call for real-time price
            self.logger.info(f"[MOCK] Fetching real-time price for {symbol}")
            
            price_data = {
                'symbol': symbol,
                'price': 0.0,
                'volume': 0,
                'timestamp': datetime.now().isoformat(),
                'source': 'fyers'
            }
            
            return price_data
            
        except Exception as e:
            self.logger.error(f"Error getting real-time price for {symbol}: {e}")
            return None 