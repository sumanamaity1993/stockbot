"""
Source Manager
Centralized manager for all data source fetchers.
Provides a unified interface for accessing different data sources.
"""

import os
import sys
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import pandas as pd

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from logger import get_logger
from .source_data.alpha_vantage_fetcher import AlphaVantageFetcher
from .source_data.yfinance_fetcher import YFinanceFetcher
from .source_data.polygon_fetcher import PolygonFetcher
from .source_data.fyers_api_fetcher import FyersAPIFetcher
from .source_data.kite_fetcher import KiteFetcher
from .source_data.enhanced_fetcher import EnhancedDataFetcher
from .source_data.data_quality import DataQualityAnalyzer
from .source_data.config import SOURCE_DATA_FETCHER_CONFIG
from postgres import store_ohlcv_data, load_ohlcv_data, check_data_freshness


class SourceManager:
    """
    Centralized manager for all data source fetchers.
    Provides a unified interface for accessing different data sources.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the source manager
        
        Args:
            config: Configuration dictionary. If None, uses default config.
        """
        self.config = config or SOURCE_DATA_FETCHER_CONFIG
        self.logger = get_logger(__name__, log_file_prefix="source_manager")
        
        # Initialize individual fetchers
        self._fetchers = {}
        self._enhanced_fetcher = None
        self._data_analyzer = None
        
        # Track source availability and performance (initialize before calling _initialize_fetchers)
        self._source_stats = {}
        self._source_availability = {}
        
        # Initialize fetchers based on configuration
        self._initialize_fetchers()
        
        self.logger.info(f"Source Manager initialized with {len(self._fetchers)} fetchers")
    
    def _initialize_fetchers(self):
        """Initialize all available fetchers"""
        try:
            # Initialize enhanced fetcher (main interface)
            self._enhanced_fetcher = EnhancedDataFetcher(self.config)
            self._data_analyzer = DataQualityAnalyzer(self.config)
            
            # Initialize individual fetchers
            available_sources = self.config.get('DATA_SOURCES', [])
            
            if 'alpha_vantage' in available_sources:
                self._fetchers['alpha_vantage'] = AlphaVantageFetcher()
                self.logger.debug("✅ Alpha Vantage fetcher initialized")
            
            if 'yfinance' in available_sources:
                self._fetchers['yfinance'] = YFinanceFetcher()
                self.logger.debug("✅ YFinance fetcher initialized")
            
            if 'polygon' in available_sources:
                self._fetchers['polygon'] = PolygonFetcher()
                self.logger.debug("✅ Polygon fetcher initialized")
            
            if 'fyers' in available_sources:
                self._fetchers['fyers'] = FyersAPIFetcher()
                self.logger.debug("✅ Fyers API fetcher initialized")
            
            if 'kite' in available_sources:
                self._fetchers['kite'] = KiteFetcher()
                self.logger.debug("✅ Kite fetcher initialized")
            
            # Check availability of each source
            self._check_source_availability()
            
        except Exception as e:
            self.logger.error(f"Error initializing fetchers: {e}")
    
    def _check_source_availability(self):
        """Check availability of each data source"""
        for source_name, fetcher in self._fetchers.items():
            try:
                # Simple availability check - try to get client/connection
                if hasattr(fetcher, 'get_alpha_vantage_client'):
                    client = fetcher.get_alpha_vantage_client()
                    self._source_availability[source_name] = client is not None
                elif hasattr(fetcher, 'get_yfinance_client'):
                    client = fetcher.get_yfinance_client()
                    self._source_availability[source_name] = client is not None
                elif hasattr(fetcher, 'get_polygon_client'):
                    client = fetcher.get_polygon_client()
                    self._source_availability[source_name] = client is not None
                else:
                    # For other fetchers, assume available if initialized
                    self._source_availability[source_name] = True
                    
            except Exception as e:
                self.logger.warning(f"Source {source_name} availability check failed: {e}")
                self._source_availability[source_name] = False
        
        available_sources = [s for s, available in self._source_availability.items() if available]
        self.logger.info(f"Available sources: {available_sources}")
    
    def get_available_sources(self) -> List[str]:
        """Get list of available data sources"""
        return [source for source, available in self._source_availability.items() if available]
    
    def get_fetcher(self, source: str):
        """Get a specific fetcher by source name"""
        return self._fetchers.get(source)
    
    def get_enhanced_fetcher(self) -> EnhancedDataFetcher:
        """Get the enhanced fetcher instance"""
        return self._enhanced_fetcher
    
    def get_data_analyzer(self) -> DataQualityAnalyzer:
        """Get the data quality analyzer instance"""
        return self._data_analyzer
    
    def fetch_ohlc(self, symbol: str, interval: str = 'daily', period: str = '6mo', 
                   sources: Optional[List[str]] = None, use_cache: bool = True, 
                   save_to_db: bool = True) -> Optional[Dict[str, Any]]:
        """
        Fetch OHLC data using the enhanced fetcher
        
        Args:
            symbol: Stock symbol
            interval: Data interval
            period: Data period
            sources: List of sources to use. If None, uses all available sources
            use_cache: Whether to use cached data
            save_to_db: Whether to save data to database
            
        Returns:
            Dict with 'data' (DataFrame) and 'source' (str) or None
        """
        if sources is None:
            sources = self.get_available_sources()
        
        try:
            return self._enhanced_fetcher.fetch_ohlc(
                symbol, interval, period, sources, use_cache, save_to_db
            )
        except Exception as e:
            self.logger.error(f"Error fetching OHLC data for {symbol}: {e}")
            return None
    
    def fetch_ohlc_from_source(self, symbol: str, source: str, interval: str = 'daily', 
                              period: str = '6mo') -> Optional[pd.DataFrame]:
        """
        Fetch OHLC data from a specific source
        
        Args:
            symbol: Stock symbol
            source: Data source name
            interval: Data interval
            period: Data period
            
        Returns:
            DataFrame or None
        """
        try:
            fetcher = self.get_fetcher(source)
            if not fetcher:
                self.logger.error(f"Fetcher not available for source: {source}")
                return None
            
            # Use the appropriate method based on the fetcher
            if hasattr(fetcher, 'fetch_ohlc'):
                return fetcher.fetch_ohlc(symbol, interval, period)
            elif hasattr(fetcher, 'fetch_ohlc_with_db_cache'):
                return fetcher.fetch_ohlc_with_db_cache(symbol, interval, period)
            elif hasattr(fetcher, 'fetch_ohlc_enhanced'):
                return fetcher.fetch_ohlc_enhanced(symbol, interval, period)
            else:
                self.logger.error(f"No fetch method found for {source}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error fetching data for {symbol} from {source}: {e}")
            return None
    
    def fetch_ohlc_from_all_sources(self, symbol: str, interval: str = 'daily', 
                                   period: str = '6mo') -> Dict[str, Optional[pd.DataFrame]]:
        """
        Fetch OHLC data from all available sources
        
        Args:
            symbol: Stock symbol
            interval: Data interval
            period: Data period
            
        Returns:
            Dict mapping source names to DataFrames
        """
        results = {}
        available_sources = self.get_available_sources()
        
        for source in available_sources:
            try:
                df = self.fetch_ohlc_from_source(symbol, source, interval, period)
                results[source] = df
                
                if df is not None and not df.empty:
                    self.logger.info(f"✅ {source}: {len(df)} data points for {symbol}")
                else:
                    self.logger.warning(f"❌ {source}: No data for {symbol}")
                    
            except Exception as e:
                self.logger.error(f"❌ {source}: Error fetching {symbol}: {e}")
                results[source] = None
        
        return results
    
    def get_stock_info(self, symbol: str, source: str = 'alpha_vantage') -> Optional[Dict[str, Any]]:
        """
        Get stock information from a specific source
        
        Args:
            symbol: Stock symbol
            source: Data source name
            
        Returns:
            Dict with stock information or None
        """
        try:
            fetcher = self.get_fetcher(source)
            if not fetcher:
                return None
            
            if hasattr(fetcher, 'get_stock_info'):
                return fetcher.get_stock_info(symbol)
            else:
                self.logger.warning(f"get_stock_info not available for {source}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting stock info for {symbol} from {source}: {e}")
            return None
    
    def get_real_time_price(self, symbol: str, source: str = 'alpha_vantage') -> Optional[Dict[str, Any]]:
        """
        Get real-time price from a specific source
        
        Args:
            symbol: Stock symbol
            source: Data source name
            
        Returns:
            Dict with price information or None
        """
        try:
            fetcher = self.get_fetcher(source)
            if not fetcher:
                return None
            
            if hasattr(fetcher, 'get_real_time_price'):
                return fetcher.get_real_time_price(symbol)
            else:
                self.logger.warning(f"get_real_time_price not available for {source}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting real-time price for {symbol} from {source}: {e}")
            return None
    
    def analyze_data_quality(self, df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """
        Analyze data quality using the data analyzer
        
        Args:
            df: DataFrame to analyze
            symbol: Stock symbol for logging
            
        Returns:
            Dict with quality analysis results
        """
        try:
            return self._data_analyzer.analyze_data_quality(df, symbol)
        except Exception as e:
            self.logger.error(f"Error analyzing data quality for {symbol}: {e}")
            return {'quality_score': 0.0, 'issues': [str(e)]}
    
    def compress_and_optimize_data(self, df: pd.DataFrame, symbol: str, source: str) -> pd.DataFrame:
        """
        Compress and optimize data using the enhanced fetcher
        
        Args:
            df: DataFrame to optimize
            symbol: Stock symbol
            source: Data source name
            
        Returns:
            Optimized DataFrame
        """
        try:
            return self._enhanced_fetcher.compress_and_optimize_data(df, symbol, source)
        except Exception as e:
            self.logger.error(f"Error optimizing data for {symbol}: {e}")
            return df
    
    def detect_and_remove_outliers(self, df: pd.DataFrame, symbol: str, method: str = "iqr") -> pd.DataFrame:
        """
        Detect and remove outliers using the enhanced fetcher
        
        Args:
            df: DataFrame to clean
            symbol: Stock symbol
            method: Outlier detection method
            
        Returns:
            Cleaned DataFrame
        """
        try:
            return self._enhanced_fetcher.detect_and_remove_outliers(df, symbol, method)
        except Exception as e:
            self.logger.error(f"Error removing outliers for {symbol}: {e}")
            return df
    
    def predict_and_prefetch_data(self, symbols: List[str], prediction_hours: int = 24) -> Dict[str, Any]:
        """
        Predict and prefetch data using the enhanced fetcher
        
        Args:
            symbols: List of symbols to prefetch
            prediction_hours: Hours to predict ahead
            
        Returns:
            Dict with prefetch results
        """
        try:
            return self._enhanced_fetcher.predict_and_prefetch_data(symbols, prediction_hours)
        except Exception as e:
            self.logger.error(f"Error in predictive prefetch: {e}")
            return {'prefetched_symbols': [], 'error': str(e)}
    
    def get_optimal_concurrency(self, source: str) -> Dict[str, Any]:
        """
        Get optimal concurrency settings for a source
        
        Args:
            source: Data source name
            
        Returns:
            Dict with concurrency settings
        """
        try:
            return self._enhanced_fetcher.get_optimal_concurrency(source)
        except Exception as e:
            self.logger.error(f"Error getting concurrency for {source}: {e}")
            return {'priority': 1, 'max_concurrent': 1, 'delay': 1.0}
    
    def get_adaptive_stats(self) -> Dict[str, Any]:
        """
        Get adaptive statistics from the enhanced fetcher
        
        Returns:
            Dict with adaptive statistics
        """
        try:
            return self._enhanced_fetcher.get_adaptive_stats()
        except Exception as e:
            self.logger.error(f"Error getting adaptive stats: {e}")
            return {}
    
    def get_cache_analytics(self) -> Dict[str, Any]:
        """
        Get cache analytics from the enhanced fetcher
        
        Returns:
            Dict with cache analytics
        """
        try:
            return self._enhanced_fetcher.get_cache_analytics()
        except Exception as e:
            self.logger.error(f"Error getting cache analytics: {e}")
            return {}
    
    def load_from_source_db(self, symbol: str, source: str, days_fresh: int = 1) -> Optional[Dict[str, Any]]:
        """
        Load data from source-specific database
        
        Args:
            symbol: Stock symbol
            source: Data source name
            days_fresh: Maximum age of data in days
            
        Returns:
            Dict with 'data' (DataFrame) and 'source' (str) or None
        """
        try:
            return self._enhanced_fetcher.load_from_source_db(symbol, source, days_fresh)
        except Exception as e:
            self.logger.error(f"Error loading from source DB for {symbol} from {source}: {e}")
            return None
    
    def fetch_ohlc_incremental(self, symbol: str, interval: str = 'daily', period: str = '6mo',
                              sources: Optional[List[str]] = None, use_cache: bool = True,
                              save_to_db: bool = True) -> Optional[Dict[str, Any]]:
        """
        Fetch OHLC data incrementally using the enhanced fetcher
        
        Args:
            symbol: Stock symbol
            interval: Data interval
            period: Data period
            sources: List of sources to use
            use_cache: Whether to use cached data
            save_to_db: Whether to save data to database
            
        Returns:
            Dict with 'data' (DataFrame) and 'source' (str) or None
        """
        if sources is None:
            sources = self.get_available_sources()
        
        try:
            return self._enhanced_fetcher.fetch_ohlc_incremental(
                symbol, interval, period, sources, use_cache, save_to_db
            )
        except Exception as e:
            self.logger.error(f"Error in incremental fetch for {symbol}: {e}")
            return None
    
    def get_source_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about all sources
        
        Returns:
            Dict with source statistics
        """
        stats = {
            'total_sources': len(self._fetchers),
            'available_sources': self.get_available_sources(),
            'source_availability': self._source_availability.copy(),
            'enhanced_fetcher_stats': self.get_adaptive_stats(),
            'cache_stats': self.get_cache_analytics()
        }
        return stats
    
    def validate_source_config(self, source: str) -> bool:
        """
        Validate configuration for a specific source
        
        Args:
            source: Data source name
            
        Returns:
            True if configuration is valid
        """
        try:
            fetcher = self.get_fetcher(source)
            if not fetcher:
                return False
            
            # Check if fetcher has required methods
            required_methods = ['fetch_ohlc']
            for method in required_methods:
                if not hasattr(fetcher, method):
                    self.logger.warning(f"Source {source} missing required method: {method}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating source {source}: {e}")
            return False


# Global instance for easy access
_source_manager = None

def get_source_manager(config: Optional[Dict[str, Any]] = None) -> SourceManager:
    """
    Get the global source manager instance
    
    Args:
        config: Configuration dictionary. Only used for first initialization.
        
    Returns:
        SourceManager instance
    """
    global _source_manager
    if _source_manager is None:
        _source_manager = SourceManager(config)
    return _source_manager
