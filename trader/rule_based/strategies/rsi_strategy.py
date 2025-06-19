from .base import RuleBasedStrategy
import pandas as pd
from logger import get_logger

class RSIStrategy(RuleBasedStrategy):
    """
    Relative Strength Index (RSI) Strategy
    
    This strategy generates signals based on RSI overbought/oversold conditions:
    - Buy Signal: RSI crosses above oversold threshold (typically 30)
    - Sell Signal: RSI crosses below overbought threshold (typically 70)
    
    RSI measures the speed and magnitude of price changes.
    """
    
    def __init__(self, period=14, oversold=30, overbought=70):
        """
        Initialize the RSI strategy
        
        Args:
            period (int): Period for RSI calculation (default: 14)
            oversold (int): Oversold threshold for buy signals (default: 30)
            overbought (int): Overbought threshold for sell signals (default: 70)
        """
        if oversold >= overbought:
            raise ValueError("oversold must be less than overbought")
            
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.logger = get_logger(__name__, log_file_prefix="rule_based")
        
        self.logger.info(f"Initialized RSI Strategy: {period}-day RSI, Oversold: {oversold}, Overbought: {overbought}")

    def calculate_rsi(self, data):
        """Calculate RSI for the given data"""
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def should_buy(self, data):
        """
        Check for buy signal: RSI crosses above oversold threshold
        """
        if len(data) < self.period + 1:
            self.logger.debug(f"Not enough data points. Need {self.period + 1}, got {len(data)}")
            return False
            
        rsi = self.calculate_rsi(data)
        
        # Get the last two values for comparison
        if len(rsi) < 2:
            self.logger.debug("Not enough data points after calculating RSI")
            return False
            
        try:
            # Convert to Python scalars using .item()
            rsi_prev = float(rsi.iloc[-2].item())
            rsi_curr = float(rsi.iloc[-1].item())
            
            # Debug log the values
            self.logger.debug(f"RSI ({self.period}d): Previous={rsi_prev:.2f}, Current={rsi_curr:.2f}")
            self.logger.debug(f"Buy Check: Previous (below oversold): {rsi_prev < self.oversold}, Current (above oversold): {rsi_curr > self.oversold}")
            
            # Buy signal: RSI crosses above oversold threshold
            # Previous: RSI < oversold (oversold condition)
            # Current: RSI > oversold (recovering from oversold)
            should_buy = rsi_prev < self.oversold and rsi_curr > self.oversold
            
            if should_buy:
                self.logger.info(f"🟢 RSI BUY: RSI ({rsi_curr:.2f}) crossed above oversold threshold ({self.oversold})")
            return should_buy
            
        except (AttributeError, ValueError) as e:
            self.logger.error(f"Error converting values: {e}")
            return False

    def should_sell(self, data):
        """
        Check for sell signal: RSI crosses below overbought threshold
        """
        if len(data) < self.period + 1:
            self.logger.debug(f"Not enough data points. Need {self.period + 1}, got {len(data)}")
            return False
            
        rsi = self.calculate_rsi(data)
        
        # Get the last two values for comparison
        if len(rsi) < 2:
            self.logger.debug("Not enough data points after calculating RSI")
            return False
            
        try:
            # Convert to Python scalars using .item()
            rsi_prev = float(rsi.iloc[-2].item())
            rsi_curr = float(rsi.iloc[-1].item())
            
            # Debug log the values
            self.logger.debug(f"RSI ({self.period}d): Previous={rsi_prev:.2f}, Current={rsi_curr:.2f}")
            self.logger.debug(f"Sell Check: Previous (above overbought): {rsi_prev > self.overbought}, Current (below overbought): {rsi_curr < self.overbought}")
            
            # Sell signal: RSI crosses below overbought threshold
            # Previous: RSI > overbought (overbought condition)
            # Current: RSI < overbought (falling from overbought)
            should_sell = rsi_prev > self.overbought and rsi_curr < self.overbought
            
            if should_sell:
                self.logger.info(f"🔴 RSI SELL: RSI ({rsi_curr:.2f}) crossed below overbought threshold ({self.overbought})")
            return should_sell
            
        except (AttributeError, ValueError) as e:
            self.logger.error(f"Error converting values: {e}")
            return False 