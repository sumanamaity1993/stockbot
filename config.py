# Configuration file for Stockbot
# Change these settings as needed

# DRY RUN MODE
# Set to True for testing/analysis (no real orders placed)
# Set to False for real trading
DRY_RUN = True

# LOGGING
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_TO_FILE = True
LOG_TO_CONSOLE = True

# DATABASE
DB_TABLE_NAME = "sip_orders"

# TRADING
DEFAULT_ORDER_TYPE = "MARKET"  # MARKET, LIMIT
DEFAULT_PRODUCT = "CNC"  # CNC, MIS, NRML 