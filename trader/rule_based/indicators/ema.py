import pandas as pd

def compute_ema(series, span):
    return series.ewm(span=span, adjust=False).mean() 