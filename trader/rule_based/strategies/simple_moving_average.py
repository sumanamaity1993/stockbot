from .base import RuleBasedStrategy
import pandas as pd
from logger import get_logger

class SimpleMovingAverageStrategy(RuleBasedStrategy):
    """
    Simple Moving Average Crossover Strategy
    
    This strategy generates signals based on moving average crossovers:
    - Golden Cross (Buy): Short MA crosses above Long MA
    - Death Cross (Sell): Short MA crosses below Long MA
    
    Common configurations:
    - Aggressive: short_window=5, long_window=20
    - Balanced: short_window=20, long_window=50 (default)
    - Conservative: short_window=50, long_window=200
    """
    
    def __init__(self, short_window=20, long_window=50):
        """
        Initialize the strategy with configurable moving average periods
        
        Args:
            short_window (int): Period for short-term moving average (default: 20)
            long_window (int): Period for long-term moving average (default: 50)
        """
        if short_window >= long_window:
            raise ValueError("short_window must be less than long_window")
            
        self.short_window = short_window
        self.long_window = long_window
        self.logger = get_logger(__name__, log_file_prefix="rule_based")
        
        self.logger.info(f"Initialized SMA Strategy: {short_window}-day vs {long_window}-day MA")

    def should_buy(self, data):
        """
        Check for Golden Cross (buy signal)
        Golden Cross: Short MA crosses above Long MA
        """
        if len(data) < self.long_window:
            self.logger.debug(f"Not enough data points. Need {self.long_window}, got {len(data)}")
            return False
            
        short_ma = data['close'].rolling(window=self.short_window).mean()
        long_ma = data['close'].rolling(window=self.long_window).mean()
        
        # Get the last two values for comparison
        if len(short_ma) < 2 or len(long_ma) < 2:
            self.logger.debug("Not enough data points after calculating moving averages")
            return False
            
        try:
            # Convert to Python scalars using .item()
            short_prev = float(short_ma.iloc[-2].item())
            short_curr = float(short_ma.iloc[-1].item())
            long_prev = float(long_ma.iloc[-2].item())
            long_curr = float(long_ma.iloc[-1].item())
            
            # Debug log the values
            self.logger.debug(f"Short MA ({self.short_window}d): Previous={short_prev:.2f}, Current={short_curr:.2f}")
            self.logger.debug(f"Long MA ({self.long_window}d): Previous={long_prev:.2f}, Current={long_curr:.2f}")
            self.logger.debug(f"Golden Cross Check: Previous (short < long): {short_prev < long_prev}, Current (short > long): {short_curr > long_curr}")
            
            # Golden Cross: Short MA crosses above Long MA
            # Previous: short < long (below)
            # Current: short > long (above)
            should_buy = short_prev < long_prev and short_curr > long_curr
            
            if should_buy:
                self.logger.info(f"🟢 GOLDEN CROSS: {self.short_window}d MA ({short_curr:.2f}) crossed above {self.long_window}d MA ({long_curr:.2f})")
            return should_buy
            
        except (AttributeError, ValueError) as e:
            self.logger.error(f"Error converting values: {e}")
            return False

    def should_sell(self, data):
        """
        Check for Death Cross (sell signal)
        Death Cross: Short MA crosses below Long MA
        """
        if len(data) < self.long_window:
            self.logger.debug(f"Not enough data points. Need {self.long_window}, got {len(data)}")
            return False
            
        short_ma = data['close'].rolling(window=self.short_window).mean()
        long_ma = data['close'].rolling(window=self.long_window).mean()
        
        # Get the last two values for comparison
        if len(short_ma) < 2 or len(long_ma) < 2:
            self.logger.debug("Not enough data points after calculating moving averages")
            return False
            
        try:
            # Convert to Python scalars using .item()
            short_prev = float(short_ma.iloc[-2].item())
            short_curr = float(short_ma.iloc[-1].item())
            long_prev = float(long_ma.iloc[-2].item())
            long_curr = float(long_ma.iloc[-1].item())
            
            # Debug log the values
            self.logger.debug(f"Short MA ({self.short_window}d): Previous={short_prev:.2f}, Current={short_curr:.2f}")
            self.logger.debug(f"Long MA ({self.long_window}d): Previous={long_prev:.2f}, Current={long_curr:.2f}")
            self.logger.debug(f"Death Cross Check: Previous (short > long): {short_prev > long_prev}, Current (short < long): {short_curr < long_curr}")
            
            # Death Cross: Short MA crosses below Long MA
            # Previous: short > long (above)
            # Current: short < long (below)
            should_sell = short_prev > long_prev and short_curr < long_curr
            
            if should_sell:
                self.logger.info(f"🔴 DEATH CROSS: {self.short_window}d MA ({short_curr:.2f}) crossed below {self.long_window}d MA ({long_curr:.2f})")
            return should_sell
            
        except (AttributeError, ValueError) as e:
            self.logger.error(f"Error converting values: {e}")
            return False 