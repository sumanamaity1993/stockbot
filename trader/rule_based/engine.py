import pandas as pd
from trader.data.enhanced_fetcher import EnhancedDataFetcher
from trader.data.config import ENHANCED_DATA_CONFIG
from postgres import get_sqlalchemy_engine, init_trading_signals_tables, store_classic_engine_signals, store_trading_analysis_history
from trader.rule_based.strategies.simple_moving_average import SimpleMovingAverageStrategy
from trader.rule_based.strategies.exponential_moving_average import ExponentialMovingAverageStrategy
from trader.rule_based.strategies.rsi_strategy import RSIStrategy
from trader.rule_based.strategies.macd_strategy import MACDStrategy
from trader.data.data_quality import DataQualityAnalyzer
from logger import get_logger
import time

class RuleBasedEngine:
    def __init__(self, config, strategies=None):
        self.config = config
        self.symbols = config["SYMBOLS"]
        self.data_source = config["DATA_SOURCE"]
        self.db_dump = config["DB_DUMP"]
        self.data_period = config["DATA_PERIOD"]
        self.logger = get_logger(
            __name__,
            config["LOG_TO_FILE"],
            config["LOG_TO_CONSOLE"],
            config["LOG_LEVEL"],
            log_file_prefix="rule_based_classic_engine"
        )
        
        # Initialize enhanced data fetcher
        self.enhanced_fetcher = EnhancedDataFetcher(self.config.get("ENGINE_CONFIG", {}))
        
        # Initialize data quality analyzer
        self.data_analyzer = DataQualityAnalyzer(self.config.get("ENGINE_CONFIG", {}))
        
        # Get strategy parameters from config
        strategies_config = config.get("STRATEGIES", [])
        
        if strategies is None:
            # Create strategies based on new config format
            self.strategies = []
            
            for strategy_config in strategies_config:
                strategy_name = strategy_config.get("name")
                params = strategy_config.get("params", {})
                
                if strategy_name == "SimpleMovingAverageStrategy":
                    self.strategies.append(SimpleMovingAverageStrategy(**params))
                elif strategy_name == "ExponentialMovingAverageStrategy":
                    self.strategies.append(ExponentialMovingAverageStrategy(**params))
                elif strategy_name == "RSIStrategy":
                    self.strategies.append(RSIStrategy(**params))
                elif strategy_name == "MACDStrategy":
                    self.strategies.append(MACDStrategy(**params))
                else:
                    self.logger.warning(f"Unknown strategy: {strategy_name}")
            
            # If no strategies configured, use default SMA
            if not self.strategies:
                self.strategies = [SimpleMovingAverageStrategy()]
        else:
            self.strategies = strategies
            
        self.logger.info(f"Initialized with {len(self.strategies)} strategies: {[s.__class__.__name__ for s in self.strategies]}")
        self.engine = get_sqlalchemy_engine()
        
        # Initialize trading signals tables
        init_trading_signals_tables()

    def evaluate(self, data):
        signals = []
        for strategy in self.strategies:
            if strategy.should_buy(data):
                signals.append(('buy', strategy.__class__.__name__))
            if strategy.should_sell(data):
                signals.append(('sell', strategy.__class__.__name__))
        return signals

    def get_data(self, symbol):
        """
        Enhanced data fetching using only the enhanced fetcher with quality validation
        """
        self.logger.info(f"Fetching data for {symbol} using enhanced fetcher")
        
        try:
            # Get sources from config
            sources = self.config.get("ENGINE_CONFIG", {}).get("DATA_SOURCES", ['yfinance', 'alpha_vantage', 'polygon'])
            
            # First try to load from individual source databases
            if self.db_dump:
                for source in sources:
                    db_result = self.enhanced_fetcher.load_from_source_db(
                        symbol, 
                        source,
                        days_fresh=1
                    )
                    
                    if db_result is not None:
                        df = db_result['data']
                        source = db_result['source']
                        
                        # Quality check for DB data
                        quality = self.data_analyzer.analyze_data_quality(df, symbol)
                        self.logger.info(f"Loaded data from DB for {symbol} (source: {source}). Quality score: {quality['quality_score']:.2f}")
                        
                        # Skip if quality is very low
                        if quality['quality_score'] < 0.5:
                            self.logger.warning(f"Very low quality data for {symbol} from {source} DB: {quality['quality_score']:.2f}")
                            continue
                        
                        return df
            
            # Fetch fresh data using enhanced fetcher
            result = self.enhanced_fetcher.fetch_ohlc(
                symbol, 
                interval='1d', 
                period=self.data_period,
                sources=sources,
                use_cache=True,
                save_to_db=self.db_dump
            )
            
            if result is not None:
                df = result['data']
                source = result['source']
                
                # Quality check for fresh data
                quality = self.data_analyzer.analyze_data_quality(df, symbol)
                self.logger.info(f"Successfully fetched data for {symbol} from {source}: {len(df)} rows. Quality score: {quality['quality_score']:.2f}")
                
                # Log quality issues if any
                if quality['quality_score'] < 0.7:
                    self.logger.warning(f"Low quality data for {symbol} from {source}: {quality['quality_score']:.2f}")
                    if quality.get('recommendations'):
                        for rec in quality['recommendations']:
                            self.logger.warning(f"  - {rec}")
                
                # Skip if quality is very low
                if quality['quality_score'] < 0.5:
                    self.logger.error(f"Very low quality data for {symbol} from {source}: {quality['quality_score']:.2f}. Skipping trading.")
                    return None
                
                return df
            
            self.logger.error(f"Failed to fetch data for {symbol} from enhanced fetcher")
            return None
                
        except Exception as e:
            self.logger.error(f"Error in enhanced data fetching for {symbol}: {e}")
            return None

    def run(self):
        start_time = time.time()
        self.logger.info(f"Running rule-based trading for symbols: {self.symbols} using enhanced data fetcher")
        results = {}
        successful_symbols = 0
        failed_symbols = 0
        symbols_with_signals = []
        total_signals = 0
        buy_signals = 0
        sell_signals = 0
        
        for symbol in self.symbols:
            symbol_start_time = time.time()
            self.logger.info(f"Processing {symbol}")
            
            # Get data using enhanced fetcher (handles DB loading and saving)
            df = self.get_data(symbol)
            
            if df is not None and not df.empty:
                signals = self.evaluate(df)
                self.logger.info(f"{symbol} Signals: {signals}")
                results[symbol] = signals
                successful_symbols += 1
                
                # Count signals
                for signal_type, strategy_name in signals:
                    total_signals += 1
                    if signal_type == 'buy':
                        buy_signals += 1
                    elif signal_type == 'sell':
                        sell_signals += 1
                
                if signals:
                    symbols_with_signals.append(symbol)
                
                # Store individual symbol analysis
                symbol_execution_time = int((time.time() - symbol_start_time) * 1000)
                data_source = "enhanced_fetcher"  # Default source
                data_quality_score = 0.0  # Will be updated if available
                data_points = len(df)
                
                # Try to get data source and quality from enhanced fetcher
                try:
                    # This would need to be passed from get_data method
                    # For now, using defaults
                    pass
                except:
                    pass
                
                # Store classic engine signals
                store_classic_engine_signals(
                    symbol=symbol,
                    data_source=data_source,
                    data_quality_score=data_quality_score,
                    data_points=data_points,
                    period=self.data_period,
                    signals=signals,
                    strategies=[s.__class__.__name__ for s in self.strategies],
                    analysis_summary=f"Classic engine analysis for {symbol}",
                    execution_time_ms=symbol_execution_time,
                    cache_hit=self.db_dump  # Simplified cache hit detection
                )
            else:
                failed_symbols += 1
        
        # Calculate execution time
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Store overall analysis history
        store_trading_analysis_history(
            engine_type="classic",
            symbols_processed=len(self.symbols),
            successful_symbols=successful_symbols,
            failed_symbols=failed_symbols,
            total_signals=total_signals,
            buy_signals=buy_signals,
            sell_signals=sell_signals,
            hold_signals=0,  # Classic engine doesn't generate hold signals
            execution_time_ms=execution_time_ms,
            config_used={
                "symbols": self.symbols,
                "data_period": self.data_period,
                "strategies": [s.__class__.__name__ for s in self.strategies],
                "db_dump": self.db_dump
            }
        )
        
        # Summary
        self.logger.info("=" * 60)
        self.logger.info("RULE-BASED TRADING SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Total symbols processed: {len(self.symbols)}")
        self.logger.info(f"✅ Successful: {successful_symbols}")
        self.logger.info(f"❌ Failed: {failed_symbols}")
        self.logger.info(f"Symbols with signals: {len(symbols_with_signals)}")
        
        if symbols_with_signals:
            self.logger.info("Symbols with trading signals:")
            for symbol in symbols_with_signals:
                signals = results[symbol]
                signal_summary = []
                for signal_type, strategy_name in signals:
                    dot = "🟢" if signal_type == 'buy' else "🔴"
                    signal_summary.append(f"{dot} {signal_type.upper()} ({strategy_name})")
                self.logger.info(f"   📈 {symbol}: {' | '.join(signal_summary)}")
        else:
            self.logger.info("😴 No trading signals found in current market conditions")
            self.logger.info("💡 Consider:")
            self.logger.info("   • Using shorter moving average periods for more signals")
            self.logger.info("   • Enabling additional strategies (EMA, RSI, MACD)")
            self.logger.info("   • Checking different time periods")
        
        # Cache statistics
        cache_stats = self.enhanced_fetcher.get_cache_stats()
        self.logger.info(f"Cache statistics: {cache_stats['cache_size']} entries, duration: {cache_stats['cache_duration']}s")
        
        self.logger.info(f"✅ Engine execution completed successfully")
        
        return results 