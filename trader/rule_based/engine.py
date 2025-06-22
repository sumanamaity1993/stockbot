import pandas as pd
from trader.data import yfinance_fetcher, kite_fetcher
from trader.data.enhanced_fetcher import EnhancedDataFetcher
from trader.data.config import ENHANCED_DATA_CONFIG
from postgres import get_db_connection, get_sqlalchemy_engine, init_ohlcv_data_table
from trader.rule_based.strategies.simple_moving_average import SimpleMovingAverageStrategy
from trader.rule_based.strategies.exponential_moving_average import ExponentialMovingAverageStrategy
from trader.rule_based.strategies.rsi_strategy import RSIStrategy
from trader.rule_based.strategies.macd_strategy import MACDStrategy
from logger import get_logger

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
            log_file_prefix="rule_based"
        )
        
        # Initialize enhanced data fetcher
        self.enhanced_fetcher = EnhancedDataFetcher(ENHANCED_DATA_CONFIG)
        
        # Get strategy parameters from config
        strategy_config = config.get("STRATEGY_CONFIG", {})
        
        if strategies is None:
            # Create default strategies based on config
            self.strategies = []
            
            # Add SMA strategy if enabled
            if strategy_config.get("USE_SMA", True):
                short_window = strategy_config.get("SMA_SHORT_WINDOW", 20)
                long_window = strategy_config.get("SMA_LONG_WINDOW", 50)
                self.strategies.append(SimpleMovingAverageStrategy(short_window=short_window, long_window=long_window))
            
            # Add EMA strategy if enabled
            if strategy_config.get("USE_EMA", False):
                short_window = strategy_config.get("EMA_SHORT_WINDOW", 12)
                long_window = strategy_config.get("EMA_LONG_WINDOW", 26)
                self.strategies.append(ExponentialMovingAverageStrategy(short_window=short_window, long_window=long_window))
            
            # Add RSI strategy if enabled
            if strategy_config.get("USE_RSI", False):
                period = strategy_config.get("RSI_PERIOD", 14)
                oversold = strategy_config.get("RSI_OVERSOLD", 30)
                overbought = strategy_config.get("RSI_OVERBOUGHT", 70)
                self.strategies.append(RSIStrategy(period=period, oversold=oversold, overbought=overbought))
            
            # Add MACD strategy if enabled
            if strategy_config.get("USE_MACD", False):
                fast_period = strategy_config.get("MACD_FAST_PERIOD", 12)
                slow_period = strategy_config.get("MACD_SLOW_PERIOD", 26)
                signal_period = strategy_config.get("MACD_SIGNAL_PERIOD", 9)
                self.strategies.append(MACDStrategy(fast_period=fast_period, slow_period=slow_period, signal_period=signal_period))
            
            # If no strategies enabled, use default SMA
            if not self.strategies:
                self.strategies = [SimpleMovingAverageStrategy()]
        else:
            self.strategies = strategies
            
        self.logger.info(f"Initialized with {len(self.strategies)} strategies: {[s.__class__.__name__ for s in self.strategies]}")
        self.engine = get_sqlalchemy_engine()

    def evaluate(self, data):
        signals = []
        for strategy in self.strategies:
            if strategy.should_buy(data):
                signals.append(('buy', strategy.__class__.__name__))
            if strategy.should_sell(data):
                signals.append(('sell', strategy.__class__.__name__))
        return signals

    def fetch_data_from_db(self, symbol):
        query = """
            SELECT date, open, high, low, close, volume
            FROM ohlcv_data
            WHERE symbol = %(symbol)s
            ORDER BY date ASC
        """
        df = pd.read_sql(query, self.engine, params={"symbol": symbol})
        return df

    def get_scalar(self, val):
        """Robustly extract a scalar value from a pandas Series, numpy array, or other iterable."""
        # If it's a pandas Series, get the first element
        if isinstance(val, pd.Series):
            val = val.iloc[0]
        # If it's a numpy generic or has item() method, convert to Python scalar
        if hasattr(val, 'item'):
            try:
                val = val.item()
            except Exception:
                pass
        # If it's still iterable (but not a string/bytes), get first element
        if hasattr(val, '__iter__') and not isinstance(val, (str, bytes)):
            try:
                val = next(iter(val))
            except Exception:
                pass
        return val

    def dump_data_to_db(self, symbol, df):
        conn = get_db_connection()
        cur = conn.cursor()
        for _, row in df.iterrows():
            # Extract and convert each value, with debug prints
            self.logger.debug(f"Raw types before conversion - date: {type(row['date'])}, open: {type(row['open'])}")
            
            date_val = self.get_scalar(row['date'])
            if hasattr(date_val, 'to_pydatetime'):
                date_val = date_val.to_pydatetime()
            
            try:
                open_val = float(self.get_scalar(row['open']))
                high_val = float(self.get_scalar(row['high']))
                low_val = float(self.get_scalar(row['low']))
                close_val = float(self.get_scalar(row['close']))
                volume_val = int(self.get_scalar(row['volume']))
            except Exception as e:
                self.logger.error(f"Conversion error for {symbol}: {e}")
                self.logger.error(f"Values: open={row['open']}, high={row['high']}, low={row['low']}, close={row['close']}, volume={row['volume']}")
                raise

            # Debug print final types
            self.logger.debug(
                f"Final types - date: {type(date_val)}, open: {type(open_val)}, "
                f"high: {type(high_val)}, low: {type(low_val)}, "
                f"close: {type(close_val)}, volume: {type(volume_val)}"
            )

            cur.execute(
                """
                INSERT INTO ohlcv_data (symbol, date, open, high, low, close, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, date) DO NOTHING
                """,
                (symbol, date_val, open_val, high_val, low_val, close_val, volume_val)
            )
        conn.commit()
        cur.close()
        conn.close()

    def get_data(self, symbol):
        """
        Enhanced data fetching with multiple sources and fallback
        """
        self.logger.info(f"Fetching data for {symbol} using enhanced fetcher")
        
        try:
            # Use enhanced fetcher as primary method
            df = self.enhanced_fetcher.fetch_ohlc(
                symbol, 
                interval='1d', 
                period=self.data_period,
                use_cache=True
            )
            
            if df is not None and not df.empty:
                self.logger.info(f"Successfully fetched data from enhanced fetcher for {symbol}: {len(df)} rows")
                return df
            
            # Fallback to original methods if enhanced fetcher fails
            self.logger.warning(f"Enhanced fetcher failed for {symbol}, falling back to original methods")
            
            if self.data_source == "yfinance":
                try:
                    df = yfinance_fetcher.fetch_ohlc_enhanced(symbol, period=self.data_period)
                    if df is not None and not df.empty:
                        self.logger.info(f"Successfully fetched data from yfinance for {symbol}")
                        return df
                except Exception as e:
                    self.logger.warning(f"yfinance failed for {symbol}: {e}")
                
                # Try kite as last resort
                self.logger.info("Falling back to Kite API...")
                try:
                    return kite_fetcher.fetch_ohlc(symbol, interval='day')
                except Exception as kite_error:
                    self.logger.error(f"All data sources failed for {symbol}: {kite_error}")
                    return None
                    
            elif self.data_source == "kite":
                try:
                    return kite_fetcher.fetch_ohlc(symbol, interval='day')
                except Exception as e:
                    self.logger.error(f"Kite failed for {symbol}: {e}")
                    return None
            else:
                raise ValueError(f"Unknown data source: {self.data_source}")
                
        except Exception as e:
            self.logger.error(f"Error in enhanced data fetching for {symbol}: {e}")
            return None

    def run(self):
        init_ohlcv_data_table()
        self.logger.info(f"Running rule-based trading for symbols: {self.symbols} using enhanced data fetcher")
        results = {}
        successful_symbols = 0
        failed_symbols = 0
        symbols_with_signals = []
        
        for symbol in self.symbols:
            self.logger.info(f"Processing {symbol}")
            df = None
            if self.db_dump:
                try:
                    df = self.fetch_data_from_db(symbol)
                    if not df.empty:
                        self.logger.info("Loaded data from DB.")
                except Exception as e:
                    self.logger.warning(f"DB load failed for {symbol}: {e}")
                    df = None
            if df is None or df.empty:
                df = self.get_data(symbol)
                if df is not None and not df.empty and self.db_dump:
                    self.dump_data_to_db(symbol, df)
                    self.logger.info("Dumped data to DB.")
            
            if df is not None and not df.empty:
                signals = self.evaluate(df)
                self.logger.info(f"{symbol} Signals: {signals}")
                results[symbol] = signals
                successful_symbols += 1
                
                if signals:
                    symbols_with_signals.append(symbol)
            else:
                failed_symbols += 1
                self.logger.error(f"Failed to get data for {symbol}")
        
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
                signal_details = []
                for signal_type, strategy_name in signals:
                    if signal_type == 'buy':
                        signal_details.append(f"🟢 BUY ({strategy_name})")
                    elif signal_type == 'sell':
                        signal_details.append(f"🔴 SELL ({strategy_name})")
                    else:
                        signal_details.append(f"⚪ {signal_type.upper()} ({strategy_name})")
                
                signal_str = " | ".join(signal_details)
                self.logger.info(f"  📈 {symbol}: {signal_str}")
            
            # Count buy vs sell signals
            buy_signals = sum(1 for symbol in symbols_with_signals 
                            for signal_type, _ in results[symbol] if signal_type == 'buy')
            sell_signals = sum(1 for symbol in symbols_with_signals 
                             for signal_type, _ in results[symbol] if signal_type == 'sell')
            
            self.logger.info("")
            self.logger.info("Signal Summary:")
            self.logger.info(f"  🟢 Buy signals: {buy_signals}")
            self.logger.info(f"  🔴 Sell signals: {sell_signals}")
            self.logger.info(f"  📊 Total signals: {buy_signals + sell_signals}")
        else:
            self.logger.info("😴 No trading signals found in current market conditions")
            self.logger.info("💡 Consider:")
            self.logger.info("   • Using shorter moving average periods for more signals")
            self.logger.info("   • Enabling additional strategies (EMA, RSI, MACD)")
            self.logger.info("   • Checking different time periods")
        
        # Cache statistics
        cache_stats = self.enhanced_fetcher.get_cache_stats()
        self.logger.info(f"Cache statistics: {cache_stats['cache_size']} entries, duration: {cache_stats['cache_duration']}s")
        
        return results 