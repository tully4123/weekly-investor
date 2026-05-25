# Weekly Investor

Automated weekly stock pick + daily morning updates, delivered to your email.

## What it does

| Schedule | Action |
|---|---|
| Every Sunday 6 PM ET | Scans ~45 stocks, ETFs, crypto, and commodities. Scores them on momentum, RSI, trend, volume, and 52-week position. Emails the top pick with full thesis. |
| Mon–Fri 8 AM ET | Emails the current pick's price, % change, since-pick return, and latest news. |

## Setup (one-time, ~10 minutes)

### 1. Create a Gmail App Password

You need this so the script can send email without your real password.

1. Go to your Google Account → **Security** → enable **2-Step Verification** (if not already on)
2. Then go to **Security** → **App passwords**
3. Choose app: **Mail**, device: **Other** → name it "Weekly Investor"
4. Copy the 16-character password shown

### 2. Push this repo to GitHub

```bash
git init
git add .
git commit -m "initial commit"
# Create a new repo at github.com/new, then:
git remote add origin https://github.com/YOUR_USERNAME/weekly-investor.git
git push -u origin main
```

### 3. Add GitHub Secrets

Go to your repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add these three secrets:

| Name | Value |
|---|---|
| `EMAIL_FROM` | `tully4123@gmail.com` |
| `EMAIL_TO` | `tully4123@gmail.com` |
| `EMAIL_PASSWORD` | The 16-char App Password from step 1 |

### 4. Enable Actions

Go to your repo → **Actions** tab → click **"I understand my workflows, go ahead and enable them"**

That's it. The first weekly email will arrive next Sunday at 6 PM ET.

## Run manually (optional)

You can trigger either workflow anytime:
- Go to **Actions** → select the workflow → **Run workflow**

Or run locally:

```bash
pip install -r requirements.txt
export EMAIL_FROM="tully4123@gmail.com"
export EMAIL_TO="tully4123@gmail.com"
export EMAIL_PASSWORD="your-app-password"
python weekly_scan.py   # full scan + email
python daily_update.py  # daily update email
```

## Customize the watchlist

Edit `config.py` to add/remove assets from any category:

```python
WATCHLIST = {
    "stocks":     ["AAPL", "MSFT", ...],
    "etfs":       ["SPY", "QQQ", ...],
    "crypto":     {"Bitcoin": "BTC-USD", ...},
    "commodities":{"Gold": "GC=F", ...},
}
```

## How scoring works (out of 100)

| Factor | Max pts | Notes |
|---|---|---|
| Weekly momentum | 25 | Rewards +2–5% gains; penalises sharp drops |
| RSI position | 20 | Sweet spot 45–65; oversold gets 15 pts |
| Trend vs MAs | 25 | Price > 50d > 200d = full 25 |
| Volume vs 20d avg | 15 | 1.5× average = full 15 |
| 52-week range position | 15 | Mid-range (25–60%) = full 15 |

Assets with RSI > 78 are deprioritised unless everything is overbought.
