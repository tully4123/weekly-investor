import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date
from config import EMAIL_FROM, EMAIL_PASS, SMTP_SERVER, SMTP_PORT
from analysis import generate_thesis, generate_risks


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fmt_price(v) -> str:
    if v is None:
        return "N/A"
    return f"${v:,.2f}"


def _fmt_pct(v, decimals=2) -> str:
    if v is None:
        return "N/A"
    sign = "+" if v >= 0 else ""
    return f"{sign}{v:.{decimals}f}%"


def _fmt_cap(v) -> str:
    if v is None:
        return "N/A"
    if v >= 1e12:
        return f"${v/1e12:.2f}T"
    if v >= 1e9:
        return f"${v/1e9:.2f}B"
    if v >= 1e6:
        return f"${v/1e6:.2f}M"
    return f"${v:,.0f}"


def _badge_color(asset_type: str) -> str:
    return {
        "stock":     "#2563eb",
        "etf":       "#7c3aed",
        "crypto":    "#d97706",
        "commodity": "#059669",
    }.get(asset_type, "#6b7280")


def _pct_color(v) -> str:
    if v is None:
        return "#6b7280"
    return "#16a34a" if v >= 0 else "#dc2626"


def _52w_bar(price, lo, hi) -> str:
    if not lo or not hi or hi <= lo:
        return ""
    pct = int((price - lo) / (hi - lo) * 100)
    pct = max(0, min(100, pct))
    return f"""
    <div style="margin:4px 0;">
      <div style="display:flex;justify-content:space-between;font-size:11px;color:#6b7280;">
        <span>{_fmt_price(lo)}</span><span>52-wk range</span><span>{_fmt_price(hi)}</span>
      </div>
      <div style="background:#e5e7eb;border-radius:4px;height:6px;margin-top:3px;">
        <div style="background:#2563eb;width:{pct}%;height:6px;border-radius:4px;"></div>
      </div>
    </div>"""


# ── Weekly email ──────────────────────────────────────────────────────────────

