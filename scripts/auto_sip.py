import os
import sys
import json
import logging
from datetime import datetime, time
from kiteconnect import KiteConnect
from dotenv import load_dotenv
from postgres.postgres_db import get_db_connection, init_db
import certifi

# Ensure the parent directory is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import configuration
from config import DRY_RUN, LOG_LEVEL, LOG_TO_FILE, LOG_TO_CONSOLE

# Setup environment
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
ACCESS_FILE = "access_token.json"

def setup_logging():
    """Setup logging with file and console handlers"""
    os.makedirs("logs", exist_ok=True)
    
    handlers = []
    if LOG_TO_FILE:
        file_handler = logging.FileHandler(f'logs/sip_{datetime.now().strftime("%Y%m%d")}.log', encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        handlers.append(file_handler)
    
    if LOG_TO_CONSOLE:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        handlers.append(console_handler)
    
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        handlers=handlers
    )
    return logging.getLogger(__name__)

def get_console_message(message):
    """Convert problematic emoji messages to ASCII-friendly for Windows console"""
    if os.name == 'nt':
        replacements = {
            '🔍': '[DRY_RUN]',
            '📉': '[TRENDING_DOWN]'
        }
        for emoji, ascii_text in replacements.items():
            message = message.replace(emoji, ascii_text)
    return message

class WindowsSafeLogger:
    """Logger wrapper to handle Windows console encoding issues"""
    def __init__(self, logger):
        self.logger = logger
    
    def info(self, message):
        console_message = get_console_message(message)
        self.logger.info(console_message)
    
    def warning(self, message):
        console_message = get_console_message(message)
        self.logger.warning(console_message)
    
    def error(self, message):
        console_message = get_console_message(message)
        self.logger.error(console_message)
    
    def debug(self, message):
        console_message = get_console_message(message)
        self.logger.debug(console_message)

logger = WindowsSafeLogger(setup_logging())
kite = KiteConnect(api_key=API_KEY)

def is_market_open():
    """Check if regular market hours are open (9:15 AM - 3:30 PM)"""
    now = datetime.now().time()
    return time(9, 15) <= now <= time(15, 30)

def is_amo_hours():
    """Check if AMO hours are open (5:30 AM - 9:00 AM)"""
    now = datetime.now().time()
    return time(5, 30) <= now <= time(9, 0)

def can_place_orders():
    """Check if orders can be placed (market hours or AMO hours)"""
    return is_market_open() or is_amo_hours()

def authenticate():
    """Authenticate with Kite API using existing token or generate new session"""
    if os.path.exists(ACCESS_FILE):
        with open(ACCESS_FILE) as f:
            data = json.load(f)
            kite.set_access_token(data["access_token"])
            logger.info("✅ Using existing access token")
            return True
    else:
        logger.info("🔑 No access token found. Starting authentication...")
        print(f"\n🔗 Visit this URL to login:\n{kite.login_url()}")
        request_token = input("📝 Paste request_token here: ").strip()
        
        try:
            session_data = kite.generate_session(request_token, api_secret=API_SECRET)
            with open(ACCESS_FILE, "w") as f:
                json.dump({
                    "access_token": session_data["access_token"],
                    "public_token": session_data["public_token"]
                }, f)
            kite.set_access_token(session_data["access_token"])
            logger.info("🔒 Authentication successful")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to generate session: {e}")
            return False

def load_sip_config():
    with open("sip_config.json") as f:
        return json.load(f)

def log_sip(symbol, amount, quantity, order_type, platform, status):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO sip_orders (symbol, amount, quantity, order_type, platform, status) VALUES (%s, %s, %s, %s, %s, %s)",
            (symbol, amount, quantity, order_type, platform, status),
        )
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"💾 Logged to database: {symbol} - ₹{amount if amount else '-'} - Qty: {quantity if quantity else '-'} - {order_type} - {platform} - {status}")
    except Exception as e:
        logger.warning(f"⚠️ DB logging failed: {e}")

