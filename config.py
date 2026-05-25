import os

WATCHLIST = {
    "stocks": [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA",
        "JPM", "V", "WMT", "HD", "XOM", "BAC", "JNJ",
        "NFLX", "AMD", "PLTR", "COIN", "UBER", "SHOP",
    ],
    "etfs": [
        "SPY", "QQQ", "IWM", "VTI", "GLD", "SLV", "USO",
        "XLK", "XLF", "XLE", "ARKK", "SOXX", "SCHD",
    ],
    "crypto": {
        "Bitcoin":   "BTC-USD",
        "Ethereum":  "ETH-USD",
        "Solana":    "SOL-USD",
        "Avalanche": "AVAX-USD",
        "Chainlink": "LINK-USD",
        "Dogecoin":  "DOGE-USD",
    },
    "commodities": {
        "Gold":        "GC=F",
        "Silver":      "SI=F",
        "Crude Oil":   "CL=F",
        "Natural Gas": "NG=F",
    },
}

EMAIL_FROM = os.environ.get("EMAIL_FROM", "tully4123@gmail.com")
EMAIL_TO   = os.environ.get("EMAIL_TO",   "tully4123@gmail.com")
EMAIL_PASS = os.environ.get("EMAIL_PASSWORD", "")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT   = 587