def build_weekly_html(pick: dict, top10: list) -> str:
    thesis = generate_thesis(pick)
    risks  = generate_risks(pick)

    badge_col  = _badge_color(pick["asset_type"])
    week_col   = _pct_color(pick.get("week_return"))
    month_col  = _pct_color(pick.get("month_return"))
    atype_label = pick["asset_type"].upper()

    ma50_str  = _fmt_price(pick.get("ma50"))
    ma200_str = _fmt_price(pick.get("ma200"))
    ma50_diff = ((pick["current_price"] - pick["ma50"]) / pick["ma50"] * 100) if pick.get("ma50") else None
    ma200_diff= ((pick["current_price"] - pick["ma200"]) / pick["ma200"] * 100) if pick.get("ma200") else None

    bar_html = _52w_bar(pick["current_price"], pick.get("low_52w"), pick.get("high_52w"))

    risk_items = "".join(f'<li style="margin-bottom:6px;">{r}</li>' for r in risks)

    # News rows
    news_rows = ""
    for item in pick.get("news", [])[:4]:
        title = item.get("title", "")
        link  = item.get("link") or item.get("url") or "#"
        if title:
            news_rows += f'<li style="margin-bottom:5px;"><a href="{link}" style="color:#2563eb;text-decoration:none;">{title}</a></li>'
    news_section = f"""
    <table width="100%" style="margin-top:24px;">
      <tr><td style="padding:16px;background:#f0f9ff;border-radius:8px;">
        <p style="margin:0 0 10px;font-weight:700;font-size:14px;color:#1e3a5f;">Recent News</p>
        <ul style="margin:0;padding-left:18px;font-size:13px;color:#374151;">{news_rows}</ul>
      </td></tr>
    </table>""" if news_rows else ""

    # Runner-up table
    runner_rows = ""
    for i, c in enumerate(top10[1:6], start=2):
        wr_col = _pct_color(c.get("week_return"))
        runner_rows += f"""
        <tr style="border-bottom:1px solid #f3f4f6;">
          <td style="padding:8px 6px;font-weight:600;color:#374151;">#{i} {c['symbol']}</td>
          <td style="padding:8px 6px;color:#6b7280;font-size:12px;">{c['asset_type']}</td>
          <td style="padding:8px 6px;">{_fmt_price(c['current_price'])}</td>
          <td style="padding:8px 6px;color:{wr_col};font-weight:600;">{_fmt_pct(c.get('week_return'))}</td>
          <td style="padding:8px 6px;text-align:right;font-weight:700;">{c['score']}/100</td>
        </tr>"""

    runners_section = f"""
    <table width="100%" style="margin-top:24px;border-collapse:collapse;">
      <tr style="background:#f9fafb;">
        <th colspan="5" style="padding:12px;text-align:left;font-size:14px;color:#374151;border-bottom:2px solid #e5e7eb;">Runner-Up Picks</th>
      </tr>
      <tr style="background:#f9fafb;font-size:11px;color:#9ca3af;text-transform:uppercase;">
        <th style="padding:6px;">Asset</th><th style="padding:6px;">Type</th>
        <th style="padding:6px;">Price</th><th style="padding:6px;">Week</th>
        <th style="padding:6px;text-align:right;">Score</th>
      </tr>
      {runner_rows}
    </table>""" if runner_rows else ""

    pe_row = f'<tr><td style="padding:6px 0;color:#6b7280;">P/E Ratio</td><td style="padding:6px 0;font-weight:600;text-align:right;">{pick["pe_ratio"]:.1f}x</td></tr>' if pick.get("pe_ratio") else ""
    cap_row = f'<tr><td style="padding:6px 0;color:#6b7280;">Market Cap</td><td style="padding:6px 0;font-weight:600;text-align:right;">{_fmt_cap(pick.get("market_cap"))}</td></tr>' if pick.get("market_cap") else ""
    sector_row = f'<tr><td style="padding:6px 0;color:#6b7280;">Sector</td><td style="padding:6px 0;font-weight:600;text-align:right;">{pick["sector"]}</td></tr>' if pick.get("sector") else ""

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
<table width="100%" style="max-width:600px;margin:24px auto;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">

  <!-- Header -->
  <tr><td style="background:linear-gradient(135deg,#1e3a5f 0%,#2563eb 100%);padding:28px 32px;">
    <p style="margin:0;color:rgba(255,255,255,0.7);font-size:13px;letter-spacing:1px;text-transform:uppercase;">Weekly Investment Pick</p>
    <p style="margin:6px 0 0;color:#ffffff;font-size:12px;">{date.today().strftime('%A, %B %d, %Y')}</p>
  </td></tr>

  <!-- Pick hero -->
  <tr><td style="padding:28px 32px 20px;">
    <span style="background:{badge_col};color:#fff;font-size:11px;font-weight:700;padding:3px 10px;border-radius:20px;letter-spacing:0.5px;text-transform:uppercase;">{atype_label}</span>
    <h1 style="margin:12px 0 4px;font-size:40px;font-weight:800;color:#111827;letter-spacing:-1px;">{pick['symbol']}</h1>
    <p style="margin:0 0 16px;color:#6b7280;font-size:15px;">{pick.get('name', '')}</p>

    <table style="border-collapse:collapse;">
      <tr>
        <td style="padding-right:32px;">
          <p style="margin:0;font-size:28px;font-weight:700;color:#111827;">{_fmt_price(pick['current_price'])}</p>
          <p style="margin:2px 0 0;font-size:12px;color:#6b7280;">Current Price</p>
        </td>
        <td style="padding-right:32px;">
          <p style="margin:0;font-size:24px;font-weight:700;color:{week_col};">{_fmt_pct(pick.get('week_return'))}</p>
          <p style="margin:2px 0 0;font-size:12px;color:#6b7280;">This Week</p>
        </td>
        <td>
          <p style="margin:0;font-size:24px;font-weight:700;color:{month_col};">{_fmt_pct(pick.get('month_return'))}</p>
          <p style="margin:2px 0 0;font-size:12px;color:#6b7280;">This Month</p>
        </td>
      </tr>
    </table>

    <div style="background:#eff6ff;border-left:4px solid #2563eb;border-radius:4px;padding:14px 16px;margin-top:20px;">
      <p style="margin:0;font-size:14px;color:#1e3a5f;line-height:1.6;">{thesis}</p>
    </div>
  </td></tr>

  <!-- Metrics -->
  <tr><td style="padding:0 32px 24px;">
    <p style="margin:0 0 12px;font-weight:700;font-size:14px;color:#374151;border-bottom:1px solid #e5e7eb;padding-bottom:8px;">Key Metrics</p>
    <table width="100%" style="border-collapse:collapse;font-size:14px;">
      <tr>
        <td style="padding:6px 0;color:#6b7280;">RSI (14)</td>
        <td style="padding:6px 0;font-weight:600;text-align:right;">{pick.get('rsi', 0):.1f}</td>
      </tr>
      <tr>
        <td style="padding:6px 0;color:#6b7280;">vs 50-day MA ({ma50_str})</td>
        <td style="padding:6px 0;font-weight:600;text-align:right;color:{_pct_color(ma50_diff)};">{_fmt_pct(ma50_diff)}</td>
      </tr>
      <tr>
        <td style="padding:6px 0;color:#6b7280;">vs 200-day MA ({ma200_str})</td>
        <td style="padding:6px 0;font-weight:600;text-align:right;color:{_pct_color(ma200_diff)};">{_fmt_pct(ma200_diff)}</td>
      </tr>
      <tr>
        <td style="padding:6px 0;color:#6b7280;">Volume vs 20-day avg</td>
        <td style="padding:6px 0;font-weight:600;text-align:right;">{pick.get('volume_ratio', 1):.2f}×</td>
      </tr>
      {pe_row}{cap_row}{sector_row}
    </table>
    {bar_html}
  </td></tr>

  <!-- Risk -->
  <tr><td style="padding:0 32px 24px;">
    <p style="margin:0 0 10px;font-weight:700;font-size:14px;color:#374151;border-bottom:1px solid #e5e7eb;padding-bottom:8px;">Risk Factors</p>
    <ul style="margin:0;padding-left:18px;font-size:13px;color:#6b7280;line-height:1.7;">{risk_items}</ul>
  </td></tr>

  <!-- Action -->
  <tr><td style="padding:0 32px 24px;">
    <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:16px 20px;">
      <p style="margin:0 0 6px;font-weight:700;font-size:14px;color:#15803d;">This Week's Action</p>
      <p style="margin:0;font-size:14px;color:#166534;line-height:1.6;">
        Consider investing <strong>$100 in {pick['symbol']}</strong> at market open Monday.
        Fractional shares are supported on Fidelity, Schwab, and Robinhood — no need to buy a whole share.
      </p>
    </div>
  </td></tr>

  {news_section}

  {runners_section}

  <!-- Footer -->
  <tr><td style="padding:20px 32px;background:#f9fafb;border-top:1px solid #e5e7eb;">
    <p style="margin:0;font-size:11px;color:#9ca3af;line-height:1.6;">
      This is an automated market analysis for educational purposes only. Not financial advice.
      Always do your own research before investing. Score out of 100 is a relative ranking, not an absolute recommendation.
    </p>
  </td></tr>

