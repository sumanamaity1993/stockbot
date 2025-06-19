from abc import ABC, abstractmethod

class RuleBasedStrategy(ABC):
    @abstractmethod
    def should_buy(self, data):
        pass

    @abstractmethod
    def should_sell(self, data):
        pass 