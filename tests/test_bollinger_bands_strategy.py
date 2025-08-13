import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import pandas as pd
import numpy as np
from trader.rule_based.strategies.bollinger_bands_strategy import BollingerBandsStrategy

class TestBollingerBandsStrategy(unittest.TestCase):
    
    def setUp(self):
        """Set up test data"""
        # Create sample price data
        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        np.random.seed(42)  # For reproducible results
        
        # Generate realistic price data with some volatility
        base_price = 100
        returns = np.random.normal(0, 0.02, 50)  # 2% daily volatility
        prices = [base_price]
        
        for ret in returns[1:]:
            new_price = prices[-1] * (1 + ret)
            prices.append(new_price)
        
        self.data = pd.DataFrame({
            'close': prices,
            'open': [p * 0.99 for p in prices],  # Slightly lower open
            'high': [p * 1.02 for p in prices],  # Slightly higher high
            'low': [p * 0.98 for p in prices],   # Slightly lower low
            'volume': np.random.randint(1000000, 10000000, 50)
        }, index=dates)
        
        self.strategy = BollingerBandsStrategy(period=20, std_dev=2.0, squeeze_threshold=0.15)
    
    def test_strategy_initialization(self):
        """Test strategy initialization"""
        self.assertEqual(self.strategy.period, 20)
        self.assertEqual(self.strategy.std_dev, 2.0)
        self.assertEqual(self.strategy.squeeze_threshold, 0.15)
    
    def test_calculate_bollinger_bands(self):
        """Test Bollinger Bands calculation"""
        upper, middle, lower = self.strategy.calculate_bollinger_bands(self.data)
        
        # Check that bands are calculated
        self.assertIsNotNone(upper)
        self.assertIsNotNone(middle)
        self.assertIsNotNone(lower)
        
        # Check that upper > middle > lower (only for non-NaN values)
        valid_mask = ~(upper.isna() | middle.isna() | lower.isna())
        if valid_mask.any():
            self.assertTrue(all(upper[valid_mask] >= middle[valid_mask]))
            self.assertTrue(all(middle[valid_mask] >= lower[valid_mask]))
        
        # Check that bands have correct length
        self.assertEqual(len(upper), len(self.data))
        self.assertEqual(len(middle), len(self.data))
        self.assertEqual(len(lower), len(self.data))
        
        # Check that we have some valid values after the initial period
        self.assertTrue(valid_mask.sum() > 0, "Should have valid values after initial period")
    
    def test_insufficient_data(self):
        """Test behavior with insufficient data"""
        short_data = self.data.head(10)  # Less than period (20)
        
        # Should return None for all bands
        upper, middle, lower = self.strategy.calculate_bollinger_bands(short_data)
        self.assertIsNone(upper)
        self.assertIsNone(middle)
        self.assertIsNone(lower)
        
        # Should return False for signals
        self.assertFalse(self.strategy.should_buy(short_data))
        self.assertFalse(self.strategy.should_buy(short_data))
    
    def test_band_squeeze_detection(self):
        """Test band squeeze detection"""
        # Create data with very low volatility (squeezed bands)
        squeezed_data = self.data.copy()
        squeezed_data['close'] = 100 + np.random.normal(0, 0.001, 50)  # Very low volatility
        
        is_squeezed = self.strategy.detect_band_squeeze(squeezed_data)
        # Should detect squeeze due to very low volatility
        self.assertTrue(is_squeezed)
    
    def test_get_band_values(self):
        """Test getting current band values"""
        band_values = self.strategy.get_band_values(self.data)
        
        self.assertIsNotNone(band_values)
        self.assertIn('current_price', band_values)
        self.assertIn('upper_band', band_values)
        self.assertIn('middle_band', band_values)
        self.assertIn('lower_band', band_values)
        self.assertIn('band_width', band_values)
        
        # Check that values are numeric
        self.assertIsInstance(band_values['current_price'], float)
        self.assertIsInstance(band_values['upper_band'], float)
        self.assertIsInstance(band_values['middle_band'], float)
        self.assertIsInstance(band_values['lower_band'], float)
        self.assertIsInstance(band_values['band_width'], float)
    
    def test_invalid_parameters(self):
        """Test strategy with invalid parameters"""
        with self.assertRaises(ValueError):
            BollingerBandsStrategy(period=0, std_dev=2.0, squeeze_threshold=0.15)
        
        with self.assertRaises(ValueError):
            BollingerBandsStrategy(period=20, std_dev=0, squeeze_threshold=0.15)
        
        with self.assertRaises(ValueError):
            BollingerBandsStrategy(period=20, std_dev=2.0, squeeze_threshold=0)
    
    def test_signal_generation_edge_cases(self):
        """Test signal generation with edge cases"""
        # Test with exactly period + 1 data points
        edge_data = self.data.head(21)  # Exactly 21 points for period=20
        
        # Should not crash
        try:
            buy_signal = self.strategy.should_buy(edge_data)
            sell_signal = self.strategy.should_sell(edge_data)
            # Just checking it doesn't crash, actual signals depend on data
        except Exception as e:
            self.fail(f"Signal generation failed with edge case data: {e}")

if __name__ == '__main__':
    unittest.main()