</table>
</body>
</html>"""
    return html


# ── Daily email ───────────────────────────────────────────────────────────────

def build_daily_html(d: dict) -> str:
    sym          = d["symbol"]
    name         = d.get("name", sym)
    price        = d["current_price"]
    day_chg      = d.get("day_change", 0)
    since_chg    = d.get("since_pick_change", 0)
    pick_price   = d.get("pick_price", price)
    week_picked  = d.get("week_picked", "")
    premarket    = d.get("premarket_price")
    pm_chg       = ((premarket - price) / price * 100) if premarket else None

    day_col   = _pct_color(day_chg)
    since_col = _pct_color(since_chg)
    pm_col    = _pct_color(pm_chg)
    arrow     = "▲" if day_chg >= 0 else "▼"
    pm_arrow  = "▲" if (pm_chg or 0) >= 0 else "▼"

    premarket_block = ""
    if premarket:
        premarket_block = f"""
        <tr><td style="padding:10px 0;border-bottom:1px solid #f3f4f6;">
          <span style="color:#6b7280;font-size:13px;">Pre-market</span>
          <span style="float:right;font-weight:600;color:{pm_col};">
            {_fmt_price(premarket)} ({pm_arrow} {_fmt_pct(pm_chg)})
          </span>
        </td></tr>"""

    news_items = ""
    for item in d.get("news", [])[:5]:
        title = item.get("title", "")
        link  = item.get("link") or item.get("url") or "#"
        pub   = item.get("publisher") or item.get("providerPublishTime") or ""
        if title:
            news_items += f'<li style="margin-bottom:8px;font-size:13px;"><a href="{link}" style="color:#2563eb;text-decoration:none;">{title}</a>'
            if pub and isinstance(pub, str):
                news_items += f' <span style="color:#9ca3af;font-size:11px;">— {pub}</span>'
            news_items += "</li>"

    news_block = f"""
    <table width="100%" style="margin-top:20px;">
      <tr><td style="padding:16px;background:#f9fafb;border-radius:8px;">
        <p style="margin:0 0 10px;font-weight:700;font-size:14px;color:#374151;">Latest News</p>
        <ul style="margin:0;padding-left:18px;color:#374151;">{news_items}</ul>
      </td></tr>
    </table>""" if news_items else ""

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
<table width="100%" style="max-width:540px;margin:24px auto;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">

  <!-- Header -->
  <tr><td style="background:#1e3a5f;padding:20px 28px;">
    <p style="margin:0;color:rgba(255,255,255,0.7);font-size:12px;text-transform:uppercase;letter-spacing:1px;">Morning Update</p>
    <p style="margin:4px 0 0;color:#ffffff;font-size:13px;">{d.get('today', date.today().strftime('%A, %B %d, %Y'))}</p>
  </td></tr>

  <!-- Price hero -->
  <tr><td style="padding:24px 28px;">
    <h2 style="margin:0 0 2px;font-size:22px;font-weight:800;color:#111827;">{sym} <span style="font-size:14px;font-weight:400;color:#6b7280;">{name}</span></h2>
    <p style="margin:0 0 16px;font-size:40px;font-weight:800;color:#111827;">{_fmt_price(price)}</p>

    <table width="100%" style="border-collapse:collapse;font-size:14px;">
      {premarket_block}
      <tr><td style="padding:10px 0;border-bottom:1px solid #f3f4f6;">
        <span style="color:#6b7280;">Today's change</span>
        <span style="float:right;font-size:18px;font-weight:700;color:{day_col};">{arrow} {_fmt_pct(day_chg)}</span>
      </td></tr>
      <tr><td style="padding:10px 0;border-bottom:1px solid #f3f4f6;">
        <span style="color:#6b7280;">Since picked (${pick_price:.2f} on {week_picked})</span>
        <span style="float:right;font-weight:700;color:{since_col};">{_fmt_pct(since_chg)}</span>
      </td></tr>
    </table>
  </td></tr>

  {news_block}

  <!-- Footer -->
  <tr><td style="padding:16px 28px;background:#f9fafb;border-top:1px solid #e5e7eb;">
    <p style="margin:0;font-size:11px;color:#9ca3af;">Automated daily update · Not financial advice</p>
  </td></tr>

</table>
</body>
</html>"""
    return html


# ── Send ──────────────────────────────────────────────────────────────────────

def send_email(subject: str, html: str, to: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = EMAIL_FROM
    msg["To"]      = to
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASS)
        server.sendmail(EMAIL_FROM, to, msg.as_string())
    print(f"Email sent: {subject}")
