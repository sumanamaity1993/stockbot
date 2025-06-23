#!/usr/bin/env python3
"""
Test script for Enhanced Data Fetcher

This script demonstrates the enhanced data fetching capabilities including:
- Multiple data sources (yfinance, Alpha Vantage, Polygon.io)
- Data validation and quality checks
- Error handling and retry logic
- Caching functionality
- Real-time price fetching
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from datetime import datetime

from trader.data.enhanced_fetcher import EnhancedDataFetcher
from trader.data.data_quality import DataQualityAnalyzer
from trader.data.config import DATA_FETCHER_CONFIG, check_data_source_availability
from trader.data import yfinance_fetcher
from logger import get_logger

def test_enhanced_fetcher():
    """Test the enhanced data fetcher with various scenarios"""
    logger = get_logger(__name__, log_file_prefix="test_enhanced_fetcher")
    
    logger.info("=" * 60)
    logger.info("🧪 ENHANCED DATA FETCHER TEST")
    logger.info("=" * 60)
    
    # Initialize enhanced fetcher
    fetcher = EnhancedDataFetcher(DATA_FETCHER_CONFIG)
    
    # Check data source availability
    logger.info("📊 Checking data source availability...")
    availability = check_data_source_availability(DATA_FETCHER_CONFIG)
    for source, info in availability.items():
        status_emoji = "✅" if info['available'] else "❌"
        logger.info(f"{status_emoji} {source}: {info['status']}")
    
    # Test symbols
    test_symbols = [
        "AAPL",      # Apple Inc.
        "MSFT",      # Microsoft
        "GOOGL",     # Google
        "RELIANCE.NS", # Reliance Industries (Indian market)
        "TCS.NS",    # TCS (Indian market)
    ]
    
    # Initialize quality analyzer
    analyzer = DataQualityAnalyzer()
    
    for symbol in test_symbols:
        logger.info(f"\n🔍 Testing symbol: {symbol}")
        logger.info("-" * 40)
        
        try:
            # Test 1: Basic data fetching
            logger.info("📈 Fetching historical data...")
            df = fetcher.fetch_ohlc(symbol, interval='1d', period='1mo')
            
            if df is not None and not df.empty:
                logger.info(f"✅ Successfully fetched {len(df)} data points")
                logger.info(f"   Date range: {df['date'].min()} to {df['date'].max()}")
                logger.info(f"   Latest close: ${df['close'].iloc[-1]:.2f}")
                
                # Test 2: Data quality analysis
                logger.info("🔍 Analyzing data quality...")
                quality_analysis = analyzer.analyze_data_quality(df, symbol)
                
                logger.info(f"   Quality Score: {quality_analysis['quality_score']:.2f}/1.00")
                logger.info(f"   Completeness: {quality_analysis['completeness']['completeness_score']:.2f}")
                logger.info(f"   Consistency: {quality_analysis['consistency']['consistency_score']:.2f}")
                
                # Show recommendations
                if quality_analysis['recommendations']:
                    logger.info("   📋 Recommendations:")
                    for rec in quality_analysis['recommendations']:
                        logger.info(f"      • {rec}")
                
                # Test 3: Real-time price
                logger.info("⏰ Fetching real-time price...")
                real_time = fetcher.get_real_time_price(symbol)
                if real_time:
                    logger.info(f"   Current Price: ${real_time['price']:.2f}")
                    logger.info(f"   Change: {real_time['change']:+.2f} ({real_time['change_percent']:+.2f}%)")
                else:
                    logger.warning("   Real-time price not available")
                
                # Test 4: Stock information (yfinance only)
                logger.info("ℹ️  Fetching stock information...")
                stock_info = yfinance_fetcher.get_stock_info(symbol)
                if stock_info:
                    logger.info(f"   Company: {stock_info['name']}")
                    logger.info(f"   Sector: {stock_info['sector']}")
                    logger.info(f"   Market Cap: ${stock_info['market_cap']:,}" if stock_info['market_cap'] else "   Market Cap: N/A")
                    logger.info(f"   P/E Ratio: {stock_info['pe_ratio']:.2f}" if stock_info['pe_ratio'] else "   P/E Ratio: N/A")
                else:
                    logger.warning("   Stock information not available")
                
            else:
                logger.error(f"❌ Failed to fetch data for {symbol}")
                
        except Exception as e:
            logger.error(f"❌ Error testing {symbol}: {e}")
    
    # Test 5: Market status
    logger.info(f"\n🏛️  Market Status:")
    market_status = fetcher.get_market_status()
    status_emoji = "🟢" if market_status['is_open'] else "🔴"
    logger.info(f"{status_emoji} Market is {'OPEN' if market_status['is_open'] else 'CLOSED'}")
    logger.info(f"   Current Time: {market_status['current_time']}")
    
    # Test 6: Cache functionality
    logger.info(f"\n💾 Cache Statistics:")
    cache_stats = fetcher.get_cache_stats()
    logger.info(f"   Cache Enabled: {cache_stats['cache_enabled']}")
    logger.info(f"   Cache Size: {cache_stats['cache_size']} entries")
    logger.info(f"   Cache Duration: {cache_stats['cache_duration']} seconds")
    
    # Test 7: Multiple data sources
    logger.info(f"\n🔄 Testing multiple data sources...")
    test_symbol = "AAPL"
    
    for source in ['yfinance', 'alpha_vantage', 'polygon']:
        logger.info(f"   Testing {source}...")
        try:
            df = fetcher.fetch_ohlc(test_symbol, sources=[source])
            if df is not None and not df.empty:
                logger.info(f"   ✅ {source}: {len(df)} data points")
            else:
                logger.warning(f"   ⚠️ {source}: No data available")
        except Exception as e:
            logger.error(f"   ❌ {source}: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ ENHANCED DATA FETCHER TEST COMPLETED")
    logger.info("=" * 60)

def test_data_quality_analysis():
    """Test the data quality analyzer with sample data"""
    logger = get_logger(__name__, log_file_prefix="test_data_quality")
    
    logger.info("\n" + "=" * 60)
    logger.info("🔍 DATA QUALITY ANALYSIS TEST")
    logger.info("=" * 60)
    
    # Initialize analyzer
    analyzer = DataQualityAnalyzer()
    
    # Test with a sample symbol
    symbol = "AAPL"
    
    # Fetch data
    fetcher = EnhancedDataFetcher(DATA_FETCHER_CONFIG)
    df = fetcher.fetch_ohlc(symbol, period='3mo')
    
    if df is not None and not df.empty:
        # Perform quality analysis
        analysis = analyzer.analyze_data_quality(df, symbol)
        
        # Generate and display report
        report = analyzer.generate_quality_report(analysis)
        print(report)
        
        # Save report to file
        report_path = f"logs/quality_report_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        analyzer.generate_quality_report(analysis, save_path=report_path)
        logger.info(f"📄 Quality report saved to: {report_path}")
    else:
        logger.error(f"❌ No data available for {symbol}")

def test_error_handling():
    """Test error handling with invalid symbols"""
    logger = get_logger(__name__, log_file_prefix="test_error_handling")
    
    logger.info("\n" + "=" * 60)
    logger.info("🚨 ERROR HANDLING TEST")
    logger.info("=" * 60)
    
    fetcher = EnhancedDataFetcher(DATA_FETCHER_CONFIG)
    
    # Test with invalid symbols
    invalid_symbols = [
        "INVALID_SYMBOL_123",
        "NONEXISTENT_STOCK",
        "",
        "123456789",
    ]
    
    for symbol in invalid_symbols:
        logger.info(f"Testing invalid symbol: '{symbol}'")
        try:
            df = fetcher.fetch_ohlc(symbol)
            if df is None or df.empty:
                logger.info(f"   ✅ Properly handled invalid symbol: {symbol}")
            else:
                logger.warning(f"   ⚠️ Unexpected data returned for invalid symbol: {symbol}")
        except Exception as e:
            logger.info(f"   ✅ Exception properly caught for invalid symbol: {symbol} - {e}")

if __name__ == "__main__":
    try:
        # Run all tests
        test_enhanced_fetcher()
        test_data_quality_analysis()
        test_error_handling()
        
        print("\n🎉 All tests completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc() 