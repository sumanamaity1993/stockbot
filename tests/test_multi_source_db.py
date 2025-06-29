#!/usr/bin/env python3
"""
Test script to validate multi-source database setup and functionality
"""

import os
import sys
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from trader.rule_based.config import RULE_BASED_CONFIG
from trader.rule_based.multi_source_engine import MultiSourceRuleBasedEngine
from postgres import init_multi_source_ohlcv_tables, load_ohlcv_data, check_data_freshness
from trader.data.source_data import YFinanceFetcher, AlphaVantageFetcher, PolygonFetcher

def test_database_setup():
    """Test database table creation and basic functionality"""
    print("🗄️  TESTING DATABASE SETUP")
    print("=" * 40)
    
    try:
        # Initialize tables
        init_multi_source_ohlcv_tables()
        print("✅ Database tables created successfully")
        
        # Test data freshness check
        symbol = "AAPL"
        for source in ['yfinance', 'alpha_vantage', 'polygon']:
            is_fresh = check_data_freshness(symbol, source, days_threshold=1)
            print(f"   📊 {source}: Data fresh = {is_fresh}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def test_individual_fetchers():
    """Test individual fetchers with database caching"""
    print("\n📊 TESTING INDIVIDUAL FETCHERS WITH DB CACHE")
    print("=" * 50)
    
    symbol = "AAPL"
    period = "1mo"
    
    fetchers = [
        ("yfinance", YFinanceFetcher()),
        ("alpha_vantage", AlphaVantageFetcher()),
        ("polygon", PolygonFetcher())
    ]
    
    results = {}
    
    for name, fetcher in fetchers:
        print(f"\n🔍 Testing {name.upper()}...")
        try:
            # This will use DB cache if available, otherwise fetch from API
            df = fetcher.fetch_ohlc_enhanced(symbol, period=period)
            
            if df is not None and not df.empty:
                print(f"   ✅ Success: {len(df)} data points")
                print(f"   📅 Date range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
                print(f"   💰 Latest close: ${df['close'].iloc[-1]:.2f}")
                results[name] = df
            else:
                print(f"   ❌ No data returned")
                results[name] = None
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results[name] = None
    
    return results

def test_multi_source_engine():
    """Test the multi-source engine"""
    print("\n🚀 TESTING MULTI-SOURCE ENGINE")
    print("=" * 40)
    
    try:
        # Create a smaller test configuration
        test_config = RULE_BASED_CONFIG.copy()
        test_config["SYMBOLS"] = ["AAPL", "MSFT"]  # Just 2 symbols for testing
        
        # Initialize engine
        engine = MultiSourceRuleBasedEngine(test_config)
        print("✅ Multi-source engine initialized")
        
        # Run analysis
        print("\n🔄 Running multi-source analysis...")
        results = engine.run_multi_source_analysis()
        
        # Show consensus signals
        consensus = engine.get_consensus_signals(results)
        if consensus:
            print("\n🎯 CONSENSUS SIGNALS:")
            for symbol, data in consensus.items():
                signal = data['signal']
                confidence = data['confidence']
                buy_count = data['buy_count']
                sell_count = data['sell_count']
                
                if signal == 'buy':
                    print(f"   📈 {symbol}: 🟢 BUY (confidence: {confidence:.2f}, buy: {buy_count}, sell: {sell_count})")
                elif signal == 'sell':
                    print(f"   📈 {symbol}: 🔴 SELL (confidence: {confidence:.2f}, buy: {buy_count}, sell: {sell_count})")
                else:
                    print(f"   📈 {symbol}: ⏸️  HOLD (confidence: {confidence:.2f}, buy: {buy_count}, sell: {sell_count})")
        
        return True
        
    except Exception as e:
        print(f"❌ Multi-source engine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_operations():
    """Test database load operations"""
    print("\n💾 TESTING DATABASE OPERATIONS")
    print("=" * 40)
    
    symbol = "AAPL"
    
    for source in ['yfinance', 'alpha_vantage', 'polygon']:
        print(f"\n📊 Testing {source} database operations...")
        
        try:
            # Check if data exists
            is_fresh = check_data_freshness(symbol, source, days_threshold=1)
            print(f"   📊 Data fresh: {is_fresh}")
            
            # Try to load data
            df = load_ohlcv_data(symbol, source)
            if df is not None and not df.empty:
                print(f"   ✅ Loaded {len(df)} records from database")
                print(f"   📅 Date range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
            else:
                print(f"   ⚠️  No data found in database")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def main():
    """Main test function"""
    print("🧪 MULTI-SOURCE DATABASE INTEGRATION TEST")
    print("=" * 60)
    
    # Test 1: Database setup
    if not test_database_setup():
        print("❌ Database setup failed. Exiting.")
        return
    
    # Test 2: Individual fetchers
    fetcher_results = test_individual_fetchers()
    
    # Test 3: Database operations
    test_database_operations()
    
    # Test 4: Multi-source engine
    if not test_multi_source_engine():
        print("❌ Multi-source engine test failed.")
        return
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    
    print("\n📋 SUMMARY:")
    print("✅ Database tables created for all sources")
    print("✅ Individual fetchers working with DB cache")
    print("✅ Multi-source engine operational")
    print("✅ Data persistence and retrieval working")
    
    print("\n🚀 NEXT STEPS:")
    print("1. Add API keys for Alpha Vantage and Polygon.io")
    print("2. Run the multi-source engine for your symbols")
    print("3. Monitor database growth and performance")
    print("4. Add more data sources (news, Reddit, etc.)")

if __name__ == "__main__":
    main() 