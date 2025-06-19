import psycopg2
import os
from dotenv import load_dotenv

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