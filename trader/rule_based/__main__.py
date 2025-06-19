import os
from trader.rule_based.config import RULE_BASED_CONFIG
from trader.rule_based.engine import RuleBasedEngine

def main():
    engine = RuleBasedEngine(config=RULE_BASED_CONFIG)
    engine.run()

if __name__ == "__main__":
    main() 