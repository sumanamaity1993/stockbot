#!/usr/bin/env python3
"""
Configurable Rule-Based Trading Engine Main Script
Supports multiple engine types: classic, multi_source, and future ML engines
"""

import os
import sys
import argparse
from datetime import datetime
from trader.rule_based.config import RULE_BASED_CONFIG
from logger import get_logger

def create_engine(engine_type: str, config: dict):
    """
    Create the appropriate engine based on type
    
    Args:
        engine_type: Type of engine to create
        config: Configuration dictionary
        
    Returns:
        Engine instance
    """
    logger = get_logger(__name__, log_file_prefix="rule_based_main")
    
    try:
        if engine_type == "classic":
            from trader.rule_based.engine import RuleBasedEngine
            logger.info("🚦 Initializing Classic Rule-Based Engine")
            return RuleBasedEngine(config=config)
            
        elif engine_type == "multi_source":
            from trader.rule_based.multi_source_engine import MultiSourceRuleBasedEngine
            logger.info("🚦 Initializing Multi-Source Rule-Based Engine")
            return MultiSourceRuleBasedEngine(config)
            
        elif engine_type == "ml_enhanced":
            # Future ML-enhanced engine (placeholder)
            logger.warning("🤖 ML-Enhanced Engine not yet implemented")
            logger.info("🚦 Falling back to Multi-Source Engine")
            from trader.rule_based.multi_source_engine import MultiSourceRuleBasedEngine
            return MultiSourceRuleBasedEngine(config)
            
        else:
            raise ValueError(f"Unknown engine type: {engine_type}")
            
    except ImportError as e:
        logger.error(f"❌ Failed to import engine type '{engine_type}': {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to create engine: {e}")
        raise

def run_engine(engine, engine_type: str):
    """
    Run the appropriate engine method
    
    Args:
        engine: Engine instance
        engine_type: Type of engine
    """
    logger = get_logger(__name__, log_file_prefix="rule_based_main")
    
    try:
        if engine_type == "classic":
            logger.info("🔄 Running Classic Engine Analysis")
            engine.run()
            
        elif engine_type == "multi_source":
            logger.info("🔄 Running Multi-Source Engine Analysis")
            results = engine.run_multi_source_analysis()
            
            # Show consensus signals if enabled
            if RULE_BASED_CONFIG.get("ENGINE_CONFIG", {}).get("ENABLE_CONSENSUS", True):
                consensus = engine.get_consensus_signals(results)
                if consensus:
                    logger.info("\n🎯 CONSENSUS SIGNALS SUMMARY:")
                    
                    # Separate actionable signals from hold signals
                    buy_signals = []
                    sell_signals = []
                    hold_signals = []
                    
                    for symbol, data in consensus.items():
                        signal = data['signal']
                        confidence = data['confidence']
                        buy_count = data['buy_count']
                        sell_count = data['sell_count']
                        
                        signal_info = f"   📈 {symbol}: (confidence: {confidence:.2f}, buy: {buy_count}, sell: {sell_count})"
                        
                        if signal == 'buy':
                            buy_signals.append(f"🟢 BUY {signal_info}")
                        elif signal == 'sell':
                            sell_signals.append(f"🔴 SELL {signal_info}")
                        else:
                            hold_signals.append(f"⏸️  HOLD {signal_info}")
                    
                    # Show actionable signals first
                    if buy_signals:
                        logger.info("🟢 BUY SIGNALS:")
                        for signal in buy_signals:
                            logger.info(signal)
                    
                    if sell_signals:
                        logger.info("🔴 SELL SIGNALS:")
                        for signal in sell_signals:
                            logger.info(signal)
                    
                    # Show hold signals separately
                    if hold_signals:
                        logger.info("⏸️  HOLD SIGNALS:")
                        for signal in hold_signals:
                            logger.info(signal)
                    
                    # Summary counts
                    logger.info(f"\n📊 SUMMARY: {len(buy_signals)} BUY | {len(sell_signals)} SELL | {len(hold_signals)} HOLD")
            
        elif engine_type == "ml_enhanced":
            # Future ML engine execution
            logger.info("🔄 Running ML-Enhanced Engine Analysis")
            # Placeholder for ML engine execution
            pass
            
    except Exception as e:
        logger.error(f"❌ Engine execution failed: {e}")
        raise

def main():
    """Main function with command-line argument support"""
    parser = argparse.ArgumentParser(description="Rule-Based Trading Engine")
    parser.add_argument(
        "--engine", 
        choices=["classic", "multi_source", "ml_enhanced"],
        help="Engine type to use (overrides config)"
    )
    parser.add_argument(
        "--config-override",
        help="Override specific config values (JSON format)"
    )
    parser.add_argument(
        "--symbols",
        nargs="+",
        help="Override symbols list"
    )
    parser.add_argument(
        "--period",
        default="6mo",
        help="Data period (default: 6mo)"
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=["yfinance", "alpha_vantage", "polygon", "fyers"],
        help="Data sources to use (overrides config)"
    )
    parser.add_argument(
        "--force-fetch",
        action="store_true",
        help="Force fetch from API even if DB has data"
    )
    
    args = parser.parse_args()
    
    # Create a copy of config to modify
    config = RULE_BASED_CONFIG.copy()
    
    # Override engine type if specified
    engine_type = args.engine or config.get("ENGINE_TYPE", "multi_source")
    
    # Override symbols if specified
    if args.symbols:
        config["SYMBOLS"] = args.symbols
    
    # Override data period if specified
    if args.period:
        config["DATA_PERIOD"] = args.period
    
    # Override data sources if specified
    if args.sources:
        config["ENGINE_CONFIG"]["DATA_SOURCES"] = args.sources
    
    # Override force fetch if specified
    if args.force_fetch:
        config["ENGINE_CONFIG"]["FORCE_API_FETCH"] = True
    
    # Override config values if specified
    if args.config_override:
        import json
        try:
            override_config = json.loads(args.config_override)
            config.update(override_config)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in config override: {e}")
            return
    
    # Initialize logger
    logger = get_logger(__name__, log_file_prefix="rule_based_main")
    
    # Log startup information
    logger.info("🚀 RULE-BASED TRADING ENGINE STARTING")
    logger.info("=" * 50)
    logger.info(f"📅 Start Time: {datetime.now()}")
    logger.info(f"🔧 Engine Type: {engine_type}")
    logger.info(f"📊 Symbols: {len(config['SYMBOLS'])}")
    logger.info(f"📈 Data Period: {config['DATA_PERIOD']}")
    logger.info(f"🔗 Data Sources: {config['ENGINE_CONFIG'].get('DATA_SOURCES', [])}")
    logger.info(f"🗄️  DB Cache: {config['ENGINE_CONFIG'].get('ENABLE_DB_CACHE', True)}")
    logger.info(f"🔄 Force API Fetch: {config['ENGINE_CONFIG'].get('FORCE_API_FETCH', False)}")
    
    try:
        # Create and run engine
        engine = create_engine(engine_type, config)
        run_engine(engine, engine_type)
        
        logger.info("✅ Engine execution completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Engine execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 