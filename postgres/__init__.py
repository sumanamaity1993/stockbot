import psycopg2
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from urllib.parse import quote_plus
import json

load_dotenv()

def get_db_connection():
    """Get database connection using environment variables"""
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )

def get_sqlalchemy_engine():
    """Get SQLAlchemy engine using environment variables"""
    user = quote_plus(os.getenv('DB_USER'))
    password = quote_plus(os.getenv('DB_PASSWORD'))
    host = os.getenv('DB_HOST')
    port = os.getenv('DB_PORT')
    db = os.getenv('DB_NAME')
    db_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    return create_engine(db_url)

def init_sip_orders_table():
    """Initialize the sip_orders table"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sip_orders (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT NOW(),
            symbol VARCHAR(50),
            amount DECIMAL(10,2),
            quantity INTEGER,
            order_type VARCHAR(20),
            platform VARCHAR(20),
            status TEXT
        )
    """)
    
    conn.commit()
    cur.close()
    conn.close()

def init_multi_source_ohlcv_tables(sources=None):
    """
    Initialize separate OHLCV tables for each data source
    
    Args:
        sources: List of data sources (default: ['yfinance', 'alpha_vantage', 'polygon'])
    """
    if sources is None:
        sources = ['yfinance', 'alpha_vantage', 'polygon']
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Define table schemas for each source
    for source in sources:
        table_name = f"ohlcv_{source}"
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                symbol VARCHAR(50),
                date DATE,
                open NUMERIC,
                high NUMERIC,
                low NUMERIC,
                close NUMERIC,
                volume NUMERIC,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                PRIMARY KEY (symbol, date)
            )
        """)
        
        # Create indexes for better performance
        cur.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{table_name}_symbol_date 
            ON {table_name} (symbol, date)
        """)
        
        cur.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{table_name}_date 
            ON {table_name} (date)
        """)
    
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Multi-source OHLCV tables initialized successfully!")

def get_source_table_name(source: str) -> str:
    """Get the table name for a given data source"""
    return f"ohlcv_{source}"

def store_ohlcv_data(df, source: str, symbol: str):
    """
    Store OHLCV data in the appropriate source table
    
    Args:
        df: DataFrame with OHLCV data
        source: Data source name (yfinance, alpha_vantage, polygon)
        symbol: Stock symbol
    """
    if df is None or df.empty:
        return False
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        table_name = get_source_table_name(source)
        
        # Prepare data for insertion
        data_to_insert = []
        for _, row in df.iterrows():
            data_to_insert.append((
                symbol,
                row['date'].date(),
                float(row['open']),
                float(row['high']),
                float(row['low']),
                float(row['close']),
                float(row['volume']) if 'volume' in row else 0
            ))
        
        # Use UPSERT (INSERT ... ON CONFLICT) to handle duplicates
        cur.executemany(f"""
            INSERT INTO {table_name} (symbol, date, open, high, low, close, volume, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (symbol, date) 
            DO UPDATE SET 
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                volume = EXCLUDED.volume,
                updated_at = NOW()
        """, data_to_insert)
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Stored {len(data_to_insert)} records for {symbol} in {table_name}")
        return True
        
    except Exception as e:
        print(f"❌ Error storing data for {symbol} in {source}: {e}")
        return False

def load_ohlcv_data(symbol: str, source: str, start_date=None, end_date=None):
    """
    Load OHLCV data from the appropriate source table
    
    Args:
        symbol: Stock symbol
        source: Data source name (yfinance, alpha_vantage, polygon)
        start_date: Start date (optional)
        end_date: End date (optional)
        
    Returns:
        DataFrame or None: OHLCV data
    """
    try:
        import pandas as pd
        
        conn = get_db_connection()
        table_name = get_source_table_name(source)
        
        # Build query
        query = f"""
            SELECT symbol, date, open, high, low, close, volume
            FROM {table_name}
            WHERE symbol = %s
        """
        params = [symbol]
        
        if start_date:
            query += " AND date >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND date <= %s"
            params.append(end_date)
        
        query += " ORDER BY date"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        if not df.empty:
            print(f"✅ Loaded {len(df)} records for {symbol} from {table_name}")
            return df
        else:
            print(f"📊 No data found for {symbol} in {table_name}")
            return None
            
    except Exception as e:
        print(f"❌ Error loading data for {symbol} from {source}: {e}")
        return None

def check_data_freshness(symbol: str, source: str, days_threshold: int = 1):
    """
    Check if data for a symbol is fresh (recently updated)
    
    Args:
        symbol: Stock symbol
        source: Data source name
        days_threshold: Number of days to consider data fresh
        
    Returns:
        bool: True if data is fresh, False otherwise
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        table_name = get_source_table_name(source)
        
        cur.execute(f"""
            SELECT MAX(updated_at) 
            FROM {table_name} 
            WHERE symbol = %s
        """, (symbol,))
        
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if result and result[0]:
            from datetime import datetime, timedelta
            last_updated = result[0]
            threshold_date = datetime.now() - timedelta(days=days_threshold)
            
            return last_updated >= threshold_date
        else:
            return False
            
    except Exception as e:
        print(f"❌ Error checking data freshness for {symbol} from {source}: {e}")
        return False

def init_trading_signals_tables():
    """Initialize tables for storing trading signals and analysis"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Classic Engine Signals Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS classic_engine_signals (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT NOW(),
            symbol VARCHAR(20),
            data_source VARCHAR(50),
            data_quality_score DECIMAL(3,2),
            data_points INTEGER,
            period VARCHAR(10),
            signals_generated JSONB,
            strategies_applied JSONB,
            analysis_summary TEXT,
            execution_time_ms INTEGER,
            cache_hit BOOLEAN,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    
    # Multi-Source Engine Signals Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS multi_source_engine_signals (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT NOW(),
            symbol VARCHAR(20),
            sources_analyzed JSONB,
            consensus_signal VARCHAR(10),
            consensus_confidence DECIMAL(3,2),
            buy_count INTEGER,
            sell_count INTEGER,
            total_sources INTEGER,
            signals_by_source JSONB,
            strategies_applied JSONB,
            data_quality_scores JSONB,
            analysis_summary TEXT,
            execution_time_ms INTEGER,
            cache_hit BOOLEAN,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    
    # Trading Analysis History Table (Common fields)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS trading_analysis_history (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT NOW(),
            engine_type VARCHAR(20),
            symbols_processed INTEGER,
            successful_symbols INTEGER,
            failed_symbols INTEGER,
            total_signals_generated INTEGER,
            buy_signals INTEGER,
            sell_signals INTEGER,
            hold_signals INTEGER,
            execution_time_ms INTEGER,
            config_used JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    
    # Create indexes for better performance
    cur.execute("CREATE INDEX IF NOT EXISTS idx_classic_signals_symbol ON classic_engine_signals (symbol)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_classic_signals_timestamp ON classic_engine_signals (timestamp)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_multi_signals_symbol ON multi_source_engine_signals (symbol)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_multi_signals_timestamp ON multi_source_engine_signals (timestamp)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_analysis_history_timestamp ON trading_analysis_history (timestamp)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_analysis_history_engine ON trading_analysis_history (engine_type)")
    
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Trading signals tables initialized successfully!")

def store_classic_engine_signals(symbol: str, data_source: str, data_quality_score: float, 
                                data_points: int, period: str, signals: list, strategies: list,
                                analysis_summary: str, execution_time_ms: int, cache_hit: bool):
    """Store classic engine signals and analysis"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO classic_engine_signals 
            (symbol, data_source, data_quality_score, data_points, period, signals_generated, 
             strategies_applied, analysis_summary, execution_time_ms, cache_hit)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            symbol, data_source, data_quality_score, data_points, period,
            json.dumps(signals), json.dumps(strategies), analysis_summary, 
            execution_time_ms, cache_hit
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error storing classic engine signals: {e}")

def store_multi_source_engine_signals(symbol: str, sources_analyzed: list, consensus_signal: str,
                                     consensus_confidence: float, buy_count: int, sell_count: int,
                                     total_sources: int, signals_by_source: dict, strategies: list,
                                     data_quality_scores: dict, analysis_summary: str,
                                     execution_time_ms: int, cache_hit: bool):
    """Store multi-source engine signals and consensus analysis"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO multi_source_engine_signals 
            (symbol, sources_analyzed, consensus_signal, consensus_confidence, buy_count, sell_count,
             total_sources, signals_by_source, strategies_applied, data_quality_scores,
             analysis_summary, execution_time_ms, cache_hit)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            symbol, json.dumps(sources_analyzed), consensus_signal, consensus_confidence,
            buy_count, sell_count, total_sources, json.dumps(signals_by_source),
            json.dumps(strategies), json.dumps(data_quality_scores), analysis_summary,
            execution_time_ms, cache_hit
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error storing multi-source engine signals: {e}")

def store_trading_analysis_history(engine_type: str, symbols_processed: int, successful_symbols: int,
                                  failed_symbols: int, total_signals: int, buy_signals: int,
                                  sell_signals: int, hold_signals: int, execution_time_ms: int,
                                  config_used: dict):
    """Store overall trading analysis history"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO trading_analysis_history 
            (engine_type, symbols_processed, successful_symbols, failed_symbols, total_signals_generated,
             buy_signals, sell_signals, hold_signals, execution_time_ms, config_used)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            engine_type, symbols_processed, successful_symbols, failed_symbols, total_signals,
            buy_signals, sell_signals, hold_signals, execution_time_ms, json.dumps(config_used)
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error storing trading analysis history: {e}")

def get_trading_signals_history(engine_type: str = None, symbol: str = None, 
                               days_back: int = 30) -> list:
    """Retrieve trading signals history for analysis"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        if engine_type == 'classic':
            query = """
                SELECT * FROM classic_engine_signals 
                WHERE timestamp >= NOW() - INTERVAL '%s days'
                ORDER BY timestamp DESC
            """
            if symbol:
                query = query.replace("WHERE", f"WHERE symbol = '{symbol}' AND")
        elif engine_type == 'multi_source':
            query = """
                SELECT * FROM multi_source_engine_signals 
                WHERE timestamp >= NOW() - INTERVAL '%s days'
                ORDER BY timestamp DESC
            """
            if symbol:
                query = query.replace("WHERE", f"WHERE symbol = '{symbol}' AND")
        else:
            # Get from both tables
            query = """
                SELECT 'classic' as engine_type, * FROM classic_engine_signals 
                WHERE timestamp >= NOW() - INTERVAL '%s days'
                UNION ALL
                SELECT 'multi_source' as engine_type, * FROM multi_source_engine_signals 
                WHERE timestamp >= NOW() - INTERVAL '%s days'
                ORDER BY timestamp DESC
            """
            if symbol:
                query = query.replace("WHERE", f"WHERE symbol = '{symbol}' AND")
        
        cur.execute(query, (days_back,))
        results = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return results
        
    except Exception as e:
        print(f"❌ Error retrieving trading signals history: {e}")
        return [] 