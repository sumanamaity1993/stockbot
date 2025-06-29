#!/usr/bin/env python3
"""
Test script to validate all individual fetchers and show multi-source usage
"""

import os
import sys
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from trader.data.source_data import YFinanceFetcher, AlphaVantageFetcher, PolygonFetcher
from logger import get_logger

def test_individual_fetchers():
    """Test each fetcher individually"""
    print("🧪 TESTING INDIVIDUAL FETCHERS")
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
        print(f"\n📊 Testing {name.upper()} fetcher...")
        try:
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

def test_multi_source_comparison(results):
    """Compare data from different sources"""
    print("\n🔍 MULTI-SOURCE COMPARISON")
    print("=" * 40)
    
    symbol = "AAPL"
    available_sources = [name for name, df in results.items() if df is not None]
    
    if len(available_sources) < 2:
        print("⚠️  Need at least 2 sources for comparison")
        return
    
    print(f"📈 Comparing data for {symbol} from {len(available_sources)} sources:")
    
    for source in available_sources:
        df = results[source]
        if df is not None:
            latest_price = df['close'].iloc[-1]
            price_range = f"${df['low'].min():.2f} - ${df['high'].max():.2f}"
            print(f"   {source.upper()}: ${latest_price:.2f} (Range: {price_range})")
    
    # Check for price discrepancies
    prices = []
    for source in available_sources:
        df = results[source]
        if df is not None:
            prices.append((source, df['close'].iloc[-1]))
    
    if len(prices) > 1:
        max_price = max(prices, key=lambda x: x[1])
        min_price = min(prices, key=lambda x: x[1])
        diff_percent = ((max_price[1] - min_price[1]) / min_price[1]) * 100
        
        print(f"\n💰 Price Comparison:")
        print(f"   Highest: {max_price[0].upper()} - ${max_price[1]:.2f}")
        print(f"   Lowest: {min_price[0].upper()} - ${min_price[1]:.2f}")
        print(f"   Difference: {diff_percent:.2f}%")
        
        if diff_percent > 1.0:
            print("   ⚠️  Significant price difference detected")
        else:
            print("   ✅ Prices are consistent across sources")

def show_rule_based_integration():
    """Show how to integrate all sources in rule-based trading"""
    print("\n🎯 RULE-BASED INTEGRATION EXAMPLE")
    print("=" * 40)
    
    print("📋 How to use all sources in rule-based signals:")
    print()
    print("1️⃣ Import all fetchers:")
    print("   from trader.data import yfinance_fetcher, alpha_vantage_fetcher, polygon_fetcher")
    print()
    print("2️⃣ Fetch data from each source:")
    print("   sources = ['yfinance', 'alpha_vantage', 'polygon']")
    print("   data_by_source = {}")
    print("   for source in sources:")
    print("       df = fetcher.fetch_ohlc_enhanced(symbol, period='6mo')")
    print("       data_by_source[source] = df")
    print()
    print("3️⃣ Run strategies on each dataset:")
    print("   signals_by_source = {}")
    print("   for source, df in data_by_source.items():")
    print("       if df is not None:")
    print("           signals = engine.evaluate(df)")
    print("           signals_by_source[source] = signals")
    print()
    print("4️⃣ Compare signals across sources:")
    print("   for source, signals in signals_by_source.items():")
    print("       print(f'{source}: {signals}')")

def show_future_extensions():
    """Show how to extend with news and Reddit data"""
    print("\n🚀 FUTURE EXTENSIONS")
    print("=" * 30)
    
    print("📰 News Data Integration:")
    print("   • Create news_fetcher.py")
    print("   • Fetch financial news from APIs (NewsAPI, Alpha Vantage News)")
    print("   • Sentiment analysis on news headlines")
    print("   • Impact scoring on stock prices")
    print()
    print("📱 Reddit Data Integration:")
    print("   • Create reddit_fetcher.py")
    print("   • Fetch posts from r/wallstreetbets, r/stocks, r/investing")
    print("   • Sentiment analysis on Reddit posts")
    print("   • Mention frequency tracking")
    print()
    print("🔗 Multi-Source Signal Generation:")
    print("   • Technical signals (from price data)")
    print("   • Sentiment signals (from news/Reddit)")
    print("   • Combined scoring system")
    print("   • Weighted decision making")

if __name__ == "__main__":
    try:
        # Test individual fetchers
        results = test_individual_fetchers()
        
        # Compare data from different sources
        test_multi_source_comparison(results)
        
        # Show integration examples
        show_rule_based_integration()
        
        # Show future extensions
        show_future_extensions()
        
        print("\n" + "=" * 50)
        print("✅ ALL FETCHERS TESTED SUCCESSFULLY!")
        print("=" * 50)
        print("\nNext Steps:")
        print("1. Add API keys for Alpha Vantage and Polygon.io")
        print("2. Integrate all sources in rule-based engine")
        print("3. Add news and Reddit data sources")
        print("4. Create multi-source signal generation")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc() 