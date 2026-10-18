from __future__ import annotations

from dataclasses import dataclass
import math
import pandas as pd


@dataclass
class Signal:
    side: str
    entry: float
    stop: float
    target: float
    confidence: int
    reasons: list[str]
    candle_time: str


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    rs = gain / loss.replace(0, pd.NA)
    return 100 - (100 / (1 + rs))


def _atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    prev = df["Close"].shift(1)
    tr = pd.concat([(df["High"] - df["Low"]), (df["High"] - prev).abs(), (df["Low"] - prev).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def analyze(df: pd.DataFrame, pip_size: float = 0.10, rr: float = 2.0,
            atr_mult: float = 1.5, min_confidence: int = 60) -> Signal | None:
    if df is None or len(df) < 60:
        return None
    df = df.copy().dropna(subset=["Open", "High", "Low", "Close"])
    df["ema20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["ema50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["rsi"] = _rsi(df["Close"])
    df["macd"] = df["Close"].ewm(span=12, adjust=False).mean() - df["Close"].ewm(span=26, adjust=False).mean()
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["atr"] = _atr(df)
    row = df.iloc[-2]  # last fully closed candle
    prior = df.iloc[-3]
    close = float(row["Close"])
    atr = float(row["atr"])
    if not math.isfinite(atr) or atr <= 0:
        return None

    long_score = 0
    short_score = 0
    long_reasons, short_reasons = [], []
    if row.ema20 > row.ema50:
        long_score += 25; long_reasons.append("الاتجاه صاعد EMA20 فوق EMA50")
    if row.ema20 < row.ema50:
        short_score += 25; short_reasons.append("الاتجاه هابط EMA20 تحت EMA50")
    if 50 <= row.rsi <= 72:
        long_score += 20; long_reasons.append(f"RSI داعم للشراء {row.rsi:.1f}")
    if 28 <= row.rsi <= 50:
        short_score += 20; short_reasons.append(f"RSI داعم للبيع {row.rsi:.1f}")
    if row.macd > row.macd_signal and prior.macd <= prior.macd_signal:
        long_score += 30; long_reasons.append("تقاطع MACD صاعد")
    elif row.macd > row.macd_signal:
        long_score += 15; long_reasons.append("MACD فوق خط الإشارة")
    if row.macd < row.macd_signal and prior.macd >= prior.macd_signal:
        short_score += 30; short_reasons.append("تقاطع MACD هابط")
    elif row.macd < row.macd_signal:
        short_score += 15; short_reasons.append("MACD تحت خط الإشارة")
    if close > row.ema20:
        long_score += 15; long_reasons.append("الإغلاق فوق EMA20")
    if close < row.ema20:
        short_score += 15; short_reasons.append("الإغلاق تحت EMA20")

    if long_score >= min_confidence and long_score > short_score:
        stop = close - atr * atr_mult
        target = close + (close - stop) * rr
        side, confidence, reasons = "BUY", min(long_score, 95), long_reasons
    elif short_score >= min_confidence and short_score > long_score:
        stop = close + atr * atr_mult
        target = close - (stop - close) * rr
        side, confidence, reasons = "SELL", min(short_score, 95), short_reasons
    else:
        return None

    def round_price(x: float) -> float:
        return round(round(x / pip_size) * pip_size, 2)
    return Signal(side, round_price(close), round_price(stop), round_price(target), confidence, reasons, str(df.index[-2]))
