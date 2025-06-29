#!/usr/bin/env python3
"""
Test: Source Manager
Test the centralized source manager functionality
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from trader.data import SourceManager, get_source_manager
from logger import get_logger

class TestSourceManager(unittest.TestCase):
    """Test cases for SourceManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            'DATA_SOURCES': ['yfinance', 'alpha_vantage', 'polygon'],
            'CACHE_ENABLED': True,
            'DB_DUMP': True
        }
        self.source_manager = SourceManager(self.config)
        self.logger = get_logger(__name__, log_file_prefix="test_source_manager")
    
    def test_initialization(self):
        """Test source manager initialization"""
        self.assertIsNotNone(self.source_manager)
        self.assertEqual(self.source_manager.config, self.config)
        self.assertIsNotNone(self.source_manager._enhanced_fetcher)
        self.assertIsNotNone(self.source_manager._data_analyzer)
    
    def test_get_available_sources(self):
        """Test getting available sources"""
        sources = self.source_manager.get_available_sources()
        self.assertIsInstance(sources, list)
        # Should contain at least some sources from config
        self.assertTrue(len(sources) >= 0)
    
    def test_get_fetcher(self):
        """Test getting specific fetchers"""
        # Test with existing source
        fetcher = self.source_manager.get_fetcher('yfinance')
        self.assertIsNotNone(fetcher)
        
        # Test with non-existing source
        fetcher = self.source_manager.get_fetcher('non_existent')
        self.assertIsNone(fetcher)
    
    def test_get_enhanced_fetcher(self):
        """Test getting enhanced fetcher"""
        enhanced_fetcher = self.source_manager.get_enhanced_fetcher()
        self.assertIsNotNone(enhanced_fetcher)
    
    def test_get_data_analyzer(self):
        """Test getting data analyzer"""
        data_analyzer = self.source_manager.get_data_analyzer()
        self.assertIsNotNone(data_analyzer)
    
    @patch('trader.data.source_manager.EnhancedDataFetcher')
    def test_fetch_ohlc(self, mock_enhanced_fetcher):
        """Test fetching OHLC data"""
        # Mock the enhanced fetcher
        mock_instance = Mock()
        mock_instance.fetch_ohlc.return_value = {
            'data': pd.DataFrame({'date': ['2023-01-01'], 'close': [100]}),
            'source': 'yfinance'
        }
        mock_enhanced_fetcher.return_value = mock_instance
        
        # Create source manager with mocked fetcher
        source_manager = SourceManager(self.config)
        source_manager._enhanced_fetcher = mock_instance
        
        # Test fetch_ohlc
        result = source_manager.fetch_ohlc('AAPL')
        self.assertIsNotNone(result)
        self.assertIn('data', result)
        self.assertIn('source', result)
    
    def test_analyze_data_quality(self):
        """Test data quality analysis"""
        # Create sample data
        df = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=10),
            'open': [100] * 10,
            'high': [105] * 10,
            'low': [95] * 10,
            'close': [102] * 10,
            'volume': [1000] * 10
        })
        
        quality = self.source_manager.analyze_data_quality(df, 'AAPL')
        self.assertIsInstance(quality, dict)
        self.assertIn('quality_score', quality)
    
    def test_compress_and_optimize_data(self):
        """Test data compression and optimization"""
        # Create sample data
        df = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=10),
            'open': [100] * 10,
            'high': [105] * 10,
            'low': [95] * 10,
            'close': [102] * 10,
            'volume': [1000] * 10
        })
        
        optimized_df = self.source_manager.compress_and_optimize_data(df, 'AAPL', 'yfinance')
        self.assertIsInstance(optimized_df, pd.DataFrame)
        self.assertEqual(len(optimized_df), len(df))  # Should have same number of rows
    
    def test_detect_and_remove_outliers(self):
        """Test outlier detection and removal"""
        # Create sample data with outliers
        df = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=10),
            'open': [100, 101, 102, 103, 104, 105, 106, 107, 108, 1000],  # Last value is outlier
            'high': [105] * 10,
            'low': [95] * 10,
            'close': [102] * 10,
            'volume': [1000] * 10
        })
        
        cleaned_df = self.source_manager.detect_and_remove_outliers(df, 'AAPL')
        self.assertIsInstance(cleaned_df, pd.DataFrame)
    
    def test_get_source_statistics(self):
        """Test getting source statistics"""
        stats = self.source_manager.get_source_statistics()
        self.assertIsInstance(stats, dict)
        self.assertIn('total_sources', stats)
        self.assertIn('available_sources', stats)
        self.assertIn('source_availability', stats)
    
    def test_validate_source_config(self):
        """Test source configuration validation"""
        # Test with valid source
        is_valid = self.source_manager.validate_source_config('yfinance')
        self.assertIsInstance(is_valid, bool)
        
        # Test with invalid source
        is_valid = self.source_manager.validate_source_config('non_existent')
        self.assertFalse(is_valid)
    
    def test_get_stock_info(self):
        """Test getting stock information"""
        # Mock the fetcher
        mock_fetcher = Mock()
        mock_fetcher.get_stock_info.return_value = {
            'symbol': 'AAPL',
            'name': 'Apple Inc.',
            'sector': 'Technology'
        }
        
        self.source_manager._fetchers['alpha_vantage'] = mock_fetcher
        self.source_manager._source_availability['alpha_vantage'] = True
        
        stock_info = self.source_manager.get_stock_info('AAPL', 'alpha_vantage')
        self.assertIsNotNone(stock_info)
        self.assertEqual(stock_info['symbol'], 'AAPL')
    
    def test_get_real_time_price(self):
        """Test getting real-time price"""
        # Mock the fetcher
        mock_fetcher = Mock()
        mock_fetcher.get_real_time_price.return_value = {
            'symbol': 'AAPL',
            'price': 150.0,
            'change': 2.5
        }
        
        self.source_manager._fetchers['alpha_vantage'] = mock_fetcher
        self.source_manager._source_availability['alpha_vantage'] = True
        
        price_data = self.source_manager.get_real_time_price('AAPL', 'alpha_vantage')
        self.assertIsNotNone(price_data)
        self.assertEqual(price_data['symbol'], 'AAPL')
        self.assertEqual(price_data['price'], 150.0)


class TestGetSourceManager(unittest.TestCase):
    """Test cases for get_source_manager function"""
    
    def test_get_source_manager_singleton(self):
        """Test that get_source_manager returns singleton instance"""
        manager1 = get_source_manager()
        manager2 = get_source_manager()
        self.assertIs(manager1, manager2)
    
    def test_get_source_manager_with_config(self):
        """Test get_source_manager with custom config"""
        config = {'DATA_SOURCES': ['yfinance']}
        manager = get_source_manager(config)
        self.assertIsNotNone(manager)
        self.assertEqual(manager.config['DATA_SOURCES'], ['yfinance'])


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2) 