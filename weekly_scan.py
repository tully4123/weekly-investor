"""
Weekly market scanner — runs every Sunday evening.
Scores all watchlist assets and emails the top pick.
"""

import json
import subprocess
from datetime import date
from config import WATCHLIST, EMAIL_TO
from analysis import analyze_asset
from email_utils import build_weekly_html, send_email


def run():
    print(f"=== Weekly Scan — {date.today()} ===\n")
    candidates = []

    for symbol in WATCHLIST["stocks"]:
        print(f"  stock    {symbol}")
        r = analyze_asset(symbol, "stock")
        if r:
            candidates.append(r)

    for symbol in WATCHLIST["etfs"]:
        print(f"  etf      {symbol}")
        r = analyze_asset(symbol, "etf")
        if r:
            candidates.append(r)

    for name, symbol in WATCHLIST["commodities"].items():
        print(f"  commodity {name}")
        r = analyze_asset(symbol, "commodity", display_name=name)
        if r:
            candidates.append(r)

    for name, symbol in WATCHLIST["crypto"].items():
        print(f"  crypto   {name}")
        r = analyze_asset(symbol, "crypto", display_name=name)
        if r:
            candidates.append(r)

    if not candidates:
        print("ERROR: No candidates returned — check network / yfinance.")
        return

    candidates.sort(key=lambda x: x["score"], reverse=True)

    # Prefer assets not severely overbought unless everything is
    filtered = [c for c in candidates if c.get("rsi", 50) <= 78]
    pick = (filtered or candidates)[0]

    # Persist the pick so daily_update.py can reference it
    state = {
        "symbol":       pick["symbol"],
        "name":         pick.get("name", pick["symbol"]),
        "asset_type":   pick["asset_type"],
        "price_at_pick": pick["current_price"],
        "week_picked":  str(date.today()),
        "score":        pick["score"],
    }
    with open("current_pick.json", "w") as f:
        json.dump(state, f, indent=2)

    # Commit the updated pick back to the repo (GitHub Actions has write token)
    try:
        subprocess.run(["git", "config", "user.email", "actions@github.com"], check=False)
        subprocess.run(["git", "config", "user.name", "Weekly Investor Bot"], check=False)
        subprocess.run(["git", "add", "current_pick.json"], check=False)
        subprocess.run(["git", "commit", "-m", f"pick: {pick['symbol']} week of {date.today()}"], check=False)
        subprocess.run(["git", "push"], check=False)
    except Exception as e:
        print(f"  [WARN] git commit/push failed: {e}")

    print(f"\nPICK: {pick['symbol']} | score {pick['score']}/100 | "
          f"week {pick.get('week_return',0):+.1f}% | RSI {pick.get('rsi',0):.0f}\n")

    subject = f"📊 Weekly Pick: {pick['symbol']} — {date.today().strftime('%b %d, %Y')}"
    html = build_weekly_html(pick, candidates[:10])
    send_email(subject, html, EMAIL_TO)
    print("Done.")


if __name__ == "__main__":
    run()
