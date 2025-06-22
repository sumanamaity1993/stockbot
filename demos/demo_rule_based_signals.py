#!/usr/bin/env python3
"""
Demo script to showcase the colored signal display feature
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime

from trader.rule_based.config import RULE_BASED_CONFIG
from trader.rule_based.engine import RuleBasedEngine
from trader.rule_based.strategies.simple_moving_average import SimpleMovingAverageStrategy
from trader.rule_based.strategies.exponential_moving_average import ExponentialMovingAverageStrategy
from trader.rule_based.strategies.rsi_strategy import RSIStrategy
from trader.rule_based.strategies.macd_strategy import MACDStrategy
from logger import get_logger

def demo_rule_based_signals():
    """Demonstrate the colored signal display feature"""
    logger = get_logger(__name__, log_file_prefix="demo_rule_based_signals")

    print("\n" + "=" * 50)
    print("🎨 COLORED SIGNAL DISPLAY DEMO")
    print("=" * 50)
    print()
    
    # Create a demo configuration with multiple strategies
    demo_config = RULE_BASED_CONFIG.copy()
    demo_config["SYMBOLS"] = [
        "AAPL",      # Apple Inc.
        "MSFT",      # Microsoft
        "GOOGL",     # Google
        "TSLA",      # Tesla
    ]
    demo_config["DATA_PERIOD"] = "3mo"
    
    # Create strategies with different parameters
    strategies = [
        SimpleMovingAverageStrategy(short_window=5, long_window=10),
        ExponentialMovingAverageStrategy(short_window=5, long_window=10),
        RSIStrategy(period=7, oversold=30, overbought=70),
        MACDStrategy(fast_period=8, slow_period=15, signal_period=5)
    ]
    
    print("🔧 Configuration:")
    print(f"  • Symbols: {demo_config['SYMBOLS']}")
    print(f"  • Data period: {demo_config['DATA_PERIOD']}")
    print(f"  • Strategies: {[s.__class__.__name__ for s in strategies]}")
    print()
    
    try:
        print("🔄 Running analysis...")
        print("-" * 30)
        
        # Initialize and run engine
        engine = RuleBasedEngine(demo_config, strategies=strategies)
        results = engine.run()
        
        print()
        print("✅ Demo completed!")
        print()
        print("💡 The colored signals make it easy to:")
        print("  • Quickly identify buy vs sell signals")
        print("  • See which strategies generated signals")
        print("  • Get a summary of signal distribution")
        print("  • Understand market sentiment at a glance")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

def show_example_output():
    """Show an example of what the colored output looks like"""
    print("\n📋 EXAMPLE OUTPUT:")
    print("=" * 30)
    print("2025-06-22 17:07:55,043 - INFO - ============================================================")
    print("2025-06-22 17:07:55,043 - INFO - RULE-BASED TRADING SUMMARY")
    print("2025-06-22 17:07:55,044 - INFO - ============================================================")
    print("2025-06-22 17:07:55,044 - INFO - Total symbols processed: 6")
    print("2025-06-22 17:07:55,045 - INFO - Successful: 6")
    print("2025-06-22 17:07:55,045 - INFO - Failed: 0")
    print("2025-06-22 17:07:55,045 - INFO - Symbols with signals: 3")
    print("2025-06-22 17:07:55,046 - INFO - Symbols with trading signals:")
    print("2025-06-22 17:07:55,047 - INFO -   📈 AAPL: 🟢 BUY (MACDStrategy)")
    print("2025-06-22 17:07:55,047 - INFO -   📈 MSFT: 🔴 SELL (MACDStrategy)")
    print("2025-06-22 17:07:55,048 - INFO -   📈 GOOGL: 🔴 SELL (SimpleMovingAverageStrategy) | 🔴 SELL (ExponentialMovingAverageStrategy)")
    print("2025-06-22 17:07:55,048 - INFO - ")
    print("2025-06-22 17:07:55,049 - INFO - Signal Summary:")
    print("2025-06-22 17:07:55,049 - INFO -   🟢 Buy signals: 1")
    print("2025-06-22 17:07:55,050 - INFO -   🔴 Sell signals: 3")
    print("2025-06-22 17:07:55,050 - INFO -   📊 Total signals: 4")

if __name__ == "__main__":
    try:
        demo_rule_based_signals()
    except KeyboardInterrupt:
        print("\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc() 