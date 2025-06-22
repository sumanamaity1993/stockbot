# Tests Directory

This directory contains all test files for the StockBot project.

## Test Files

### Core Functionality Tests
- **`test_all_fetchers.py`** - Tests all data fetchers (yfinance, Alpha Vantage, Polygon)
- **`test_enhanced_fetcher.py`** - Tests the enhanced data fetcher with quality analysis
- **`test_alpha_vantage.py`** - Specific tests for Alpha Vantage API integration

### Engine Tests
- **`test_configurable_engine.py`** - Tests the configurable engine system
- **`test_multi_source_db.py`** - Tests multi-source database operations

## Running Tests

```bash
# Run all tests
python tests/test_all_fetchers.py

# Run specific test
python tests/test_enhanced_fetcher.py
```

## Test Coverage

- ✅ Data fetching from multiple sources
- ✅ Data quality analysis
- ✅ Database operations
- ✅ Engine configurations
- ✅ Strategy evaluations 