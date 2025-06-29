#!/usr/bin/env python3
"""
Demo script for Enhanced Data Fetcher

This script demonstrates how to use the enhanced data fetcher with various features:
- Multiple data sources
- Data validation and quality analysis
- Real-time price fetching
- Caching functionality
- Error handling
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from datetime import datetime
from trader.data.source_data import EnhancedDataFetcher
from trader.data.source_data import DataQualityAnalyzer
from trader.data.source_data import SOURCE_DATA_FETCHER_CONFIG
from logger import get_logger

def main():
    """Main demo function"""
    logger = get_logger(__name__, log_file_prefix="demo_enhanced_fetcher")
    
    print("🚀 ENHANCED DATA FETCHER DEMO")
    print("=" * 50)
    
    # Initialize enhanced fetcher
    print("📊 Initializing Enhanced Data Fetcher...")
    fetcher = EnhancedDataFetcher(SOURCE_DATA_FETCHER_CONFIG)
    
    # Initialize quality analyzer
    analyzer = DataQualityAnalyzer()
    
    # Demo 1: Basic data fetching
    print("\n1️⃣ BASIC DATA FETCHING")
    print("-" * 30)
    
    symbols = ["AAPL", "MSFT", "GOOGL"]
    for symbol in symbols:
        print(f"\n📈 Fetching data for {symbol}...")
        df = fetcher.fetch_ohlc(symbol, period='1mo')
        
        if df is not None and not df.empty:
            print(f"   ✅ Success: {len(df)} data points")
            print(f"   📅 Date range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
            print(f"   💰 Latest close: ${df['close'].iloc[-1]:.2f}")
            print(f"   📊 Price range: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
        else:
            print(f"   ❌ Failed to fetch data for {symbol}")
    
    # Demo 2: Data quality analysis
    print("\n2️⃣ DATA QUALITY ANALYSIS")
    print("-" * 30)
    
    symbol = "AAPL"
    print(f"\n🔍 Analyzing data quality for {symbol}...")
    
    df = fetcher.fetch_ohlc(symbol, period='3mo')
    if df is not None and not df.empty:
        analysis = analyzer.analyze_data_quality(df, symbol)
        
        print(f"   📊 Quality Score: {analysis['quality_score']:.2f}/1.00")
        
        # Handle completeness score
        if 'completeness' in analysis and 'completeness_score' in analysis['completeness']:
            print(f"   ✅ Completeness: {analysis['completeness']['completeness_score']:.2f}")
        else:
            print(f"   ✅ Completeness: N/A (error in analysis)")
        
        # Handle consistency score
        if 'consistency' in analysis and 'consistency_score' in analysis['consistency']:
            print(f"   🔄 Consistency: {analysis['consistency']['consistency_score']:.2f}")
        else:
            print(f"   🔄 Consistency: N/A (error in analysis)")
        
        # Show anomalies
        total_anomalies = 0
        if 'anomalies' in analysis:
            for anomaly_data in analysis['anomalies'].values():
                if isinstance(anomaly_data, dict) and 'indices' in anomaly_data:
                    total_anomalies += len(anomaly_data['indices'])
        print(f"   ⚠️  Anomalies: {total_anomalies}")
        
        # Show recommendations
        if analysis.get('recommendations'):
            print("   📋 Recommendations:")
            for rec in analysis['recommendations'][:3]:  # Show first 3
                print(f"      • {rec}")
    else:
        print(f"   ❌ No data available for analysis")
    
    # Demo 3: Real-time price fetching
    print("\n3️⃣ REAL-TIME PRICE FETCHING")
    print("-" * 30)
    
    for symbol in ["AAPL", "MSFT"]:
        print(f"\n⏰ Getting real-time price for {symbol}...")
        real_time = fetcher.get_real_time_price(symbol)
        
        if real_time:
            change_emoji = "🟢" if real_time['change'] >= 0 else "🔴"
            print(f"   {change_emoji} Current Price: ${real_time['price']:.2f}")
            print(f"   📈 Change: {real_time['change']:+.2f} ({real_time['change_percent']:+.2f}%)")
            print(f"   📊 Volume: {real_time['volume']:,}")
        else:
            print(f"   ❌ Real-time price not available")
    
    # Demo 4: Market status
    print("\n4️⃣ MARKET STATUS")
    print("-" * 30)
    
    market_status = fetcher.get_market_status()
    status_emoji = "🟢" if market_status['is_open'] else "🔴"
    print(f"\n{status_emoji} Market Status: {'OPEN' if market_status['is_open'] else 'CLOSED'}")
    print(f"   🕐 Current Time: {market_status['current_time'].strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   📅 Weekend: {'Yes' if market_status['is_weekend'] else 'No'}")
    print(f"   ⏰ Market Hours: {'Yes' if market_status['is_market_hours'] else 'No'}")
    
    # Demo 5: Caching functionality
    print("\n5️⃣ CACHING FUNCTIONALITY")
    print("-" * 30)
    
    cache_stats = fetcher.get_cache_stats()
    print(f"\n💾 Cache Statistics:")
    print(f"   Enabled: {cache_stats['cache_enabled']}")
    print(f"   Size: {cache_stats['cache_size']} entries")
    print(f"   Duration: {cache_stats['cache_duration']} seconds")
    
    # Test caching by fetching the same data twice
    symbol = "AAPL"
    print(f"\n🔄 Testing cache with {symbol}...")
    
    # First fetch (should hit API)
    start_time = datetime.now()
    df1 = fetcher.fetch_ohlc(symbol, period='1mo')
    first_fetch_time = (datetime.now() - start_time).total_seconds()
    
    # Second fetch (should hit cache)
    start_time = datetime.now()
    df2 = fetcher.fetch_ohlc(symbol, period='1mo')
    second_fetch_time = (datetime.now() - start_time).total_seconds()
    
    print(f"   First fetch: {first_fetch_time:.3f}s")
    print(f"   Second fetch: {second_fetch_time:.3f}s")
    print(f"   Speed improvement: {first_fetch_time/second_fetch_time:.1f}x faster")
    
    # Demo 6: Error handling
    print("\n6️⃣ ERROR HANDLING")
    print("-" * 30)
    
    invalid_symbols = ["INVALID_SYMBOL", "NONEXISTENT", ""]
    for symbol in invalid_symbols:
        print(f"\n🚨 Testing invalid symbol: '{symbol}'")
        try:
            df = fetcher.fetch_ohlc(symbol)
            if df is None or df.empty:
                print(f"   ✅ Properly handled invalid symbol")
            else:
                print(f"   ⚠️ Unexpected data returned")
        except Exception as e:
            print(f"   ✅ Exception caught: {str(e)[:50]}...")
    
    # Demo 7: Multiple data sources
    print("\n7️⃣ MULTIPLE DATA SOURCES")
    print("-" * 30)
    
    symbol = "AAPL"
    sources = ['yfinance', 'alpha_vantage', 'polygon']
    
    for source in sources:
        print(f"\n🔄 Testing {source}...")
        try:
            df = fetcher.fetch_ohlc(symbol, sources=[source])
            if df is not None and not df.empty:
                print(f"   ✅ {source}: {len(df)} data points")
            else:
                print(f"   ⚠️ {source}: No data available")
        except Exception as e:
            print(f"   ❌ {source}: {str(e)[:50]}...")
    
    # Demo 8: Data comparison
    print("\n8️⃣ DATA COMPARISON")
    print("-" * 30)
    
    symbol = "AAPL"
    print(f"\n📊 Comparing data sources for {symbol}...")
    
    # Fetch from different sources
    yf_data = fetcher.fetch_ohlc(symbol, sources=['yfinance'])
    av_data = fetcher.fetch_ohlc(symbol, sources=['alpha_vantage'])
    
    if yf_data is not None and not yf_data.empty:
        print(f"   📈 yfinance: {len(yf_data)} points, latest: ${yf_data['close'].iloc[-1]:.2f}")
    
    if av_data is not None and not av_data.empty:
        print(f"   📈 Alpha Vantage: {len(av_data)} points, latest: ${av_data['close'].iloc[-1]:.2f}")
    
    # Summary
    print("\n" + "=" * 50)
    print("🎉 ENHANCED DATA FETCHER DEMO COMPLETED")
    print("=" * 50)
    print("\nKey Features Demonstrated:")
    print("✅ Multiple data sources with fallback")
    print("✅ Data validation and quality analysis")
    print("✅ Real-time price fetching")
    print("✅ Intelligent caching")
    print("✅ Robust error handling")
    print("✅ Market status monitoring")
    print("\nNext Steps:")
    print("1. Add API keys to .env file for Alpha Vantage and Polygon.io")
    print("2. Run the test script: python trader/data/test_enhanced_fetcher.py")
    print("3. Integrate with your trading strategies")
    print("4. Set up scheduled data collection")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc() 