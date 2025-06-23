#!/usr/bin/env python3
"""
Test script to verify Alpha Vantage API key setup
"""

import os
import sys
from dotenv import load_dotenv

# Add the project root to the path
sys.path.append(os.path.dirname(__file__))

from trader.data.enhanced_fetcher import EnhancedDataFetcher
from trader.data.config import DATA_FETCHER_CONFIG

def test_alpha_vantage():
    """Test Alpha Vantage API key setup"""
    print("🔑 TESTING ALPHA VANTAGE API KEY")
    print("=" * 40)
    
    # Load environment variables
    load_dotenv()
    
    # Check if API key is set
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        print("❌ ALPHA_VANTAGE_API_KEY not found in .env file")
        print("💡 Please add: ALPHA_VANTAGE_API_KEY=your_api_key_here")
        return False
    
    if api_key == "your_api_key_here":
        print("❌ Please replace 'your_api_key_here' with your actual API key")
        return False
    
    print(f"✅ API Key found: {api_key[:8]}...{api_key[-4:]}")
    
    # Update config with API key
    config = DATA_FETCHER_CONFIG.copy()
    config['ALPHA_VANTAGE_API_KEY'] = api_key
    
    # Initialize enhanced fetcher
    print("\n🔄 Initializing Enhanced Data Fetcher...")
    fetcher = EnhancedDataFetcher(config)
    
    # Test with Alpha Vantage only
    print("\n📊 Testing Alpha Vantage data source...")
    try:
        df = fetcher.fetch_ohlc('AAPL', sources=['alpha_vantage'], period='1mo')
        
        if df is not None and not df.empty:
            print(f"✅ Success! Fetched {len(df)} data points from Alpha Vantage")
            print(f"   📅 Date range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
            print(f"   💰 Latest close: ${df['close'].iloc[-1]:.2f}")
            print(f"   📊 Price range: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
            return True
        else:
            print("❌ No data returned from Alpha Vantage")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Alpha Vantage: {e}")
        return False

def show_usage_info():
    """Show information about Alpha Vantage usage"""
    print("\n📋 ALPHA VANTAGE USAGE INFO")
    print("=" * 30)
    print("🎯 Free Tier Limits:")
    print("   • 500 API calls per day")
    print("   • 5 API calls per minute")
    print("   • Real-time and historical data")
    print("   • US stocks, forex, crypto")
    
    print("\n💡 Tips:")
    print("   • Your bot will use Alpha Vantage as backup to yfinance")
    print("   • Cache is enabled to reduce API calls")
    print("   • Monitor your usage at: https://www.alphavantage.co/account")
    
    print("\n🔧 Next Steps:")
    print("   1. Run: python demo_enhanced_fetcher.py")
    print("   2. Check that Alpha Vantage appears in data sources")
    print("   3. Monitor API usage in your Alpha Vantage account")

if __name__ == "__main__":
    try:
        success = test_alpha_vantage()
        if success:
            show_usage_info()
        else:
            print("\n❌ Setup incomplete. Please check your API key.")
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc() 