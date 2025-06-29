#!/usr/bin/env python3
"""
Demo: Source Manager Usage
Demonstrates how to use the centralized source manager for data fetching
"""

import os
import sys
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from trader.data import get_source_manager
from logger import get_logger

def demo_source_manager():
    """Demonstrate source manager functionality"""
    logger = get_logger(__name__, log_file_prefix="demo_source_manager")
    
    logger.info("🚀 Starting Source Manager Demo")
    logger.info("=" * 60)
    
    # Get the source manager instance
    source_manager = get_source_manager()
    
    # Get available sources
    available_sources = source_manager.get_available_sources()
    logger.info(f"📊 Available sources: {available_sources}")
    
    # Get source statistics
    stats = source_manager.get_source_statistics()
    logger.info(f"📈 Source statistics: {stats}")
    
    # Test symbols
    test_symbols = ["AAPL", "MSFT", "GOOGL"]
    
    for symbol in test_symbols:
        logger.info(f"\n📈 Processing {symbol}...")
        
        # Method 1: Fetch from all sources
        logger.info("🔄 Fetching from all sources...")
        all_sources_data = source_manager.fetch_ohlc_from_all_sources(symbol)
        
        for source, df in all_sources_data.items():
            if df is not None and not df.empty:
                logger.info(f"✅ {source}: {len(df)} data points")
                
                # Analyze data quality
                quality = source_manager.analyze_data_quality(df, symbol)
                logger.info(f"   Quality score: {quality['quality_score']:.2f}")
            else:
                logger.warning(f"❌ {source}: No data")
        
        # Method 2: Use enhanced fetcher (recommended)
        logger.info("🔄 Using enhanced fetcher...")
        result = source_manager.fetch_ohlc(symbol, interval='daily', period='1mo')
        
        if result is not None:
            df = result['data']
            source = result['source']
            logger.info(f"✅ Enhanced fetcher ({source}): {len(df)} data points")
            
            # Optimize and clean data
            df_optimized = source_manager.compress_and_optimize_data(df, symbol, source)
            df_clean = source_manager.detect_and_remove_outliers(df_optimized, symbol)
            logger.info(f"   After optimization: {len(df_clean)} data points")
        else:
            logger.warning(f"❌ Enhanced fetcher: No data for {symbol}")
        
        # Method 3: Get stock info
        logger.info("🔄 Getting stock info...")
        stock_info = source_manager.get_stock_info(symbol)
        if stock_info:
            logger.info(f"📊 Stock info: {stock_info.get('name', 'N/A')} - {stock_info.get('sector', 'N/A')}")
        else:
            logger.warning(f"❌ No stock info available for {symbol}")
        
        # Method 4: Get real-time price
        logger.info("🔄 Getting real-time price...")
        price_data = source_manager.get_real_time_price(symbol)
        if price_data:
            logger.info(f"💰 Real-time price: ${price_data.get('price', 'N/A')}")
        else:
            logger.warning(f"❌ No real-time price available for {symbol}")
    
    # Test predictive prefetching
    logger.info("\n🧠 Testing predictive prefetching...")
    prefetch_result = source_manager.predict_and_prefetch_data(test_symbols, prediction_hours=24)
    logger.info(f"📊 Prefetch result: {prefetch_result}")
    
    # Get final statistics
    final_stats = source_manager.get_source_statistics()
    logger.info(f"\n📈 Final statistics: {final_stats}")
    
    logger.info("=" * 60)
    logger.info("✅ Source Manager Demo Completed")
    logger.info("=" * 60)

def demo_engine_integration():
    """Demonstrate how engines would use the source manager"""
    logger = get_logger(__name__, log_file_prefix="demo_engine_integration")
    
    logger.info("🚀 Starting Engine Integration Demo")
    logger.info("=" * 60)
    
    # Simulate engine configuration
    engine_config = {
        "SYMBOLS": ["AAPL", "MSFT"],
        "DATA_PERIOD": "6mo",
        "DB_DUMP": True,
        "ENGINE_CONFIG": {
            "DATA_SOURCES": ["yfinance", "alpha_vantage", "polygon"]
        }
    }
    
    # Get source manager with engine config
    source_manager = get_source_manager(engine_config.get("ENGINE_CONFIG", {}))
    
    # Simulate engine data fetching
    for symbol in engine_config["SYMBOLS"]:
        logger.info(f"\n📈 Engine processing {symbol}...")
        
        # Engine would use this method for data fetching
        result = source_manager.fetch_ohlc(
            symbol=symbol,
            interval='daily',
            period=engine_config["DATA_PERIOD"],
            use_cache=True,
            save_to_db=engine_config["DB_DUMP"]
        )
        
        if result is not None:
            df = result['data']
            source = result['source']
            logger.info(f"✅ Engine fetched data: {len(df)} points from {source}")
            
            # Engine would analyze data quality
            quality = source_manager.analyze_data_quality(df, symbol)
            logger.info(f"   Data quality: {quality['quality_score']:.2f}")
            
            # Engine would optimize data
            df_optimized = source_manager.compress_and_optimize_data(df, symbol, source)
            df_clean = source_manager.detect_and_remove_outliers(df_optimized, symbol)
            logger.info(f"   Optimized data: {len(df_clean)} points")
            
            # Engine would then run strategies on the clean data
            logger.info(f"   Ready for strategy analysis")
        else:
            logger.error(f"❌ Engine failed to fetch data for {symbol}")
    
    logger.info("=" * 60)
    logger.info("✅ Engine Integration Demo Completed")
    logger.info("=" * 60)

if __name__ == "__main__":
    print("Source Manager Demo")
    print("1. Basic Source Manager Demo")
    print("2. Engine Integration Demo")
    print("3. Both")
    
    choice = input("Enter your choice (1-3): ").strip()
    
    if choice == "1":
        demo_source_manager()
    elif choice == "2":
        demo_engine_integration()
    elif choice == "3":
        demo_source_manager()
        print("\n" + "="*60 + "\n")
        demo_engine_integration()
    else:
        print("Invalid choice. Running basic demo...")
        demo_source_manager() 