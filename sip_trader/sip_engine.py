import os
import sys
import json
from datetime import datetime, time
from kiteconnect import KiteConnect
from dotenv import load_dotenv
from postgres import get_db_connection, init_sip_orders_table
from logger import get_logger
import certifi
from .config import DRY_RUN, LOG_LEVEL, LOG_TO_FILE, LOG_TO_CONSOLE

class SIPEngine:
    def __init__(self):
        # Setup environment
        os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
        load_dotenv()
        self.logger = get_logger(__name__, LOG_TO_FILE, LOG_TO_CONSOLE, LOG_LEVEL)
        self.API_KEY = os.getenv("API_KEY")
        self.API_SECRET = os.getenv("API_SECRET")
        self.ACCESS_FILE = "access_token.json"
        self.kite = KiteConnect(api_key=self.API_KEY)

    def is_market_open(self):
        now = datetime.now().time()
        return time(9, 15) <= now <= time(15, 30)

    def is_amo_hours(self):
        now = datetime.now().time()
        return time(5, 30) <= now <= time(9, 0)

    def can_place_orders(self):
        return self.is_market_open() or self.is_amo_hours()

    def authenticate(self):
        if os.path.exists(self.ACCESS_FILE):
            with open(self.ACCESS_FILE) as f:
                data = json.load(f)
                self.kite.set_access_token(data["access_token"])
                self.logger.info("✅ Using existing access token")
                return True
        else:
            self.logger.info("🔑 No access token found. Starting authentication...")
            print(f"\n🔗 Visit this URL to login:\n{self.kite.login_url()}")
            request_token = input("📝 Paste request_token here: ").strip()
            try:
                session_data = self.kite.generate_session(request_token, api_secret=self.API_SECRET)
                with open(self.ACCESS_FILE, "w") as f:
                    json.dump({
                        "access_token": session_data["access_token"],
                        "public_token": session_data["public_token"]
                    }, f)
                self.kite.set_access_token(session_data["access_token"])
                self.logger.info("🔒 Authentication successful")
                return True
            except Exception as e:
                self.logger.error(f"❌ Failed to generate session: {e}")
                return False

    def load_sip_config(self):
        with open(os.path.join(os.path.dirname(__file__), "sip_config.json")) as f:
            return json.load(f)

    def save_sip_order(self, symbol, amount, quantity, order_type, platform, status):
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
            self.logger.debug(f"💾 Saved to database: {symbol} - ₹{amount if amount else '-'} - Qty: {quantity if quantity else '-'} - {order_type} - {platform} - {status}")
        except Exception as e:
            self.logger.warning(f"⚠️ DB saving failed: {e}")

    def place_sip(self, order):
        symbol = order["symbol"]
        order_type = order.get("type", "stock")
        platform = order.get("platform", "kite")
        amount = order.get("amount")
        quantity = order.get("quantity")
        try:
            self.logger.info(f"🔄 Attempting to place SIP order: {symbol} ({order_type})")
            if not self.can_place_orders():
                error_msg = "Market is closed. Orders can only be placed during market hours (9:15 AM - 3:30 PM) or AMO hours (5:30 AM - 9:00 AM)"
                self.logger.warning(f"⏰ Order failed for {symbol}: {error_msg}")
                self.save_sip_order(symbol, amount, quantity, order_type, platform, f"FAILED: {error_msg}")
                return
            variety = self.kite.VARIETY_REGULAR if self.is_market_open() else self.kite.VARIETY_AMO
            order_mode = "REGULAR" if self.is_market_open() else "AMO"
            if order_type == "mutual_fund":
                self.logger.info(f"💰 Mutual Fund SIP: {symbol} for ₹{amount}")
                if DRY_RUN:
                    self.logger.info(f"🎯 DRY RUN: Would place {order_mode} MF order for {symbol} for ₹{amount}")
                    self.save_sip_order(symbol, amount, None, order_type, platform, f"DRY_RUN: {order_mode} MF order simulated")
                    return
                self.logger.warning(f"🚫 Mutual fund order placement not supported via Kite Connect API.")
                self.save_sip_order(symbol, amount, None, order_type, platform, "FAILED: MF order not supported via API")
            else:
                # Use specific emoji for stock/ETF
                if order_type == "stock":
                    self.logger.info(f"🏦 STOCK SIP: {symbol} x {quantity} units")
                elif order_type == "etf":
                    self.logger.info(f"📊 ETF SIP: {symbol} x {quantity} units")
                else:
                    self.logger.info(f"💹 {order_type.upper()} SIP: {symbol} x {quantity} units")
                # Fetch LTP and calculate amount
                ltp = None
                try:
                    ltp_data = self.kite.ltp(f"NSE:{symbol}")
                    ltp = ltp_data[f"NSE:{symbol}"]["last_price"]
                    amount = ltp * quantity
                    self.logger.info(f"💹 LTP for {symbol}: ₹{ltp} | Total Amount: ₹{amount}")
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not fetch LTP for {symbol}: {e}")
                    amount = None
                if DRY_RUN:
                    self.logger.info(f"🎯 DRY RUN: Would place {order_mode} order for {symbol} x {quantity} units")
                    self.save_sip_order(symbol, amount, quantity, order_type, platform, f"DRY_RUN: {order_mode} order simulated")
                    return
                order_response = self.kite.place_order(
                    variety=variety,
                    exchange=self.kite.EXCHANGE_NSE,
                    tradingsymbol=symbol,
                    transaction_type=self.kite.TRANSACTION_TYPE_BUY,
                    quantity=quantity,
                    order_type=self.kite.ORDER_TYPE_MARKET,
                    product=self.kite.PRODUCT_CNC,
                )
                self.logger.info(f"💰 Order placed successfully for {symbol}")
                self.logger.info(f"📋 Order ID: {order_response}")
                self.save_sip_order(symbol, amount, quantity, order_type, platform, f"SUCCESS: Order ID {order_response}")
        except Exception as e:
            error_msg = f"Order placement failed: {str(e)}"
            self.logger.error(f"❌ Order failed for {symbol}: {error_msg}")
            self.save_sip_order(symbol, amount, quantity, order_type, platform, f"FAILED: {error_msg}")

    def run(self):
        self.logger.info("=" * 60)
        self.logger.info("📈 STOCKBOT SIP AUTOMATION STARTED")
        self.logger.info("=" * 60)
        self.logger.info("🗄️ Initializing database...")
        init_sip_orders_table()
        self.logger.info("🔐 Authenticating with Kite...")
        if self.authenticate():
            sip_list = self.load_sip_config()
            self.logger.info(f"🚀 Starting SIP automation for {len(sip_list)} symbols")
            self.logger.info(f"🔧 Dry run mode: {'ENABLED' if DRY_RUN else 'DISABLED'}")
            print()
            for sip in sip_list:
                self.place_sip(sip)
                print()
            self.logger.info("🏁 SIP automation completed")
        else:
            self.logger.error("❌ Authentication failed. Exiting.")
        self.logger.info("=" * 60)
        self.logger.info("📈 STOCKBOT SIP AUTOMATION ENDED")
        self.logger.info("=" * 60)

if __name__ == "__main__":
    sip_engine = SIPEngine()
    sip_engine.run()
