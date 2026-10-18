from __future__ import annotations

import os
import httpx
import pandas as pd
import yfinance as yf


def fetch_yfinance(period: str, interval: str) -> pd.DataFrame:
    symbols = [os.getenv("YF_SYMBOL", "XAUUSD=X"), os.getenv("YF_FALLBACK_SYMBOL", "GC=F")]
    for symbol in symbols:
        try:
            df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=False, threads=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            required = {"Open", "High", "Low", "Close"}
            if not df.empty and required.issubset(df.columns):
                return df[list(required)]
        except Exception:
            continue
    return pd.DataFrame()


def fetch_twelvedata(interval: str) -> pd.DataFrame:
    key = os.getenv("TWELVEDATA_API_KEY", "")
    if not key:
        return pd.DataFrame()
    r = httpx.get("https://api.twelvedata.com/time_series", params={"symbol": os.getenv("TWELVEDATA_SYMBOL", "XAU/USD"), "interval": interval, "outputsize": 300, "apikey": key}, timeout=30)
    r.raise_for_status()
    values = r.json().get("values", [])
    df = pd.DataFrame(values)
    if df.empty:
        return df
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.set_index("datetime").sort_index()
    return df.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close"}).astype(float)


def fetch_data() -> pd.DataFrame:
    provider = os.getenv("DATA_PROVIDER", "yfinance").lower()
    interval = os.getenv("TIMEFRAME", "15m")
    if provider == "twelvedata":
        return fetch_twelvedata(interval)
    return fetch_yfinance(os.getenv("LOOKBACK_PERIOD", "5d"), interval)
