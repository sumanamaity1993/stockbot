from .base import RuleBasedStrategy
import pandas as pd
import numpy as np
from logger import get_logger

class BollingerBandsStrategy(RuleBasedStrategy):
    """
    Bollinger Bands Strategy
    
    This strategy generates signals based on Bollinger Bands:
    - Buy Signal: Price touches or crosses below the lower band (oversold condition)
    - Sell Signal: Price touches or crosses above the upper band (overbought condition)
    - Additional: Band squeeze detection for volatility analysis
    
    Bollinger Bands consist of:
    - Middle Band: Simple Moving Average (SMA)
    - Upper Band: SMA + (Standard Deviation × Multiplier)
    - Lower Band: SMA - (Standard Deviation × Multiplier)
    """
    
    def __init__(self, period=20, std_dev=2, squeeze_threshold=0.1):
        """
        Initialize the Bollinger Bands strategy
        
        Args:
            period (int): Period for SMA calculation (default: 20)
            std_dev (float): Standard deviation multiplier (default: 2.0)
            squeeze_threshold (float): Threshold for band squeeze detection (default: 0.1)
        """
        if period <= 0 or std_dev <= 0 or squeeze_threshold <= 0:
            raise ValueError("All parameters must be positive")
            
        self.period = period
        self.std_dev = std_dev
        self.squeeze_threshold = squeeze_threshold
        self.logger = get_logger(__name__, log_file_prefix="rule_based")
        
        self.logger.info(f"Initialized Bollinger Bands Strategy: {period}-day SMA, Std Dev: {std_dev}, Squeeze Threshold: {squeeze_threshold}")

    def calculate_bollinger_bands(self, data):
        """Calculate Bollinger Bands for the given data"""
        if len(data) < self.period:
            return None, None, None
            
        # Calculate middle band (SMA)
        middle_band = data['close'].rolling(window=self.period).mean()
        
        # Calculate standard deviation
        std = data['close'].rolling(window=self.period).std()
        
        # Calculate upper and lower bands
        upper_band = middle_band + (std * self.std_dev)
        lower_band = middle_band - (std * self.std_dev)
        
        return upper_band, middle_band, lower_band

    def should_buy(self, data):
        """
        Check for buy signal: Price touches or crosses below the lower band
        """
        if len(data) < self.period + 1:
            self.logger.debug(f"Not enough data points. Need {self.period + 1}, got {len(data)}")
            return False
            
        upper_band, middle_band, lower_band = self.calculate_bollinger_bands(data)
        
        if upper_band is None or middle_band is None or lower_band is None:
            self.logger.debug("Could not calculate Bollinger Bands")
            return False
            
        # Get the last two values for comparison
        if len(upper_band) < 2:
            self.logger.debug("Not enough data points after calculating bands")
            return False
            
        try:
            # Convert to Python scalars using .item()
            price_prev = float(data['close'].iloc[-2].item())
            price_curr = float(data['close'].iloc[-1].item())
            lower_band_prev = float(lower_band.iloc[-2].item())
            lower_band_curr = float(lower_band.iloc[-1].item())
            
            # Debug log the values
            self.logger.debug(f"Bollinger Bands ({self.period}d): Price Previous={price_prev:.2f}, Current={price_curr:.2f}")
            self.logger.debug(f"Lower Band Previous={lower_band_prev:.2f}, Current={lower_band_curr:.2f}")
            
            # Buy signal: Price touches or crosses below the lower band
            # Previous: Price above lower band
            # Current: Price at or below lower band
            should_buy = (price_prev > lower_band_prev and price_curr <= lower_band_curr) or \
                        (price_curr <= lower_band_curr and price_curr >= lower_band_curr * 0.995)  # Within 0.5% of lower band
            
            if should_buy:
                self.logger.info(f"🟢 Bollinger Bands BUY: Price ({price_curr:.2f}) touched/crossed below lower band ({lower_band_curr:.2f})")
            return should_buy
            
        except (AttributeError, ValueError) as e:
            self.logger.error(f"Error converting values: {e}")
            return False

    def should_sell(self, data):
        """
        Check for sell signal: Price touches or crosses above the upper band
        """
        if len(data) < self.period + 1:
            self.logger.debug(f"Not enough data points. Need {self.period + 1}, got {len(data)}")
            return False
            
        upper_band, middle_band, lower_band = self.calculate_bollinger_bands(data)
        
        if upper_band is None or middle_band is None or lower_band is None:
            self.logger.debug("Could not calculate Bollinger Bands")
            return False
            
        # Get the last two values for comparison
        if len(upper_band) < 2:
            self.logger.debug("Not enough data points after calculating bands")
            return False
            
        try:
            # Convert to Python scalars using .item()
            price_prev = float(data['close'].iloc[-2].item())
            price_curr = float(data['close'].iloc[-1].item())
            upper_band_prev = float(upper_band.iloc[-2].item())
            upper_band_curr = float(upper_band.iloc[-1].item())
            
            # Debug log the values
            self.logger.debug(f"Bollinger Bands ({self.period}d): Price Previous={price_prev:.2f}, Current={price_curr:.2f}")
            self.logger.debug(f"Upper Band Previous={upper_band_prev:.2f}, Current={upper_band_curr:.2f}")
            
            # Sell signal: Price touches or crosses above the upper band
            # Previous: Price below upper band
            # Current: Price at or above upper band
            should_sell = (price_prev < upper_band_prev and price_curr >= upper_band_curr) or \
                         (price_curr >= upper_band_curr and price_curr <= upper_band_curr * 1.005)  # Within 0.5% of upper band
            
            if should_sell:
                self.logger.info(f"🔴 Bollinger Bands SELL: Price ({price_curr:.2f}) touched/crossed above upper band ({upper_band_curr:.2f})")
            return should_sell
            
        except (AttributeError, ValueError) as e:
            self.logger.error(f"Error converting values: {e}")
            return False

    def detect_band_squeeze(self, data):
        """
        Detect if Bollinger Bands are in a squeeze (low volatility)
        Returns True if bands are squeezed, False otherwise
        """
        if len(data) < self.period:
            return False
            
        upper_band, middle_band, lower_band = self.calculate_bollinger_bands(data)
        
        if upper_band is None or middle_band is None or lower_band is None:
            return False
            
        try:
            # Calculate band width as percentage of middle band
            band_width = ((upper_band.iloc[-1] - lower_band.iloc[-1]) / middle_band.iloc[-1]) * 100
            
            # Check if bands are squeezed (narrow width)
            is_squeezed = band_width < self.squeeze_threshold
            
            if is_squeezed:
                self.logger.info(f"📊 Bollinger Bands SQUEEZE detected: Band width = {band_width:.2f}% (threshold: {self.squeeze_threshold}%)")
            
            return is_squeezed
            
        except (AttributeError, ValueError) as e:
            self.logger.error(f"Error detecting band squeeze: {e}")
            return False

    def get_band_values(self, data):
        """
        Get current Bollinger Bands values for analysis
        Returns dict with upper, middle, lower bands and current price
        """
        if len(data) < self.period:
            return None
            
        upper_band, middle_band, lower_band = self.calculate_bollinger_bands(data)
        
        if upper_band is None or middle_band is None or lower_band is None:
            return None
            
        try:
            current_price = float(data['close'].iloc[-1].item())
            upper = float(upper_band.iloc[-1].item())
            middle = float(middle_band.iloc[-1].item())
            lower = float(lower_band.iloc[-1].item())
            
            return {
                'current_price': current_price,
                'upper_band': upper,
                'middle_band': middle,
                'lower_band': lower,
                'band_width': ((upper - lower) / middle) * 100
            }
            
        except (AttributeError, ValueError) as e:
            self.logger.error(f"Error getting band values: {e}")
            return None
