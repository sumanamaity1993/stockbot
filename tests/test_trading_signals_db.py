#!/usr/bin/env python3
"""
Test script for trading signals database functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from postgres import init_trading_signals_tables, get_trading_signals_history
from trader.rule_based import main as rule_based_main
import argparse

def test_trading_signals_storage():
    """Test the trading signals storage functionality"""
    print("🧪 Testing Trading Signals Database Storage")
    print("=" * 50)
    
    # Initialize tables
    print("📊 Initializing trading signals tables...")
    init_trading_signals_tables()
    
    # Test classic engine
    print("\n🔧 Testing Classic Engine...")
    try:
        rule_based_main([
            "--engine", "classic",
            "--symbols", "AAPL", "MSFT",
            "--period", "1mo"
        ])
        print("✅ Classic engine test completed")
    except Exception as e:
        print(f"❌ Classic engine test failed: {e}")
    
    # Test multi-source engine
    print("\n🔧 Testing Multi-Source Engine...")
    try:
        rule_based_main([
            "--engine", "multi_source",
            "--symbols", "AAPL", "MSFT",
            "--period", "1mo"
        ])
        print("✅ Multi-source engine test completed")
    except Exception as e:
        print(f"❌ Multi-source engine test failed: {e}")
    
    # Retrieve and display history
    print("\n📊 Retrieving Trading Signals History...")
    try:
        # Get classic engine history
        classic_history = get_trading_signals_history(engine_type='classic', days_back=1)
        print(f"📈 Classic Engine Records: {len(classic_history)}")
        
        # Get multi-source engine history
        multi_history = get_trading_signals_history(engine_type='multi_source', days_back=1)
        print(f"📈 Multi-Source Engine Records: {len(multi_history)}")
        
        # Get overall history
        all_history = get_trading_signals_history(days_back=1)
        print(f"📈 Total Records: {len(all_history)}")
        
        print("✅ Database retrieval test completed")
        
    except Exception as e:
        print(f"❌ Database retrieval test failed: {e}")
    
    print("\n🎉 Trading signals database test completed!")

if __name__ == "__main__":
    test_trading_signals_storage() 