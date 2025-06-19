from .base import RuleBasedStrategy
import pandas as pd
from logger import get_logger

class MACDStrategy(RuleBasedStrategy):
    """
    Moving Average Convergence Divergence (MACD) Strategy
    
    This strategy generates signals based on MACD crossovers:
    - Buy Signal: MACD line crosses above Signal line (bullish crossover)
    - Sell Signal: MACD line crosses below Signal line (bearish crossover)
    
    MACD shows the relationship between two moving averages of a price.
    """
    
    def __init__(self, fast_period=12, slow_period=26, signal_period=9):
        """
        Initialize the MACD strategy
        
        Args:
            fast_period (int): Fast EMA period (default: 12)
            slow_period (int): Slow EMA period (default: 26)
            signal_period (int): Signal line EMA period (default: 9)
        """
        if fast_period >= slow_period:
            raise ValueError("fast_period must be less than slow_period")
            
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.logger = get_logger(__name__, log_file_prefix="rule_based")
        
        self.logger.info(f"Initialized MACD Strategy: {fast_period}/{slow_period}/{signal_period}")

    def calculate_macd(self, data):
        """Calculate MACD line and signal line"""
        fast_ema = data['close'].ewm(span=self.fast_period).mean()
        slow_ema = data['close'].ewm(span=self.slow_period).mean()
        macd_line = fast_ema - slow_ema
        signal_line = macd_line.ewm(span=self.signal_period).mean()
        return macd_line, signal_line

    def should_buy(self, data):
        """
        Check for buy signal: MACD line crosses above Signal line
        """
        if len(data) < self.slow_period + self.signal_period:
            self.logger.debug(f"Not enough data points. Need {self.slow_period + self.signal_period}, got {len(data)}")
            return False
            
        macd_line, signal_line = self.calculate_macd(data)
        
        # Get the last two values for comparison
        if len(macd_line) < 2 or len(signal_line) < 2:
            self.logger.debug("Not enough data points after calculating MACD")
            return False
            
        try:
            # Convert to Python scalars using .item()
            macd_prev = float(macd_line.iloc[-2].item())
            macd_curr = float(macd_line.iloc[-1].item())
            signal_prev = float(signal_line.iloc[-2].item())
            signal_curr = float(signal_line.iloc[-1].item())
            
            # Debug log the values
            self.logger.debug(f"MACD Line: Previous={macd_prev:.4f}, Current={macd_curr:.4f}")
            self.logger.debug(f"Signal Line: Previous={signal_prev:.4f}, Current={signal_curr:.4f}")
            self.logger.debug(f"Buy Check: Previous (MACD < Signal): {macd_prev < signal_prev}, Current (MACD > Signal): {macd_curr > signal_curr}")
            
            # Buy signal: MACD line crosses above Signal line
            # Previous: MACD < Signal (below)
            # Current: MACD > Signal (above)
            should_buy = macd_prev < signal_prev and macd_curr > signal_curr
            
            if should_buy:
                self.logger.info(f"🟢 MACD BUY: MACD line ({macd_curr:.4f}) crossed above Signal line ({signal_curr:.4f})")
            return should_buy
            
        except (AttributeError, ValueError) as e:
            self.logger.error(f"Error converting values: {e}")
            return False

    def should_sell(self, data):
        """
        Check for sell signal: MACD line crosses below Signal line
        """
        if len(data) < self.slow_period + self.signal_period:
            self.logger.debug(f"Not enough data points. Need {self.slow_period + self.signal_period}, got {len(data)}")
            return False
            
        macd_line, signal_line = self.calculate_macd(data)
        
        # Get the last two values for comparison
        if len(macd_line) < 2 or len(signal_line) < 2:
            self.logger.debug("Not enough data points after calculating MACD")
            return False
            
        try:
            # Convert to Python scalars using .item()
            macd_prev = float(macd_line.iloc[-2].item())
            macd_curr = float(macd_line.iloc[-1].item())
            signal_prev = float(signal_line.iloc[-2].item())
            signal_curr = float(signal_line.iloc[-1].item())
            
            # Debug log the values
            self.logger.debug(f"MACD Line: Previous={macd_prev:.4f}, Current={macd_curr:.4f}")
            self.logger.debug(f"Signal Line: Previous={signal_prev:.4f}, Current={signal_curr:.4f}")
            self.logger.debug(f"Sell Check: Previous (MACD > Signal): {macd_prev > signal_prev}, Current (MACD < Signal): {macd_curr < signal_curr}")
            
            # Sell signal: MACD line crosses below Signal line
            # Previous: MACD > Signal (above)
            # Current: MACD < Signal (below)
            should_sell = macd_prev > signal_prev and macd_curr < signal_curr
            
            if should_sell:
                self.logger.info(f"🔴 MACD SELL: MACD line ({macd_curr:.4f}) crossed below Signal line ({signal_curr:.4f})")
            return should_sell
            
        except (AttributeError, ValueError) as e:
            self.logger.error(f"Error converting values: {e}")
            return False 