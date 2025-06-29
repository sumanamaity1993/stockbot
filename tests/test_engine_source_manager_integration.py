#!/usr/bin/env python3
"""
Test: Engine Source Manager Integration
Test that both engines are properly using the source manager
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from trader.rule_based.engine import RuleBasedEngine
from trader.rule_based.multi_source_engine import MultiSourceRuleBasedEngine
from trader.data import get_source_manager
from logger import get_logger

class TestEngineSourceManagerIntegration(unittest.TestCase):
    """Test cases for engine integration with source manager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            "SYMBOLS": ["AAPL", "MSFT"],
            "DATA_SOURCE": "yfinance",
            "DB_DUMP": True,
            "DATA_PERIOD": "6mo",
            "LOG_TO_FILE": False,
            "LOG_TO_CONSOLE": True,
            "LOG_LEVEL": "INFO",
            "ENGINE_CONFIG": {
                "DATA_SOURCES": ["yfinance", "alpha_vantage", "polygon"]
            },
            "STRATEGIES": [
                {
                    "name": "SimpleMovingAverageStrategy",
                    "params": {"short_window": 10, "long_window": 20}
                }
            ]
        }
        self.logger = get_logger(__name__, log_file_prefix="test_engine_integration")
    
    def test_rule_based_engine_uses_source_manager(self):
        """Test that rule-based engine uses source manager"""
        with patch('trader.data.get_source_manager') as mock_get_source_manager:
            # Mock the source manager
            mock_source_manager = Mock()
            mock_get_source_manager.return_value = mock_source_manager
            
            # Mock the fetch_ohlc method
            mock_source_manager.fetch_ohlc.return_value = {
                'data': pd.DataFrame({
                    'date': pd.date_range('2023-01-01', periods=10),
                    'open': [100] * 10,
                    'high': [105] * 10,
                    'low': [95] * 10,
                    'close': [102] * 10,
                    'volume': [1000] * 10
                }),
                'source': 'yfinance'
            }
            
            # Mock other source manager methods
            mock_source_manager.analyze_data_quality.return_value = {'quality_score': 0.8}
            mock_source_manager.compress_and_optimize_data.return_value = pd.DataFrame()
            mock_source_manager.detect_and_remove_outliers.return_value = pd.DataFrame()
            mock_source_manager.predict_and_prefetch_data.return_value = {'prefetched_symbols': []}
            mock_source_manager.get_adaptive_stats.return_value = {}
            mock_source_manager.get_cache_analytics.return_value = {}
            mock_source_manager.load_from_source_db.return_value = None
            
            # Create engine
            engine = RuleBasedEngine(self.config)
            
            # Verify source manager was initialized
            self.assertIsNotNone(engine.source_manager)
            mock_get_source_manager.assert_called_once()
            
            # Test get_data method
            df = engine.get_data("AAPL")
            self.assertIsNotNone(df)
            
            # Verify source manager methods were called
            mock_source_manager.fetch_ohlc.assert_called()
            mock_source_manager.analyze_data_quality.assert_called()
    
    def test_multi_source_engine_uses_source_manager(self):
        """Test that multi-source engine uses source manager"""
        with patch('trader.data.get_source_manager') as mock_get_source_manager:
            # Mock the source manager
            mock_source_manager = Mock()
            mock_get_source_manager.return_value = mock_source_manager
            
            # Mock the fetch_ohlc method
            mock_source_manager.fetch_ohlc.return_value = {
                'data': pd.DataFrame({
                    'date': pd.date_range('2023-01-01', periods=10),
                    'open': [100] * 10,
                    'high': [105] * 10,
                    'low': [95] * 10,
                    'close': [102] * 10,
                    'volume': [1000] * 10
                }),
                'source': 'yfinance'
            }
            
            # Mock other source manager methods
            mock_source_manager.analyze_data_quality.return_value = {'quality_score': 0.8}
            mock_source_manager.compress_and_optimize_data.return_value = pd.DataFrame()
            mock_source_manager.detect_and_remove_outliers.return_value = pd.DataFrame()
            mock_source_manager.predict_and_prefetch_data.return_value = {'prefetched_symbols': []}
            mock_source_manager.get_optimal_concurrency.return_value = {'priority': 1}
            mock_source_manager.get_adaptive_stats.return_value = {}
            mock_source_manager.get_cache_analytics.return_value = {}
            mock_source_manager.fetch_ohlc_incremental.return_value = None
            
            # Create engine
            engine = MultiSourceRuleBasedEngine(self.config)
            
            # Verify source manager was initialized
            self.assertIsNotNone(engine.source_manager)
            mock_get_source_manager.assert_called_once()
            
            # Test fetch_data_from_all_sources method
            data_by_source = engine.fetch_data_from_all_sources("AAPL")
            self.assertIsInstance(data_by_source, dict)
            
            # Verify source manager methods were called
            mock_source_manager.fetch_ohlc.assert_called()
    
    def test_engines_dont_import_direct_fetchers(self):
        """Test that engines don't import fetchers directly"""
        # Check rule-based engine imports
        with open('trader/rule_based/engine.py', 'r') as f:
            content = f.read()
            # Should not import individual fetchers
            self.assertNotIn('from trader.data.source_data import EnhancedDataFetcher', content)
            self.assertNotIn('from trader.data.source_data import DataQualityAnalyzer', content)
            # Should import source manager
            self.assertIn('from trader.data import get_source_manager', content)
        
        # Check multi-source engine imports
        with open('trader/rule_based/multi_source_engine.py', 'r') as f:
            content = f.read()
            # Should not import individual fetchers
            self.assertNotIn('from trader.data.source_data import EnhancedDataFetcher', content)
            self.assertNotIn('from trader.data.source_data import DataQualityAnalyzer', content)
            # Should import source manager
            self.assertIn('from trader.data import get_source_manager', content)
    
    def test_source_manager_unified_interface(self):
        """Test that both engines use the same source manager interface"""
        with patch('trader.data.get_source_manager') as mock_get_source_manager:
            # Mock the source manager
            mock_source_manager = Mock()
            mock_get_source_manager.return_value = mock_source_manager
            
            # Mock methods
            mock_source_manager.fetch_ohlc.return_value = {
                'data': pd.DataFrame({'close': [100, 101, 102]}),
                'source': 'yfinance'
            }
            mock_source_manager.analyze_data_quality.return_value = {'quality_score': 0.8}
            mock_source_manager.compress_and_optimize_data.return_value = pd.DataFrame()
            mock_source_manager.detect_and_remove_outliers.return_value = pd.DataFrame()
            mock_source_manager.predict_and_prefetch_data.return_value = {'prefetched_symbols': []}
            mock_source_manager.get_optimal_concurrency.return_value = {'priority': 1}
            mock_source_manager.get_adaptive_stats.return_value = {}
            mock_source_manager.get_cache_analytics.return_value = {}
            mock_source_manager.load_from_source_db.return_value = None
            mock_source_manager.fetch_ohlc_incremental.return_value = None
            
            # Create both engines
            rule_engine = RuleBasedEngine(self.config)
            multi_engine = MultiSourceRuleBasedEngine(self.config)
            
            # Both should use the same source manager instance
            self.assertIs(rule_engine.source_manager, multi_engine.source_manager)
            
            # Both should call the same methods
            rule_engine.get_data("AAPL")
            multi_engine.fetch_data_from_all_sources("AAPL")
            
            # Verify same methods were called
            self.assertTrue(mock_source_manager.fetch_ohlc.called)
            self.assertTrue(mock_source_manager.analyze_data_quality.called)
    
    def test_engine_configuration_consistency(self):
        """Test that both engines handle configuration consistently"""
        config = {
            "SYMBOLS": ["AAPL"],
            "DATA_SOURCE": "yfinance",
            "DB_DUMP": True,
            "DATA_PERIOD": "1mo",
            "LOG_TO_FILE": False,
            "LOG_TO_CONSOLE": True,
            "LOG_LEVEL": "INFO",
            "ENGINE_CONFIG": {
                "DATA_SOURCES": ["yfinance", "alpha_vantage"]
            },
            "STRATEGIES": []
        }
        
        with patch('trader.data.get_source_manager') as mock_get_source_manager:
            mock_source_manager = Mock()
            mock_get_source_manager.return_value = mock_source_manager
            
            # Mock all necessary methods
            mock_source_manager.fetch_ohlc.return_value = {
                'data': pd.DataFrame({'close': [100]}),
                'source': 'yfinance'
            }
            mock_source_manager.analyze_data_quality.return_value = {'quality_score': 0.8}
            mock_source_manager.compress_and_optimize_data.return_value = pd.DataFrame()
            mock_source_manager.detect_and_remove_outliers.return_value = pd.DataFrame()
            mock_source_manager.predict_and_prefetch_data.return_value = {'prefetched_symbols': []}
            mock_source_manager.get_optimal_concurrency.return_value = {'priority': 1}
            mock_source_manager.get_adaptive_stats.return_value = {}
            mock_source_manager.get_cache_analytics.return_value = {}
            mock_source_manager.load_from_source_db.return_value = None
            mock_source_manager.fetch_ohlc_incremental.return_value = None
            
            # Both engines should accept the same config structure
            rule_engine = RuleBasedEngine(config)
            multi_engine = MultiSourceRuleBasedEngine(config)
            
            # Both should have the same configuration
            self.assertEqual(rule_engine.symbols, multi_engine.symbols)
            self.assertEqual(rule_engine.data_period, multi_engine.data_period)
            self.assertEqual(rule_engine.db_dump, multi_engine.db_dump)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2) 