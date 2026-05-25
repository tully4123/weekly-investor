import pandas as pd
import numpy as np
from market_data import fetch_asset


# ── Technical indicators ──────────────────────────────────────────────────────

def _rsi(prices: pd.Series, period: int = 14) -> float:
    delta = prices.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss
    series = 100 - (100 / (1 + rs))
    return float(series.iloc[-1])


def _sma(prices: pd.Series, period: int) -> float | None:
    if len(prices) < period:
        return None
    return float(prices.rolling(period).mean().iloc[-1])


def _vol_ratio(volume: pd.Series, window: int = 20) -> float:
    avg = volume.rolling(window).mean().iloc[-1]
    return float(volume.iloc[-1] / avg) if avg > 0 else 1.0


# ── Scoring ───────────────────────────────────────────────────────────────────

def _score(metrics: dict) -> int:
    score = 0

    # 1. Weekly momentum (0–25)
    wr = metrics.get("week_return", 0)
    if wr > 5:      score += 25
    elif wr > 2:    score += 20
    elif wr > 0:    score += 15
    elif wr > -2:   score += 8
    # else 0

    # 2. RSI sweet spot 45–65 (0–20)
    rsi = metrics.get("rsi", 50)
    if 45 <= rsi <= 65:   score += 20
    elif 35 <= rsi < 45:  score += 15   # oversold recovery
    elif 65 < rsi <= 75:  score += 10   # strong but watch it
    elif rsi < 35:        score += 8    # deeply oversold / contrarian
    else:                 score += 3    # overbought >75

    # 3. Trend vs moving averages (0–25)
    price = metrics.get("current_price", 0)
    ma50  = metrics.get("ma50")
    ma200 = metrics.get("ma200")
    if ma50 and ma200:
        if price > ma50 > ma200:    score += 25  # golden setup
        elif price > ma50:          score += 18
        elif price > ma200:         score += 12
        # else 0
    elif ma50:
        score += (15 if price > ma50 else 5)

    # 4. Volume confirmation (0–15)
    vr = metrics.get("volume_ratio", 1.0)
    if vr > 1.5:    score += 15
    elif vr > 1.2:  score += 10
    elif vr >= 0.8: score += 8
    else:           score += 4

    # 5. Position in 52-week range (0–15) — mid-range sweet spot
    hi = metrics.get("high_52w")
    lo = metrics.get("low_52w")
    if hi and lo and hi > lo:
        pos = (price - lo) / (hi - lo)
        if pos < 0.25:          score += 13   # near lows — max upside
        elif pos <= 0.60:       score += 15   # mid-range — sweet spot
        elif pos <= 0.80:       score += 10
        else:                   score += 5    # near highs

    return score


# ── Main analysis function ────────────────────────────────────────────────────

def analyze_asset(symbol: str, asset_type: str, display_name: str | None = None) -> dict | None:
    raw = fetch_asset(symbol, period="1y")
    if raw is None:
        return None

    hist  = raw["history"]
    info  = raw["info"]
    news  = raw["news"]
    close = hist["Close"]
    vol   = hist["Volume"]

    if len(close) < 20:
        return None

    current_price  = float(close.iloc[-1])
    week_ago       = float(close.iloc[-6])  if len(close) >= 6  else float(close.iloc[0])
    month_ago      = float(close.iloc[-22]) if len(close) >= 22 else float(close.iloc[0])

    week_return  = (current_price - week_ago)  / week_ago  * 100
    month_return = (current_price - month_ago) / month_ago * 100

    rsi  = _rsi(close)
    ma20 = _sma(close, 20)
    ma50 = _sma(close, 50)
    ma200= _sma(close, 200)
    vr   = _vol_ratio(vol)

    n = min(252, len(close))
    high_52w = float(close.tail(n).max())
    low_52w  = float(close.tail(n).min())

    # Fundamentals (meaningful only for stocks)
    pe_ratio   = info.get("trailingPE") or info.get("forwardPE")
    market_cap = info.get("marketCap")
    sector     = info.get("sector", "")
    name       = display_name or info.get("longName") or info.get("shortName") or symbol

    metrics = dict(
        symbol        = symbol,
        name          = name,
        asset_type    = asset_type,
        current_price = current_price,
        week_return   = week_return,
        month_return  = month_return,
        rsi           = rsi,
        ma20          = ma20,
        ma50          = ma50,
        ma200         = ma200,
        volume_ratio  = vr,
        high_52w      = high_52w,
        low_52w       = low_52w,
        pe_ratio      = pe_ratio,
        market_cap    = market_cap,
        sector        = sector,
        news          = news,
    )
    metrics["score"] = _score(metrics)
    return metrics


