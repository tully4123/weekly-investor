import yfinance as yf
import pandas as pd


def fetch_asset(symbol: str, period: str = "1y") -> dict | None:
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, auto_adjust=True)
        if hist.empty or len(hist) < 20:
            return None
        info = {}
        try:
            info = ticker.info or {}
        except Exception:
            pass
        news = []
        try:
            news = ticker.news[:6] if ticker.news else []
        except Exception:
            pass
        return {"symbol": symbol, "history": hist, "info": info, "news": news}
    except Exception as e:
        print(f"  [WARN] {symbol}: {e}")
        return None


def fetch_premarket(symbol: str) -> float | None:
    """Return pre-market price if available, else None."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d", interval="1m", prepost=True, auto_adjust=True)
        if hist.empty:
            return None
        return float(hist["Close"].iloc[-1])
    except Exception:
        return None
