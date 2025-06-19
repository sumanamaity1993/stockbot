import yfinance as yf
import pandas as pd

def fetch_ohlc(symbol, interval='1d', period='6mo'):
    """
    Fetch OHLC data for a symbol using yfinance.
    Returns a pandas DataFrame with columns: ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
    """
    df = yf.download(symbol, interval=interval, period=period)
    df = df.reset_index()
    df.rename(columns={
        'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume', 'Date': 'date'
    }, inplace=True)
    return df[['date', 'open', 'high', 'low', 'close', 'volume']] 