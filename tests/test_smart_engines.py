#!/usr/bin/env python3
"""
Test script for SMART engines (Classic and Multi-Source)
Tests all smart features: incremental fetching, adaptive rate limiting, 
predictive prefetching, data compression, outlier removal, etc.
"""

import sys
import os
import time
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from trader.rule_based.engine import RuleBasedEngine
from trader.rule_based.multi_source_engine import MultiSourceRuleBasedEngine
from trader.data.source_data import EnhancedDataFetcher
from trader.data.source_data import DataQualityAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_smart_classic_engine():
    """Test SMART Classic Engine with all features"""
    logger.info("🧪 Testing SMART Classic Engine")
    logger.info("=" * 50)
    
    # Test symbols
    test_symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    try:
        # Create config for classic engine
        config = {
            "SYMBOLS": test_symbols,
            "DATA_PERIOD": "5d",
            "DATA_SOURCE": "enhanced_fetcher",
            "DB_DUMP": True,
            "LOG_TO_FILE": True,
            "LOG_TO_CONSOLE": True,
            "LOG_LEVEL": "INFO",
            "ENGINE_CONFIG": {
                "DATA_SOURCES": ["yfinance", "alpha_vantage", "polygon"],
                "RETRY_ATTEMPTS": 2,
                "CACHE_DURATION": 300
            },
            "STRATEGIES": [
                {
                    "name": "SimpleMovingAverageStrategy",
                    "params": {"short_window": 20, "long_window": 50}
                },
                {
                    "name": "ExponentialMovingAverageStrategy", 
                    "params": {"short_window": 12, "long_window": 26}
                }
            ]
        }
        
        # Initialize engine
        engine = RuleBasedEngine(config)
        
        # Run analysis
        start_time = time.time()
        results = engine.run()
        execution_time = time.time() - start_time
        
        logger.info(f"✅ SMART Classic Engine completed in {execution_time:.2f}s")
        logger.info(f"📊 Results: {len(results)} symbols processed")
        
        # Verify smart features
        enhanced_fetcher = engine.enhanced_fetcher
        
        # Check adaptive stats
        adaptive_stats = enhanced_fetcher.get_adaptive_stats()
        logger.info(f"🧠 Adaptive Stats: {len(adaptive_stats)} sources tracked")
        
        # Check cache analytics
        cache_stats = enhanced_fetcher.get_cache_analytics()
        logger.info(f"🔥 Cache Analytics: {cache_stats.get('total_entries', 0)} entries")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ SMART Classic Engine test failed: {e}")
        return False

def test_smart_multi_source_engine():
    """Test SMART Multi-Source Engine with all features"""
    logger.info("🧪 Testing SMART Multi-Source Engine")
    logger.info("=" * 50)
    
    # Test symbols
    test_symbols = ['AAPL', 'MSFT']
    
    try:
        # Create config for multi-source engine
        config = {
            "SYMBOLS": test_symbols,
            "DATA_PERIOD": "5d",
            "DB_DUMP": True,
            "ENGINE_CONFIG": {
                "DATA_SOURCES": ["yfinance", "alpha_vantage"],
                "RETRY_ATTEMPTS": 2,
                "CACHE_DURATION": 300
            },
            "STRATEGIES": [
                {
                    "name": "SimpleMovingAverageStrategy",
                    "params": {"short_window": 20, "long_window": 50}
                },
                {
                    "name": "ExponentialMovingAverageStrategy", 
                    "params": {"short_window": 12, "long_window": 26}
                }
            ]
        }
        
        # Initialize engine
        engine = MultiSourceRuleBasedEngine(config)
        
        # Run analysis
        start_time = time.time()
        results = engine.run_multi_source_analysis()
        execution_time = time.time() - start_time
        
        logger.info(f"✅ SMART Multi-Source Engine completed in {execution_time:.2f}s")
        logger.info(f"📊 Results: {len(results)} symbols processed")
        
        # Verify smart features
        enhanced_fetcher = engine.enhanced_fetcher
        
        # Check adaptive stats
        adaptive_stats = enhanced_fetcher.get_adaptive_stats()
        logger.info(f"🧠 Adaptive Stats: {len(adaptive_stats)} sources tracked")
        
        # Check cache analytics
        cache_stats = enhanced_fetcher.get_cache_analytics()
        logger.info(f"🔥 Cache Analytics: {cache_stats.get('total_entries', 0)} entries")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ SMART Multi-Source Engine test failed: {e}")
        return False

def test_enhanced_fetcher_smart_features():
    """Test individual smart features of Enhanced Fetcher"""
    logger.info("🧪 Testing Enhanced Fetcher Smart Features")
    logger.info("=" * 50)
    
    try:
        fetcher = EnhancedDataFetcher()
        
        # Test predictive prefetching
        logger.info("🧠 Testing Predictive Prefetching...")
        prefetch_results = fetcher.predict_and_prefetch_data(['AAPL', 'MSFT'], prediction_hours=24)
        logger.info(f"✅ Predictive Prefetch: {len(prefetch_results.get('prefetched_symbols', []))} symbols")
        
        # Test data compression
        logger.info("🗜️ Testing Data Compression...")
        test_result = fetcher.fetch_ohlc_incremental('AAPL', 'yfinance')
        if test_result is not None and 'data' in test_result:
            test_data = test_result['data']
            if test_data is not None and not test_data.empty:
                compressed_data = fetcher.compress_and_optimize_data(test_data, 'AAPL', 'yfinance')
                original_size = len(test_data)
                compressed_size = len(compressed_data)
                compression_ratio = (original_size - compressed_size) / original_size * 100
                logger.info(f"✅ Data Compression: {compression_ratio:.1f}% reduction")
        
        # Test outlier removal
        logger.info("🔍 Testing Outlier Removal...")
        if test_result is not None and 'data' in test_result:
            test_data = test_result['data']
            if test_data is not None and not test_data.empty:
                clean_data = fetcher.detect_and_remove_outliers(test_data, 'AAPL', method="iqr")
                outliers_removed = len(test_data) - len(clean_data)
                logger.info(f"✅ Outlier Removal: {outliers_removed} outliers removed")
        
        # Test optimal concurrency
        logger.info("⚡ Testing Optimal Concurrency...")
        for source in ['yfinance', 'alpha_vantage', 'polygon']:
            concurrency = fetcher.get_optimal_concurrency(source)
            logger.info(f"✅ {source} Concurrency: {concurrency['max_concurrent']} max, {concurrency['priority']} priority")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Enhanced Fetcher Smart Features test failed: {e}")
        return False

def main():
    """Run all SMART engine tests"""
    logger.info("🚀 Starting SMART Engine Tests")
    logger.info("=" * 60)
    
    tests = [
        ("Enhanced Fetcher Smart Features", test_enhanced_fetcher_smart_features),
        ("SMART Classic Engine", test_smart_classic_engine),
        ("SMART Multi-Source Engine", test_smart_multi_source_engine),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running: {test_name}")
        try:
            if test_func():
                passed += 1
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"📊 TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All SMART engine tests passed!")
        return True
    else:
        logger.error("❌ Some tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 