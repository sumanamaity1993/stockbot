from .base import RuleBasedStrategy
import pandas as pd
from logger import get_logger

class ExponentialMovingAverageStrategy(RuleBasedStrategy):
    """
    Exponential Moving Average Crossover Strategy
    
    This strategy generates signals based on EMA crossovers:
    - Golden Cross (Buy): Short EMA crosses above Long EMA
    - Death Cross (Sell): Short EMA crosses below Long EMA
    
    EMA gives more weight to recent prices compared to SMA.
    """
    
    def __init__(self, short_window=12, long_window=26):
        """
        Initialize the strategy with configurable EMA periods
        
        Args:
            short_window (int): Period for short-term EMA (default: 12)
            long_window (int): Period for long-term EMA (default: 26)
        """
        if short_window >= long_window:
            raise ValueError("short_window must be less than long_window")
            
        self.short_window = short_window
        self.long_window = long_window
        self.logger = get_logger(__name__, log_file_prefix="rule_based")
        
        self.logger.info(f"Initialized EMA Strategy: {short_window}-day vs {long_window}-day EMA")

    def should_buy(self, data):
        """
        Check for Golden Cross (buy signal)
        Golden Cross: Short EMA crosses above Long EMA
        """
        if len(data) < self.long_window:
            self.logger.debug(f"Not enough data points. Need {self.long_window}, got {len(data)}")
            return False
            
        short_ema = data['close'].ewm(span=self.short_window).mean()
        long_ema = data['close'].ewm(span=self.long_window).mean()
        
        # Get the last two values for comparison
        if len(short_ema) < 2 or len(long_ema) < 2:
            self.logger.debug("Not enough data points after calculating EMAs")
            return False
            
        try:
            # Convert to Python scalars using .item()
            short_prev = float(short_ema.iloc[-2].item())
            short_curr = float(short_ema.iloc[-1].item())
            long_prev = float(long_ema.iloc[-2].item())
            long_curr = float(long_ema.iloc[-1].item())
            
            # Debug log the values
            self.logger.debug(f"Short EMA ({self.short_window}d): Previous={short_prev:.2f}, Current={short_curr:.2f}")
            self.logger.debug(f"Long EMA ({self.long_window}d): Previous={long_prev:.2f}, Current={long_curr:.2f}")
            self.logger.debug(f"Golden Cross Check: Previous (short < long): {short_prev < long_prev}, Current (short > long): {short_curr > long_curr}")
            
            # Golden Cross: Short EMA crosses above Long EMA
            # Previous: short < long (below)
            # Current: short > long (above)
            should_buy = short_prev < long_prev and short_curr > long_curr
            
            if should_buy:
                self.logger.info(f"🟢 EMA GOLDEN CROSS: {self.short_window}d EMA ({short_curr:.2f}) crossed above {self.long_window}d EMA ({long_curr:.2f})")
            return should_buy
            
        except (AttributeError, ValueError) as e:
            self.logger.error(f"Error converting values: {e}")
            return False

    def should_sell(self, data):
        """
        Check for Death Cross (sell signal)
        Death Cross: Short EMA crosses below Long EMA
        """
        if len(data) < self.long_window:
            self.logger.debug(f"Not enough data points. Need {self.long_window}, got {len(data)}")
            return False
            
        short_ema = data['close'].ewm(span=self.short_window).mean()
        long_ema = data['close'].ewm(span=self.long_window).mean()
        
        # Get the last two values for comparison
        if len(short_ema) < 2 or len(long_ema) < 2:
            self.logger.debug("Not enough data points after calculating EMAs")
            return False
            
        try:
            # Convert to Python scalars using .item()
            short_prev = float(short_ema.iloc[-2].item())
            short_curr = float(short_ema.iloc[-1].item())
            long_prev = float(long_ema.iloc[-2].item())
            long_curr = float(long_ema.iloc[-1].item())
            
            # Debug log the values
            self.logger.debug(f"Short EMA ({self.short_window}d): Previous={short_prev:.2f}, Current={short_curr:.2f}")
            self.logger.debug(f"Long EMA ({self.long_window}d): Previous={long_prev:.2f}, Current={long_curr:.2f}")
            self.logger.debug(f"Death Cross Check: Previous (short > long): {short_prev > long_prev}, Current (short < long): {short_curr < long_curr}")
            
            # Death Cross: Short EMA crosses below Long EMA
            # Previous: short > long (above)
            # Current: short < long (below)
            should_sell = short_prev > long_prev and short_curr < long_curr
            
            if should_sell:
                self.logger.info(f"🔴 EMA DEATH CROSS: {self.short_window}d EMA ({short_curr:.2f}) crossed below {self.long_window}d EMA ({long_curr:.2f})")
            return should_sell
            
        except (AttributeError, ValueError) as e:
            self.logger.error(f"Error converting values: {e}")
            return False 