# ── Narrative generation ──────────────────────────────────────────────────────

def generate_thesis(d: dict) -> str:
    parts = []
    name  = d.get("name", d["symbol"])
    wr    = d.get("week_return", 0)
    mr    = d.get("month_return", 0)
    rsi   = d.get("rsi", 50)
    price = d["current_price"]
    ma50  = d.get("ma50")
    ma200 = d.get("ma200")
    vr    = d.get("volume_ratio", 1.0)
    hi    = d.get("high_52w")
    lo    = d.get("low_52w")

    # Momentum
    if wr > 5:
        parts.append(f"{name} surged {wr:.1f}% this week, showing strong near-term momentum")
    elif wr > 2:
        parts.append(f"{name} gained {wr:.1f}% this week, building positive price action")
    elif wr > 0:
        parts.append(f"{name} edged up {wr:.1f}% this week with quiet accumulation")
    elif wr > -3:
        parts.append(f"{name} pulled back {abs(wr):.1f}% this week, offering a potential entry point")
    else:
        parts.append(f"{name} declined {abs(wr):.1f}% this week, but technicals hint at a potential reversal")

    # RSI
    if 45 <= rsi <= 65:
        parts.append(f"RSI of {rsi:.0f} sits in the ideal momentum zone — not overbought, not oversold")
    elif rsi < 40:
        parts.append(f"RSI of {rsi:.0f} signals oversold territory, historically a mean-reversion opportunity")
    elif rsi > 70:
        parts.append(f"RSI of {rsi:.0f} confirms strong demand, though extended readings warrant some caution")

    # Trend
    if ma50 and ma200:
        if price > ma50 > ma200:
            parts.append(
                f"it trades above both its 50-day (${ma50:.2f}) and 200-day (${ma200:.2f}) moving averages — a classically bullish alignment"
            )
        elif price > ma50:
            parts.append(f"price is above the 50-day MA (${ma50:.2f}), working to reclaim the 200-day (${ma200:.2f})")
        elif price > ma200:
            parts.append(f"holding long-term support at the 200-day MA (${ma200:.2f}) while the 50-day (${ma50:.2f}) acts as near-term resistance")

    # Volume
    if vr > 1.4:
        parts.append(f"volume is running {vr:.1f}× above average, signalling institutional interest")

    # 52-week position
    if hi and lo and hi > lo:
        pos = (price - lo) / (hi - lo)
        if pos < 0.30:
            parts.append(f"near its 52-week low of ${lo:.2f}, offering asymmetric upside if a floor holds")
        elif pos <= 0.60:
            parts.append(f"sitting in the middle of its 52-week range (${lo:.2f}–${hi:.2f}), with meaningful room to run")

    # Monthly context
    if mr > 12:
        parts.append(f"the {mr:.1f}% monthly gain reflects a sustained trend worth riding")
    elif mr < -12:
        parts.append(f"the {abs(mr):.1f}% monthly pullback may have created a value window")

    return ". ".join(parts) + "."


def generate_risks(d: dict) -> list[str]:
    risks = []
    rsi   = d.get("rsi", 50)
    wr    = d.get("week_return", 0)
    price = d["current_price"]
    ma200 = d.get("ma200")
    atype = d.get("asset_type", "stock")

    if rsi > 72:
        risks.append(f"RSI of {rsi:.0f} is elevated — a short-term pullback is plausible before the next leg up")
    if wr > 8:
        risks.append("A sharp weekly gain may attract profit-taking at the open Monday")
    if ma200 and price < ma200:
        risks.append(f"Price is below the 200-day MA (${ma200:.2f}), indicating the longer-term trend is still down")
    if atype == "crypto":
        risks.append("Crypto markets can move 10–20% in a single session on news or sentiment shifts")
        risks.append("Regulatory headlines remain an unpredictable tail risk for digital assets")
    if wr < -5:
        risks.append("Negative weekly momentum may persist before stabilising — consider scaling in rather than going all in")
    risks.append("With $100/week, consistency over time matters more than nailing perfect entry prices")
    return risks[:4]
