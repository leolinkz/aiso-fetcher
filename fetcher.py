"""
AI SENTIMENT OSCILLATOR — Free Data Fetcher
Uses: Alternative.me Fear & Greed API (no key) + Reddit RSS (no key)
Run: python fetcher.py
"""
import requests, json, math
from datetime import datetime

# ─── CONFIG ─────────────────────────────────────────────
# Edit this list to match the asset you're trading
SUBREDDITS  = ["CryptoCurrency", "Bitcoin", "ethtrader"]
OUTPUT_FILE = "aiso_score.json"

BULL_WORDS = [
    "moon", "bull", "buy", "pump", "ath", "surge", "rally",
    "up", "gain", "profit", "bullish", "breakout", "accumulate",
    "undervalued", "load", "hodl", "uptrend", "recovery"
]
BEAR_WORDS = [
    "crash", "dump", "bear", "sell", "down", "loss", "drop",
    "fear", "bearish", "correction", "rug", "rekt", "capitulate",
    "overvalued", "scam", "downtrend", "collapse", "bubble"
]

# ─── SOURCE 1: Fear & Greed Index (no API key needed) ───
def fetch_fear_greed():
    try:
        r = requests.get("https://api.alternative.me/fng/", timeout=10)
        data = r.json()["data"][0]
        raw   = int(data["value"])           # 0–100
        label = data["value_classification"]
        norm  = (raw - 50) * 2               # → -100 to +100
        return norm, label, raw
    except Exception as e:
        print(f"  [WARN] Fear & Greed API failed: {e}")
        return 0, "Unknown", 50

# ─── SOURCE 2: Reddit Sentiment (free, no key via RSS) ──
def fetch_reddit_sentiment():
    total_score = 0
    total_posts = 0
    headers = {"User-Agent": "AISO-Free-Fetcher/1.0"}

    for sub in SUBREDDITS:
        try:
            url = f"https://www.reddit.com/r/{sub}/hot.json?limit=50"
            r   = requests.get(url, headers=headers, timeout=10)
            posts = r.json()["data"]["children"]
            for p in posts:
                title = p["data"]["title"].lower()
                bull  = sum(1 for w in BULL_WORDS if w in title)
                bear  = sum(1 for w in BEAR_WORDS if w in title)
                total_score += (bull - bear)
                total_posts += 1
        except Exception as e:
            print(f"  [WARN] Reddit r/{sub} failed: {e}")

    if total_posts == 0:
        return 0
    avg   = total_score / total_posts
    norm  = max(-100, min(100, avg * 40))
    return round(norm, 1)

# ─── COMPOSITE ──────────────────────────────────────────
def zone_name(score):
    if   score >=  60: return "🟢 EXTREME GREED"
    elif score >=  20: return "🔵 GREED"
    elif score >= -20: return "⚪ NEUTRAL"
    elif score >= -60: return "🟡 FEAR"
    else:             return "🔴 EXTREME FEAR"

# ─── MAIN ───────────────────────────────────────────────
if __name__ == "__main__":
    print("\n══════════════════════════════════════════")
    print("  AI SENTIMENT OSCILLATOR — Free Fetcher")
    print(f"  {datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}")
    print("══════════════════════════════════════════")

    print("\n[1/2] Fetching Fear & Greed Index...")
    fg_norm, fg_label, fg_raw = fetch_fear_greed()
    print(f"  Raw: {fg_raw}/100  →  {fg_label}")
    print(f"  Normalized: {fg_norm:+.1f}")

    print("\n[2/2] Fetching Reddit sentiment...")
    reddit_score = fetch_reddit_sentiment()
    print(f"  Score: {reddit_score:+.1f}")

    # Weight: F&G 65%, Reddit 35%
    composite = (fg_norm * 0.65) + (reddit_score * 0.35)
    composite = round(max(-100, min(100, composite)), 1)

    print("\n──────────────────────────────────────────")
    print(f"  COMPOSITE SCORE :  {composite:+.1f}")
    print(f"  ZONE            :  {zone_name(composite)}")
    print("──────────────────────────────────────────")
    print("  → In TradingView:")
    print("    1. Open AISO Settings")
    print("    2. Enable 'Manual Bias'")
    print(f"    3. Set Bias Score to  {composite}")
    print("══════════════════════════════════════════\n")

    # Save JSON for GitHub Actions automation
    output = {
        "timestamp"     : datetime.now().isoformat(),
        "fear_greed_raw" : fg_raw,
        "fear_greed_label": fg_label,
        "fear_greed_norm": fg_norm,
        "reddit_score"  : reddit_score,
        "composite"     : composite,
        "zone"          : zone_name(composite).split(" ", 1)[1]
    }
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)
    print(f"  ✓  Saved to {OUTPUT_FILE}")