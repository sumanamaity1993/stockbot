#!/usr/bin/env python3
"""
Demo script showing configurable engine functionality
"""

import os
import sys
import json
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trader.rule_based.config import RULE_BASED_CONFIG
from logger import get_logger

import argparse
from trader.rule_based import main as rule_based_main

def demo_classic_engine():
    """Demo the classic engine"""
    print("\n" + "="*60)
    print("🚦 DEMO: CLASSIC ENGINE")
    print("="*60)
    
    # Configure for classic engine
    config = RULE_BASED_CONFIG.copy()
    config["ENGINE_TYPE"] = "classic"
    config["SYMBOLS"] = ["AAPL", "MSFT"]
    config["DATA_PERIOD"] = "1mo"
    
    print("Configuration:")
    print(f"   Engine Type: {config['ENGINE_TYPE']}")
    print(f"   Symbols: {config['SYMBOLS']}")
    print(f"   Enhanced Fetcher: {config['ENGINE_CONFIG']['USE_ENHANCED_FETCHER']}")
    
    try:
        from trader.rule_based.engine import RuleBasedEngine
        engine = RuleBasedEngine(config=config)
        print("\n✅ Classic engine initialized successfully!")
        
        # Note: Uncomment to actually run the engine
        # engine.run()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def demo_multi_source_engine():
    """Demo the multi-source engine"""
    print("\n" + "="*60)
    print("🚦 DEMO: MULTI-SOURCE ENGINE")
    print("="*60)
    
    # Configure for multi-source engine
    config = RULE_BASED_CONFIG.copy()
    config["ENGINE_TYPE"] = "multi_source"
    config["SYMBOLS"] = ["AAPL", "MSFT"]
    config["DATA_PERIOD"] = "1mo"
    config["ENGINE_CONFIG"]["ENABLE_CONSENSUS"] = True
    
    print("Configuration:")
    print(f"   Engine Type: {config['ENGINE_TYPE']}")
    print(f"   Symbols: {config['SYMBOLS']}")
    print(f"   Data Sources: {config['ENGINE_CONFIG']['DATA_SOURCES']}")
    print(f"   DB Cache: {config['ENGINE_CONFIG']['ENABLE_DB_CACHE']}")
    print(f"   Consensus: {config['ENGINE_CONFIG']['ENABLE_CONSENSUS']}")
    
    try:
        from trader.rule_based.multi_source_engine import MultiSourceRuleBasedEngine
        engine = MultiSourceRuleBasedEngine(config)
        print("\n✅ Multi-source engine initialized successfully!")
        
        # Note: Uncomment to actually run the engine
        # results = engine.run_multi_source_analysis()
        # consensus = engine.get_consensus_signals(results)
        
    except Exception as e:
        print(f"❌ Error: {e}")

def demo_ml_enhanced_engine():
    """Demo the ML-enhanced engine (future)"""
    print("\n" + "="*60)
    print("🚦 DEMO: ML-ENHANCED ENGINE (FUTURE)")
    print("="*60)
    
    # Configure for ML-enhanced engine
    config = RULE_BASED_CONFIG.copy()
    config["ENGINE_TYPE"] = "ml_enhanced"
    config["SYMBOLS"] = ["AAPL", "MSFT"]
    config["ENGINE_CONFIG"]["ML_ENABLED"] = True
    config["ENGINE_CONFIG"]["ML_CONFIDENCE_THRESHOLD"] = 0.8
    
    print("Configuration:")
    print(f"   Engine Type: {config['ENGINE_TYPE']}")
    print(f"   ML Enabled: {config['ENGINE_CONFIG']['ML_ENABLED']}")
    print(f"   ML Confidence Threshold: {config['ENGINE_CONFIG']['ML_CONFIDENCE_THRESHOLD']}")
    print(f"   ML Feature Sources: {config['ENGINE_CONFIG']['ML_FEATURE_SOURCES']}")
    
    print("\n🔮 This engine type is planned for future implementation!")
    print("   Features will include:")
    print("   • Technical indicators")
    print("   • Sentiment analysis")
    print("   • Fundamental data")
    print("   • ML model integration")
    print("   • Confidence-based signals")

def demo_configuration_override():
    """Demo configuration override functionality"""
    print("\n" + "="*60)
    print("⚙️ DEMO: CONFIGURATION OVERRIDE")
    print("="*60)
    
    # Original config
    original_config = RULE_BASED_CONFIG.copy()
    print("Original Configuration:")
    print(f"   Engine Type: {original_config['ENGINE_TYPE']}")
    print(f"   Symbols Count: {len(original_config['SYMBOLS'])}")
    print(f"   Data Period: {original_config['DATA_PERIOD']}")
    
    # Override config
    override_config = {
        "ENGINE_TYPE": "classic",
        "SYMBOLS": ["AAPL", "MSFT", "GOOGL"],
        "DATA_PERIOD": "3mo",
        "ENGINE_CONFIG": {
            "FORCE_API_FETCH": True
        }
    }
    
    # Apply override
    updated_config = original_config.copy()
    updated_config.update(override_config)
    
    print("\nAfter Override:")
    print(f"   Engine Type: {updated_config['ENGINE_TYPE']}")
    print(f"   Symbols: {updated_config['SYMBOLS']}")
    print(f"   Data Period: {updated_config['DATA_PERIOD']}")
    print(f"   Force API Fetch: {updated_config['ENGINE_CONFIG']['FORCE_API_FETCH']}")
    
    print("\n✅ Configuration override works!")

def demo_command_line_equivalents():
    """Show command-line equivalents for the demos"""
    print("\n" + "="*60)
    print("🖥️ COMMAND-LINE EQUIVALENTS")
    print("="*60)
    
    print("\nClassic Engine:")
    print("   python -m trader.rule_based --engine classic --symbols AAPL MSFT --period 1mo")
    
    print("\nMulti-Source Engine:")
    print("   python -m trader.rule_based --engine multi_source --symbols AAPL MSFT --period 1mo")
    
    print("\nWith Config Override:")
    print("   python -m trader.rule_based --config-override '{\"ENGINE_TYPE\": \"classic\", \"DATA_PERIOD\": \"3mo\"}'")
    
    print("\nForce API Fetch:")
    print("   python -m trader.rule_based --engine multi_source --force-fetch")
    
    print("\nCustom Symbols:")
    print("   python -m trader.rule_based --symbols RELIANCE.NS TCS.NS HDFCBANK.NS")

def main():
    """Main demo function"""
    print("🚀 CONFIGURABLE ENGINE DEMO SUITE")
    print("="*60)
    print(f"📅 Demo Time: {datetime.now()}")
    
    # Demo 1: Classic Engine
    demo_classic_engine()
    
    # Demo 2: Multi-Source Engine
    demo_multi_source_engine()
    
    # Demo 3: ML-Enhanced Engine (Future)
    demo_ml_enhanced_engine()
    
    # Demo 4: Configuration Override
    demo_configuration_override()
    
    # Demo 5: Command-Line Equivalents
    demo_command_line_equivalents()
    
    print("\n" + "="*60)
    print("✅ CONFIGURABLE ENGINE DEMO COMPLETED!")
    print("="*60)
    
    print("\n📋 SUMMARY:")
    print("✅ Classic engine: Single-source analysis")
    print("✅ Multi-source engine: Multi-source with consensus")
    print("🔮 ML-enhanced engine: Future ML integration")
    print("✅ Configuration override: Flexible settings")
    print("✅ Command-line support: Easy usage")
    
    print("\n🚀 READY TO USE!")
    print("Run any of the command-line examples above to start trading analysis.")

if __name__ == "__main__":
    main() 