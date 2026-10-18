import numpy as np
import pandas as pd
from qannas.strategy import analyze


def test_strategy_returns_signal_or_none_without_mt5():
    n = 120
    close = np.linspace(2300, 2350, n) + np.sin(np.arange(n))
    df = pd.DataFrame({"Open": close - .2, "High": close + 1, "Low": close - 1, "Close": close}, index=pd.date_range("2026-01-01", periods=n, freq="15min"))
    result = analyze(df, min_confidence=60)
    assert result is None or result.side in {"BUY", "SELL"}
