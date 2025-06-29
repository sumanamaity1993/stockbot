#!/usr/bin/env python3
"""
Multi-Source Rule-Based Trading Engine
Fetches data from multiple sources and generates signals from each
"""

import os
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import time

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from trader.rule_based.strategies.simple_moving_average import SimpleMovingAverageStrategy
from trader.rule_based.strategies.exponential_moving_average import ExponentialMovingAverageStrategy
from trader.rule_based.strategies.rsi_strategy import RSIStrategy
from trader.rule_based.strategies.macd_strategy import MACDStrategy
from postgres import init_multi_source_ohlcv_tables, load_ohlcv_data, check_data_freshness, init_trading_signals_tables, store_multi_source_engine_signals, store_trading_analysis_history
from logger import get_logger
from trader.data import get_source_manager

class MultiSourceRuleBasedEngine:
    """
    Rule-based trading engine that uses multiple data sources
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the multi-source engine
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.symbols = config.get("SYMBOLS", ["AAPL", "MSFT"])
        self.data_period = config.get("DATA_PERIOD", "6mo")
        self.db_dump = config.get("DB_DUMP", True)
        self.logger = get_logger(__name__, log_file_prefix="rule_based_multi_source_engine")
        
        # Get sources from config
        self.sources = config.get("ENGINE_CONFIG", {}).get("DATA_SOURCES", ['yfinance', 'alpha_vantage', 'polygon'])
        
        # Initialize source manager (replaces enhanced fetcher and data analyzer)
        self.source_manager = get_source_manager(self.config.get("ENGINE_CONFIG", {}))
        
        # Get strategy parameters from config
        self.strategies = config.get("STRATEGIES", [])
        self.strategy_instances = self._initialize_strategies()
        
        self.logger.info(f"Initialized with {len(self.strategies)} strategies: {[s.__class__.__name__ for s in self.strategy_instances]}")
        
        # Initialize database tables
        self._init_database()
        init_trading_signals_tables()
        
    def _init_database(self):
        """Initialize database table for source manager data"""
        try:
            self.logger.info("Database table initialized for source manager data")
        except Exception as e:
            self.logger.error(f"Error initializing database table: {e}")
        
    def _initialize_strategies(self) -> List:
        """Initialize strategy instances"""
        strategies = []
        
        for strategy_config in self.strategies:
            strategy_name = strategy_config.get("name")
            params = strategy_config.get("params", {})
            
            if strategy_name == "SimpleMovingAverageStrategy":
                strategies.append(SimpleMovingAverageStrategy(**params))
            elif strategy_name == "ExponentialMovingAverageStrategy":
                strategies.append(ExponentialMovingAverageStrategy(**params))
            elif strategy_name == "RSIStrategy":
                strategies.append(RSIStrategy(**params))
            elif strategy_name == "MACDStrategy":
                strategies.append(MACDStrategy(**params))
        
        return strategies
    
    def fetch_data_from_all_sources(self, symbol: str, period: str = '6mo') -> Dict[str, Optional[pd.DataFrame]]:
        """
        Fetch data for a symbol from all configured sources using source manager
        
        Args:
            symbol: Stock symbol
            period: Data period
            
        Returns:
            Dict mapping source names to DataFrames
        """
        data_by_source = {}
        
        for source in self.sources:
            try:
                self.logger.debug(f"Fetching {symbol} from {source}")
                
                # Use source manager to get data from this specific source
                result = self.source_manager.fetch_ohlc(
                    symbol, 
                    interval='1d', 
                    period=period,
                    sources=[source],  # Only this source
                    use_cache=True,
                    save_to_db=True
                )
                
                if result is not None:
                    df = result['data']
                    actual_source = result['source']
                    data_by_source[actual_source] = df
                    self.logger.info(f"✅ {actual_source}: {len(df)} data points for {symbol}")
                else:
                    self.logger.warning(f"❌ {source}: No data for {symbol}")
                    data_by_source[source] = None
                    
            except Exception as e:
                self.logger.error(f"❌ {source}: Error fetching {symbol}: {e}")
                data_by_source[source] = None
        
        return data_by_source
    
    def evaluate_strategies(self, df: pd.DataFrame, symbol: str) -> List[Tuple[str, str]]:
        """
        Evaluate all strategies on a dataset
        
        Args:
            df: Price data DataFrame
            symbol: Stock symbol
            
        Returns:
            List of (signal_type, strategy_name) tuples
        """
        signals = []
        
        for strategy in self.strategy_instances:
            try:
                signal = strategy.generate_signal(df)
                if signal in ['buy', 'sell']:
                    signals.append((signal, strategy.__class__.__name__))
            except Exception as e:
                self.logger.error(f"Error evaluating {strategy.__class__.__name__} for {symbol}: {e}")
        
        return signals
    
    def run_multi_source_analysis(self) -> Dict[str, Any]:
        """Run multi-source analysis and store results"""
        start_time = time.time()
        self.logger.info("🔄 Running Multi-Source Engine Analysis")
        self.logger.info("🚀 STARTING SMART MULTI-SOURCE RULE-BASED ANALYSIS")
        self.logger.info("=" * 60)
        
        # SMART: Use predictive prefetching before analysis
        try:
            self.logger.info("🧠 SMART: Running predictive prefetch for optimal performance")
            prefetch_results = self.source_manager.predict_and_prefetch_data(
                self.symbols, prediction_hours=24
            )
            if prefetch_results.get('prefetched_symbols'):
                self.logger.info(f"🧠 SMART: Prefetched {len(prefetch_results['prefetched_symbols'])} symbols")
        except Exception as e:
            self.logger.warning(f"⚠️ Predictive prefetch failed: {e}")
        
        all_results = {}
        successful_symbols = 0
        failed_symbols = 0
        total_signals = 0
        buy_signals = 0
        sell_signals = 0
        hold_signals = 0
        
        # SMART: Use source-specific concurrency for processing
        source_priorities = {}
        for source in self.sources:
            concurrency_config = self.source_manager.get_optimal_concurrency(source)
            source_priorities[source] = concurrency_config['priority']
        
        sorted_sources = sorted(self.sources, key=lambda s: source_priorities[s])
        self.logger.info(f"🎯 SMART: Processing sources by priority: {sorted_sources}")
        
        for symbol in self.symbols:
            symbol_start_time = time.time()
            self.logger.info(f"\n📈 Processing {symbol}...")
            
            # Get data from all sources with smart concurrency
            sources_data = {}
            sources_analyzed = []
            data_quality_scores = {}
            signals_by_source = {}
            
            for source in sorted_sources:
                df = self.get_data_for_source(symbol, source)
                if df is not None and not df.empty:
                    sources_data[source] = df
                    sources_analyzed.append(source)
                    
                    # SMART: Compress and optimize data
                    try:
                        df_compressed = self.source_manager.compress_and_optimize_data(df, symbol, source)
                        df_clean = self.source_manager.detect_and_remove_outliers(df_compressed, symbol, method="iqr")
                        df = df_clean  # Use cleaned data
                    except Exception as e:
                        self.logger.warning(f"⚠️ Data optimization failed for {symbol} from {source}: {e}")
                    
                    # Get data quality score
                    quality = self.source_manager.analyze_data_quality(df, symbol)
                    data_quality_scores[source] = quality['quality_score']
                    
                    # Evaluate strategies
                    signals = self.evaluate_strategies(df, symbol)
                    signals_by_source[source] = signals
                    
                    # Count signals
                    for signal_type, strategy_name in signals:
                        total_signals += 1
                        if signal_type == 'buy':
                            buy_signals += 1
                        elif signal_type == 'sell':
                            sell_signals += 1
                    
                    if signals:
                        self.logger.info(f"   📊 {source}: {len(signals)} signals")
                        for signal_type, strategy_name in signals:
                            dot = "🟢" if signal_type == 'buy' else "🔴"
                            self.logger.info(f"      {dot} {signal_type.upper()} ({strategy_name})")
                    else:
                        self.logger.info(f"   📊 {source}: No signals")
                else:
                    self.logger.info(f"   ❌ {source}: No data available")
            
            if sources_analyzed:
                successful_symbols += 1
                all_results[symbol] = signals_by_source
                
                # Generate consensus signals
                consensus = self.get_consensus_signals({symbol: signals_by_source})
                consensus_data = consensus.get(symbol, {})
                
                # Store multi-source engine signals
                symbol_execution_time = int((time.time() - symbol_start_time) * 1000)
                store_multi_source_engine_signals(
                    symbol=symbol,
                    sources_analyzed=sources_analyzed,
                    consensus_signal=consensus_data.get('signal', 'hold'),
                    consensus_confidence=consensus_data.get('confidence', 0.0),
                    buy_count=consensus_data.get('buy_count', 0),
                    sell_count=consensus_data.get('sell_count', 0),
                    total_sources=consensus_data.get('total_sources', 0),
                    signals_by_source=signals_by_source,
                    strategies=[s.__class__.__name__ for s in self.strategy_instances],
                    data_quality_scores=data_quality_scores,
                    analysis_summary=f"SMART Multi-source analysis for {symbol}",
                    execution_time_ms=symbol_execution_time,
                    cache_hit=self.db_dump
                )
                
                # Count consensus signals
                if consensus_data.get('signal') == 'hold':
                    hold_signals += 1
            else:
                failed_symbols += 1
                all_results[symbol] = {}
        
        # Calculate execution time
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # SMART: Get adaptive statistics
        adaptive_stats = self.source_manager.get_adaptive_stats()
        cache_stats = self.source_manager.get_cache_analytics()
        
        # Store overall analysis history
        store_trading_analysis_history(
            engine_type="smart_multi_source",
            symbols_processed=len(self.symbols),
            successful_symbols=successful_symbols,
            failed_symbols=failed_symbols,
            total_signals=total_signals,
            buy_signals=buy_signals,
            sell_signals=sell_signals,
            hold_signals=hold_signals,
            execution_time_ms=execution_time_ms,
            config_used={
                "symbols": self.symbols,
                "data_period": self.data_period,
                "strategies": [s.__class__.__name__ for s in self.strategy_instances],
                "sources": sorted_sources,
                "db_dump": self.db_dump,
                "adaptive_stats": adaptive_stats,
                "cache_stats": cache_stats
            }
        )
        
        # Generate summary
        self._generate_smart_multi_source_summary(all_results, successful_symbols, failed_symbols, adaptive_stats)
        
        return all_results
    
    def _generate_smart_multi_source_summary(self, results: Dict, successful_symbols: int, failed_symbols: int, adaptive_stats: Dict):
        """Generate comprehensive summary of smart multi-source analysis"""
        self.logger.info("=" * 60)
        self.logger.info("SMART MULTI-SOURCE RULE-BASED TRADING SUMMARY")
        self.logger.info("=" * 60)
        
        self.logger.info(f"Total symbols processed: {len(self.symbols)}")
        self.logger.info(f"✅ Successful: {successful_symbols}")
        self.logger.info(f"❌ Failed: {failed_symbols}")
        
        # SMART: Display adaptive statistics
        if adaptive_stats:
            self.logger.info("🧠 SMART ADAPTIVE STATISTICS:")
            for source, stats in adaptive_stats.items():
                success_rate = stats.get('success_rate', 0)
                current_delay = stats.get('current_delay', 0)
                total_calls = stats.get('total_calls', 0)
                
                if total_calls > 0:
                    self.logger.info(f"   📊 {source.upper()}:")
                    self.logger.info(f"      Success Rate: {success_rate:.1%}")
                    self.logger.info(f"      Current Delay: {current_delay:.2f}s")
                    self.logger.info(f"      Total Calls: {total_calls}")
        
        # Count signals by source
        source_signals = {}
        total_signals = 0
        
        for symbol, signals_by_source in results.items():
            for source_name, signals in signals_by_source.items():
                if source_name not in source_signals:
                    source_signals[source_name] = {'buy': 0, 'sell': 0}
                
                for signal_type, strategy_name in signals:
                    source_signals[source_name][signal_type] += 1
                    total_signals += 1
        
        self.logger.info(f"Total signals generated: {total_signals}")
        
        if source_signals:
            self.logger.info("📊 Signals by Data Source:")
            for source_name, signals in source_signals.items():
                buy_count = signals['buy']
                sell_count = signals['sell']
                total = buy_count + sell_count
                
                if total > 0:
                    self.logger.info(f"   📈 {source_name.upper()}:")
                    self.logger.info(f"      🟢 BUY: {buy_count}")
                    self.logger.info(f"      🔴 SELL: {sell_count}")
                    self.logger.info(f"      📊 Total: {total}")
        
        # Show symbols with signals
        symbols_with_signals = []
        for symbol, signals_by_source in results.items():
            has_signals = any(signals for signals in signals_by_source.items())
            if has_signals:
                symbols_with_signals.append(symbol)
        
        if symbols_with_signals:
            self.logger.info(f"📈 Symbols with signals: {len(symbols_with_signals)}")
            self.logger.info("Symbols with trading signals:")
            
            for symbol in symbols_with_signals:
                signals_by_source = results[symbol]
                signal_summary = []
                
                for source_name, signals in signals_by_source.items():
                    if signals:
                        source_signals = []
                        for signal_type, strategy_name in signals:
                            dot = "🟢" if signal_type == 'buy' else "🔴"
                            source_signals.append(f"{dot} {signal_type.upper()} ({strategy_name})")
                        
                        signal_summary.append(f"{source_name}: {' | '.join(source_signals)}")
                
                if signal_summary:
                    self.logger.info(f"   📈 {symbol}: {' | '.join(signal_summary)}")
        
        # SMART: Display cache analytics
        try:
            cache_stats = self.source_manager.get_cache_analytics()
            if cache_stats:
                self.logger.info("🔥 SMART CACHE ANALYTICS:")
                self.logger.info(f"   Total Cache Entries: {cache_stats.get('total_entries', 0)}")
                self.logger.info(f"   Cache Memory Usage: {cache_stats.get('total_memory_mb', 0):.1f} MB")
                self.logger.info(f"   Cache Duration: {cache_stats.get('cache_duration', 0)}s")
        except Exception as e:
            self.logger.warning(f"⚠️ Error getting cache analytics: {e}")
        
        self.logger.info("✅ SMART Multi-Source Engine execution completed successfully")
    
    def get_consensus_signals(self, results: Dict) -> Dict[str, Dict[str, Any]]:
        """
        Generate consensus signals across all sources
        
        Args:
            results: Results from multi-source analysis
            
        Returns:
            Consensus signals for each symbol
        """
        consensus = {}
        
        for symbol, signals_by_source in results.items():
            if not signals_by_source:
                continue
            
            # Count signals by type across all sources
            buy_count = 0
            sell_count = 0
            total_sources = len(signals_by_source)
            
            for source_name, signals in signals_by_source.items():
                for signal_type, strategy_name in signals:
                    if signal_type == 'buy':
                        buy_count += 1
                    elif signal_type == 'sell':
                        sell_count += 1
            
            # Determine consensus
            if buy_count > sell_count and buy_count > total_sources / 2:
                consensus_signal = 'buy'
                confidence = buy_count / total_sources
            elif sell_count > buy_count and sell_count > total_sources / 2:
                consensus_signal = 'sell'
                confidence = sell_count / total_sources
            else:
                consensus_signal = 'hold'
                confidence = 0.0
            
            consensus[symbol] = {
                'signal': consensus_signal,
                'confidence': confidence,
                'buy_count': buy_count,
                'sell_count': sell_count,
                'total_sources': total_sources
            }
        
        return consensus

    def get_data_for_source(self, symbol: str, source: str) -> Optional[pd.DataFrame]:
        """
        Get data for a specific source with quality validation and fallback to older data
        """
        try:
            # Check DB first if enabled
            if self.db_dump:
                # Try fresh data first (1 day threshold)
                if check_data_freshness(symbol, source, days_threshold=1):
                    df = load_ohlcv_data(symbol, source)
                    if df is not None and not df.empty:
                        # Quality check for DB data
                        quality = self.source_manager.analyze_data_quality(df, symbol)
                        self.logger.info(f"✅ {source}: {len(df)} data points for {symbol} (DB - fresh). Quality: {quality['quality_score']:.2f}")
                        
                        # Skip if quality is very low
                        if quality['quality_score'] < 0.5:
                            self.logger.warning(f"❌ {source}: Very low quality data for {symbol} from DB: {quality['quality_score']:.2f}")
                            return None
                        
                        return df
                
                # Fallback: Try older data (7 days threshold) if fresh data not available
                if check_data_freshness(symbol, source, days_threshold=7):
                    df = load_ohlcv_data(symbol, source)
                    if df is not None and not df.empty:
                        # Quality check for older DB data
                        quality = self.source_manager.analyze_data_quality(df, symbol)
                        self.logger.info(f"⚠️ {source}: {len(df)} data points for {symbol} (DB - older, 7 days). Quality: {quality['quality_score']:.2f}")
                        
                        # Skip if quality is very low
                        if quality['quality_score'] < 0.5:
                            self.logger.warning(f"❌ {source}: Very low quality older data for {symbol} from DB: {quality['quality_score']:.2f}")
                            return None
                        
                        return df
            
            # Try to fetch fresh data from API
            try:
                self.logger.info(f"Fetching data for {symbol} from sources: {[source]}")
                
                # Use incremental fetching to minimize API calls
                result = self.source_manager.fetch_ohlc_incremental(
                    symbol, 
                    interval='1d', 
                    period=self.data_period,
                    sources=[source],
                    use_cache=True,
                    save_to_db=self.db_dump
                )
                
                if result is not None:
                    df = result['data']
                    fetched_source = result['source']
                    
                    # Quality check for fresh data
                    quality = self.source_manager.analyze_data_quality(df, symbol)
                    self.logger.info(f"✅ {fetched_source}: {len(df)} data points for {symbol}. Quality: {quality['quality_score']:.2f}")
                    
                    # Log quality issues if any
                    if quality['quality_score'] < 0.7:
                        self.logger.warning(f"⚠️ {fetched_source}: Low quality data for {symbol}: {quality['quality_score']:.2f}")
                        if quality.get('recommendations'):
                            for rec in quality['recommendations']:
                                self.logger.warning(f"  - {rec}")
                    
                    # Skip if quality is very low
                    if quality['quality_score'] < 0.5:
                        self.logger.error(f"❌ {fetched_source}: Very low quality data for {symbol}: {quality['quality_score']:.2f}. Skipping.")
                        return None
                    
                    return df
                    
            except Exception as api_error:
                # If API fails for any reason, try to use any available DB data as fallback
                if self.db_dump:
                    self.logger.warning(f"⚠️ {source}: API fetch failed for {symbol} ({str(api_error)[:100]}), trying DB fallback...")
                    
                    # Try even older data (30 days threshold) as last resort
                    if check_data_freshness(symbol, source, days_threshold=30):
                        df = load_ohlcv_data(symbol, source)
                        if df is not None and not df.empty:
                            quality = self.source_manager.analyze_data_quality(df, symbol)
                            self.logger.info(f"🔄 {source}: {len(df)} data points for {symbol} (DB - older, 30 days, API fallback). Quality: {quality['quality_score']:.2f}")
                            
                            # Skip if quality is very low
                            if quality['quality_score'] < 0.5:
                                self.logger.warning(f"❌ {source}: Very low quality fallback data for {symbol}: {quality['quality_score']:.2f}")
                                return None
                            
                            return df
                    
                    # If no data in DB at all, log the API error
                    self.logger.error(f"❌ {source}: No data available for {symbol} (API failed, no DB fallback): {api_error}")
                else:
                    # If DB is not enabled, just log the API error
                    self.logger.error(f"❌ {source}: API fetch failed for {symbol}: {api_error}")
                
                return None
            
            self.logger.warning(f"❌ {source}: No data for {symbol}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching data for {symbol} from {source}: {e}")
            return None 