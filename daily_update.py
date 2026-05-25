"""
Daily morning update — runs Mon–Fri at 8 AM ET.
Fetches the current pick and emails a price + news summary.
"""

import json
from datetime import date, datetime
import yfinance as yf
from config import EMAIL_TO
from market_data import fetch_asset, fetch_premarket
from email_utils import build_daily_html, send_email, _fmt_pct


def run():
    print(f"=== Daily Update — {date.today()} ===\n")

    try:
        with open("current_pick.json") as f:
            state = json.load(f)
    except FileNotFoundError:
        print("No current_pick.json found — run weekly_scan.py first.")
        return

    symbol     = state["symbol"]
    asset_type = state["asset_type"]
    pick_price = state["price_at_pick"]
    week_picked = state["week_picked"]

    print(f"  Fetching {symbol} ({asset_type})...")
    raw = fetch_asset(symbol, period="5d")
    if raw is None:
        print(f"  ERROR: Could not fetch data for {symbol}")
        return

    hist  = raw["history"]
    news  = raw["news"]
    close = hist["Close"]

    if len(close) < 1:
        print("  ERROR: Empty history")
        return

    current_price = float(close.iloc[-1])
    prev_close    = float(close.iloc[-2]) if len(close) >= 2 else current_price
    day_change    = (current_price - prev_close) / prev_close * 100
    since_change  = (current_price - pick_price)  / pick_price  * 100

    # Pre-market price (may be None if markets not yet open or no pre-market data)
    premarket = fetch_premarket(symbol)

    update = {
        "symbol":            symbol,
        "name":              state.get("name", symbol),
        "asset_type":        asset_type,
        "current_price":     current_price,
        "day_change":        day_change,
        "since_pick_change": since_change,
        "pick_price":        pick_price,
        "week_picked":       week_picked,
        "premarket_price":   premarket,
        "news":              news,
        "today":             datetime.now().strftime("%A, %B %d, %Y"),
    }

    sign  = "+" if day_change >= 0 else ""
    emoji = "🟢" if day_change >= 0 else "🔴"
    subject = (
        f"{emoji} {symbol} Morning Update — "
        f"{sign}{day_change:.2f}% | {_fmt_pct(since_change)} since pick"
    )

    html = build_daily_html(update)
    send_email(subject, html, EMAIL_TO)

    print(f"  {symbol}: today {sign}{day_change:.2f}% | since pick {since_change:+.2f}%")
    print("Done.")


if __name__ == "__main__":
    run()