def place_sip(order):
    symbol = order["symbol"]
    order_type = order.get("type", "stock")
    platform = order.get("platform", "kite")
    amount = order.get("amount")
    quantity = order.get("quantity")
    try:
        logger.info(f"🔄 Attempting to place SIP order: {symbol} ({order_type})")
        if not can_place_orders():
            error_msg = "Market is closed. Orders can only be placed during market hours (9:15 AM - 3:30 PM) or AMO hours (5:30 AM - 9:00 AM)"
            logger.warning(f"⏰ Order failed for {symbol}: {error_msg}")
            log_sip(symbol, amount, quantity, order_type, platform, f"FAILED: {error_msg}")
            return
        variety = kite.VARIETY_REGULAR if is_market_open() else kite.VARIETY_AMO
        order_mode = "REGULAR" if is_market_open() else "AMO"
        if order_type == "mutual_fund":
            logger.info(f"💰 Mutual Fund SIP: {symbol} for ₹{amount}")
            if DRY_RUN:
                logger.info(f"🎯 DRY RUN: Would place {order_mode} MF order for {symbol} for ₹{amount}")
                log_sip(symbol, amount, None, order_type, platform, f"DRY_RUN: {order_mode} MF order simulated")
                return
            logger.warning(f"🚫 Mutual fund order placement not supported via Kite Connect API.")
            log_sip(symbol, amount, None, order_type, platform, "FAILED: MF order not supported via Kite Connect API")
        else:
            # Use specific emoji for stock/ETF
            if order_type == "stock":
                logger.info(f"🏦 STOCK SIP: {symbol} x {quantity} units")
            elif order_type == "etf":
                logger.info(f"📊 ETF SIP: {symbol} x {quantity} units")
            else:
                logger.info(f"💹 {order_type.upper()} SIP: {symbol} x {quantity} units")
            
            # Fetch LTP and calculate amount
            ltp = None
            try:
                ltp_data = kite.ltp(f"NSE:{symbol}")
                ltp = ltp_data[f"NSE:{symbol}"]["last_price"]
                amount = ltp * quantity
                logger.info(f"💹 LTP for {symbol}: ₹{ltp} | Total Amount: ₹{amount}")
            except Exception as e:
                logger.warning(f"⚠️ Could not fetch LTP for {symbol}: {e}")
                amount = None
            if DRY_RUN:
                logger.info(f"🎯 DRY RUN: Would place {order_mode} order for {symbol} x {quantity} units")
                log_sip(symbol, amount, quantity, order_type, platform, f"DRY_RUN: {order_mode} order simulated")
                return
            order_response = kite.place_order(
                variety=variety,
                exchange=kite.EXCHANGE_NSE,
                tradingsymbol=symbol,
                transaction_type=kite.TRANSACTION_TYPE_BUY,
                quantity=quantity,
                order_type=kite.ORDER_TYPE_MARKET,
                product=kite.PRODUCT_CNC,
            )
            logger.info(f"💰 Order placed successfully for {symbol}")
            logger.info(f"📋 Order ID: {order_response}")
            log_sip(symbol, amount, quantity, order_type, platform, f"SUCCESS: Order ID {order_response}")
    except Exception as e:
        error_msg = f"Order placement failed: {str(e)}"
        logger.error(f"❌ Order failed for {symbol}: {error_msg}")
        log_sip(symbol, amount, quantity, order_type, platform, f"FAILED: {error_msg}")

def place_all_sips():
    sip_list = load_sip_config()
    logger.info(f"🚀 Starting SIP automation for {len(sip_list)} symbols")
    logger.info(f"🔧 Dry run mode: {'ENABLED' if DRY_RUN else 'DISABLED'}")
    print()
    for sip in sip_list:
        place_sip(sip)
        print()
    logger.info("🏁 SIP automation completed")

def main():
    logger.info("=" * 60)
    logger.info("📈 STOCKBOT SIP AUTOMATION STARTED")
    logger.info("=" * 60)
    
    logger.info("🗄️ Initializing database...")
    init_db()
    
    logger.info("🔐 Authenticating with Kite...")
    if authenticate():
        place_all_sips()
    else:
        logger.error("❌ Authentication failed. Exiting.")
    
    logger.info("=" * 60)
    logger.info("📈 STOCKBOT SIP AUTOMATION ENDED")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
