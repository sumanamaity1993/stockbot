import psycopg2
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from urllib.parse import quote_plus

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

def init_ohlcv_data_table():
    """Initialize the ohlcv_data table if it does not exist"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ohlcv_data (
            symbol VARCHAR(50),
            date DATE,
            open NUMERIC,
            high NUMERIC,
            low NUMERIC,
            close NUMERIC,
            volume NUMERIC,
            PRIMARY KEY (symbol, date)
        )
    """)
    conn.commit()
    cur.close()
    conn.close() 