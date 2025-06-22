from abc import ABC, abstractmethod

class RuleBasedStrategy(ABC):
    @abstractmethod
    def should_buy(self, data):
        pass

    @abstractmethod
    def should_sell(self, data):
        pass
    
    def generate_signal(self, data):
        """
        Generate trading signal based on strategy logic
        
        Args:
            data: Price data DataFrame
            
        Returns:
            str: 'buy', 'sell', or 'hold'
        """
        if self.should_buy(data):
            return 'buy'
        elif self.should_sell(data):
            return 'sell'
        else:
            return 'hold' 