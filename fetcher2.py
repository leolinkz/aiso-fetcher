"""
╔══════════════════════════════════════════════════════════════╗
║   AI SENTIMENT OSCILLATOR — Multi-Asset Fetcher v2.0        ║
║   Supports: BTC, ETH, SOL, GOLD, SPY, NVDA, TSLA,          ║
║             EURUSD, OIL, and any custom Reddit keyword      ║
║                                                              ║
║   Usage:                                                     ║
║     python3 fetcher_v2.py                  (default: BTC)   ║
║     python3 fetcher_v2.py --asset GOLD                      ║
║     python3 fetcher_v2.py --asset SPY                       ║
║     python3 fetcher_v2.py --asset EURUSD                    ║
║     python3 fetcher_v2.py --asset NVDA                      ║
║     python3 fetcher_v2.py --asset OIL                       ║
║     python3 fetcher_v2.py --asset ETH                       ║
║     python3 fetcher_v2.py --list            (show all)      ║
╚══════════════════════════════════════════════════════════════╝

Install once:  pip3 install requests
"""

import requests
import json
import sys
import math
from datetime import datetime

# ── ASSET PROFILES ────────────────────────────────────────────
# Each profile defines:
#   label       : human-readable name
#   subreddits  : list of subreddits to scan
#   keywords    : extra bullish/bearish words specific to the asset
#   has_fg      : True if Alternative.me Fear & Greed applies
#   cnn_fg      : True if CNN Fear & Greed Index applies (stocks)
#   trends_term : Google-style search term for context (informational only)

ASSET_PROFILES = {

    # ── CRYPTO ────────────────────────────────────────────────
    "BTC": {
        "label"       : "Bitcoin (BTC)",
        "subreddits"  : ["CryptoCurrency", "Bitcoin", "btc"],
        "keywords"    : {
            "bull": ["bitcoin", "btc", "sats", "halving", "etf", "spot etf",
                     "institutional", "hodl", "laser eyes", "accumulate"],
            "bear": ["btc crash", "bitcoin dead", "crypto winter", "sell btc",
                     "mt gox", "regulation", "sec", "ban"]
        },
        "has_fg"      : True,
        "cnn_fg"      : False,
        "trends_term" : "bitcoin price",
        "category"    : "crypto",
    },
    "ETH": {
        "label"       : "Ethereum (ETH)",
        "subreddits"  : ["ethereum", "ethtrader", "CryptoCurrency"],
        "keywords"    : {
            "bull": ["ethereum", "eth", "staking", "degen", "defi", "l2",
                     "merge", "ultrasound", "burn", "base"],
            "bear": ["eth crash", "gas fees", "slow", "overvalued", "sell eth",
                     "ethereum killer", "btc flippening"]
        },
        "has_fg"      : True,
        "cnn_fg"      : False,
        "trends_term" : "ethereum price",
        "category"    : "crypto",
    },
    "SOL": {
        "label"       : "Solana (SOL)",
        "subreddits"  : ["solana", "CryptoCurrency"],
        "keywords"    : {
            "bull": ["solana", "sol", "fast", "cheap", "nft", "defi sol",
                     "pump fun", "meme coin", "validators"],
            "bear": ["solana down", "outage", "centralized", "sol dump",
                     "network halt", "firedancer"]
        },
        "has_fg"      : True,
        "cnn_fg"      : False,
        "trends_term" : "solana price",
        "category"    : "crypto",
    },

    # ── STOCKS / INDICES ──────────────────────────────────────
    "SPY": {
        "label"       : "S&P 500 (SPY)",
        "subreddits"  : ["stocks", "investing", "wallstreetbets", "StockMarket"],
        "keywords"    : {
            "bull": ["bull run", "all time high", "ath", "buy the dip",
                     "fed pivot", "soft landing", "earnings beat", "rally",
                     "calls", "yolo", "sp500", "spy calls"],
            "bear": ["recession", "crash", "bear market", "puts", "sell",
                     "fed hike", "inflation", "layoffs", "earnings miss",
                     "correction", "spy puts", "short"]
        },
        "has_fg"      : False,
        "cnn_fg"      : True,
        "trends_term" : "stock market crash",
        "category"    : "stocks",
    },
    "QQQ": {
        "label"       : "Nasdaq 100 (QQQ)",
        "subreddits"  : ["stocks", "investing", "wallstreetbets", "StockMarket"],
        "keywords"    : {
            "bull": ["tech rally", "ai boom", "nvidia", "big tech", "qqq calls",
                     "growth stocks", "bull", "buy"],
            "bear": ["tech selloff", "rate hike", "qqq puts", "overvalued",
                     "bubble", "layoffs", "ai bubble", "short"]
        },
        "has_fg"      : False,
        "cnn_fg"      : True,
        "trends_term" : "nasdaq crash",
        "category"    : "stocks",
    },
    "NVDA": {
        "label"       : "Nvidia (NVDA)",
        "subreddits"  : ["nvidia", "stocks", "wallstreetbets", "investing"],
        "keywords"    : {
            "bull": ["nvda", "nvidia", "ai", "gpu", "datacenter", "blackwell",
                     "earnings beat", "calls", "buy nvda", "moon"],
            "bear": ["nvda puts", "overvalued", "bubble", "competition",
                     "amd", "intel", "china ban", "short nvda", "sell"]
        },
        "has_fg"      : False,
        "cnn_fg"      : True,
        "trends_term" : "nvidia stock",
        "category"    : "stocks",
    },
    "TSLA": {
        "label"       : "Tesla (TSLA)",
        "subreddits"  : ["teslainvestorsclub", "stocks", "wallstreetbets"],
        "keywords"    : {
            "bull": ["tsla", "tesla", "elon", "cybertruck", "fsd", "optimus",
                     "calls", "buy", "moon", "delivery beat"],
            "bear": ["tsla puts", "elon mess", "boycott", "delivery miss",
                     "overvalued", "short tsla", "competition", "ev crash"]
        },
        "has_fg"      : False,
        "cnn_fg"      : True,
        "trends_term" : "tesla stock",
        "category"    : "stocks",
    },
    "MSTR": {
        "label"       : "MicroStrategy (MSTR)",
        "subreddits"  : ["MSTR", "wallstreetbets", "Bitcoin", "stocks"],
        "keywords"    : {
            "bull": ["mstr", "microstrategy", "saylor", "bitcoin treasury",
                     "buy", "calls", "leveraged btc"],
            "bear": ["mstr puts", "overleveraged", "margin call", "sell",
                     "short mstr", "bitcoin crash"]
        },
        "has_fg"      : True,
        "cnn_fg"      : True,
        "trends_term" : "microstrategy bitcoin",
        "category"    : "stocks",
    },

    # ── COMMODITIES ───────────────────────────────────────────
    "GOLD": {
        "label"       : "Gold (XAUUSD)",
        "subreddits"  : ["Gold", "Silverbugs", "investing", "wallstreetbets"],
        "keywords"    : {
            "bull": ["gold", "xau", "safe haven", "inflation hedge", "buy gold",
                     "central bank", "all time high", "bullion", "ounce",
                     "gold rally", "precious metals", "store of value"],
            "bear": ["gold dump", "sell gold", "gold crash", "dollar strong",
                     "rate hike", "gold bearish", "overvalued gold",
                     "digital gold", "gold short"]
        },
        "has_fg"      : False,
        "cnn_fg"      : False,
        "trends_term" : "gold price today",
        "category"    : "commodity",
    },
    "SILVER": {
        "label"       : "Silver (XAGUSD)",
        "subreddits"  : ["Silverbugs", "Gold", "investing"],
        "keywords"    : {
            "bull": ["silver", "xag", "silver squeeze", "buy silver",
                     "industrial demand", "solar", "ev demand", "stack"],
            "bear": ["silver dump", "sell silver", "silver crash",
                     "dollar strong", "short silver"]
        },
        "has_fg"      : False,
        "cnn_fg"      : False,
        "trends_term" : "silver price",
        "category"    : "commodity",
    },
    "OIL": {
        "label"       : "Crude Oil (WTI/USOIL)",
        "subreddits"  : ["energy", "investing", "Economics", "stocks"],
        "keywords"    : {
            "bull": ["oil rally", "opec cut", "supply cut", "crude up",
                     "energy demand", "wti", "brent", "buy oil", "shortage"],
            "bear": ["oil crash", "opec increase", "demand drop", "recession",
                     "crude down", "oversupply", "sell oil", "ev transition"]
        },
        "has_fg"      : False,
        "cnn_fg"      : False,
        "trends_term" : "oil price today",
        "category"    : "commodity",
    },

    # ── FOREX ─────────────────────────────────────────────────
    "EURUSD": {
        "label"       : "Euro / US Dollar (EURUSD)",
        "subreddits"  : ["Forex", "investing", "Economics"],
        "keywords"    : {
            "bull": ["euro rally", "eur up", "ecb hike", "dollar weak",
                     "euro strong", "buy eurusd", "dxy down"],
            "bear": ["euro crash", "eur down", "dollar strong", "dxy up",
                     "ecb cut", "recession europe", "sell eurusd", "parity"]
        },
        "has_fg"      : False,
        "cnn_fg"      : False,
        "trends_term" : "euro dollar exchange rate",
        "category"    : "forex",
    },
    "GBPUSD": {
        "label"       : "British Pound / US Dollar (GBPUSD)",
        "subreddits"  : ["Forex", "investing", "unitedkingdom"],
        "keywords"    : {
            "bull": ["pound rally", "gbp up", "boe hike", "cable up",
                     "dollar weak", "buy gbpusd", "uk economy"],
            "bear": ["pound crash", "gbp down", "dollar strong", "boe cut",
                     "uk recession", "sell gbpusd", "cable down"]
        },
        "has_fg"      : False,
        "cnn_fg"      : False,
        "trends_term" : "pound dollar exchange rate",
        "category"    : "forex",
    },
    "USDJPY": {
        "label"       : "US Dollar / Japanese Yen (USDJPY)",
        "subreddits"  : ["Forex", "investing", "japan"],
        "keywords"    : {
            "bull": ["dollar yen", "usdjpy up", "boj dovish", "yen weak",
                     "carry trade", "buy usdjpy", "intervention unlikely"],
            "bear": ["yen rally", "boj hike", "intervention", "usdjpy down",
                     "yen strong", "sell usdjpy", "carry unwind"]
        },
        "has_fg"      : False,
        "cnn_fg"      : False,
        "trends_term" : "dollar yen exchange rate",
        "category"    : "forex",
    },
}

# ── SHARED SENTIMENT WORDS (apply to all assets) ──────────────
BASE_BULL = [
    "moon", "bull", "buy", "pump", "surge", "rally", "up", "gain",
    "profit", "bullish", "breakout", "accumulate", "undervalued",
    "recovery", "long", "calls", "uptrend", "ath", "all time high"
]
BASE_BEAR = [
    "crash", "dump", "bear", "sell", "down", "loss", "drop", "fear",
    "bearish", "correction", "rekt", "capitulate", "overvalued",
    "downtrend", "collapse", "bubble", "puts", "short", "recession"
]

OUTPUT_FILE = "aiso_score.json"

# ── HELPERS ───────────────────────────────────────────────────
def clamp(val, lo=-100, hi=100):
    return max(lo, min(hi, val))

def zone_name(score):
    if   score >=  60: return "🟢 EXTREME GREED"
    elif score >=  20: return "🔵 GREED"
    elif score >= -20: return "⚪ NEUTRAL"
    elif score >= -60: return "🟡 FEAR"
    else:              return "🔴 EXTREME FEAR"

def divider(char="─", n=48):
    print(char * n)

def header(title):
    divider("═")
    print(f"  {title}")
    divider("═")

# ── SOURCE 1: Alternative.me Fear & Greed (crypto) ───────────
def fetch_crypto_fg():
    try:
        r    = requests.get("https://api.alternative.me/fng/", timeout=10)
        data = r.json()["data"][0]
        raw  = int(data["value"])
        lbl  = data["value_classification"]
        norm = clamp((raw - 50) * 2)
        return norm, lbl, raw
    except Exception as e:
        print(f"  [WARN] Crypto F&G API failed: {e}")
        return 0, "Unknown", 50

# ── SOURCE 2: CNN Fear & Greed (stocks) ──────────────────────
def fetch_cnn_fg():
    """
    CNN F&G doesn't have an official public API.
    We use a community-maintained mirror that returns JSON.
    Falls back gracefully if unavailable.
    """
    try:
        url  = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        hdrs = {"User-Agent": "AISO-Fetcher/2.0", "Referer": "https://edition.cnn.com/"}
        r    = requests.get(url, headers=hdrs, timeout=10)
        data = r.json()
        raw  = float(data["fear_and_greed"]["score"])
        lbl  = data["fear_and_greed"]["rating"].replace("_", " ").title()
        norm = clamp((raw - 50) * 2)
        return norm, lbl, round(raw)
    except Exception as e:
        print(f"  [WARN] CNN F&G API failed: {e}")
        print(f"         Falling back to Reddit-only scoring.")
        return 0, "Unavailable", 50

# ── SOURCE 3: Reddit keyword scan ────────────────────────────
def fetch_reddit_sentiment(profile):
    bull_words = BASE_BULL + profile["keywords"]["bull"]
    bear_words = BASE_BEAR + profile["keywords"]["bear"]
    headers    = {"User-Agent": "AISO-Fetcher/2.0"}

    total_score = 0
    total_posts = 0
    sub_results = {}

    for sub in profile["subreddits"]:
        try:
            url   = f"https://www.reddit.com/r/{sub}/hot.json?limit=50"
            r     = requests.get(url, headers=headers, timeout=10)
            posts = r.json()["data"]["children"]
            sub_bull = 0
            sub_bear = 0
            for p in posts:
                title = p["data"]["title"].lower()
                bull  = sum(1 for w in bull_words if w in title)
                bear  = sum(1 for w in bear_words if w in title)
                total_score += (bull - bear)
                sub_bull    += bull
                sub_bear    += bear
                total_posts += 1
            sub_results[sub] = {"bull": sub_bull, "bear": sub_bear,
                                 "posts": len(posts)}
        except Exception as e:
            print(f"  [WARN] r/{sub} failed: {e}")
            sub_results[sub] = {"bull": 0, "bear": 0, "posts": 0}

    if total_posts == 0:
        return 0, sub_results

    avg  = total_score / total_posts
    norm = clamp(avg * 40)
    return round(norm, 1), sub_results

# ── MAIN ──────────────────────────────────────────────────────
def run(asset_key):
    asset_key = asset_key.upper()

    if asset_key not in ASSET_PROFILES:
        print(f"\n  [ERROR] Unknown asset '{asset_key}'")
        print(f"  Run:  python3 fetcher_v2.py --list  to see all options.\n")
        sys.exit(1)

    profile  = ASSET_PROFILES[asset_key]
    category = profile["category"]

    now = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    header(f"AI SENTIMENT OSCILLATOR v2.0  ·  {profile['label']}")
    print(f"  {now}")
    divider()

    scores   = {}
    weights  = {}
    has_fg   = False
    fg_norm  = 0

    # ── Step 1: Sentiment index (if applicable) ──────────────
    if profile["has_fg"] and category == "crypto":
        print("\n[1/2] Fetching Crypto Fear & Greed Index...")
        fg_norm, fg_label, fg_raw = fetch_crypto_fg()
        print(f"  Raw score : {fg_raw}/100  ({fg_label})")
        print(f"  Normalized: {fg_norm:+.1f}")
        scores["fear_greed"]  = fg_norm
        weights["fear_greed"] = 0.55
        has_fg = True

    elif profile["cnn_fg"]:
        print("\n[1/2] Fetching CNN Fear & Greed Index (stocks)...")
        fg_norm, fg_label, fg_raw = fetch_cnn_fg()
        print(f"  Raw score : {fg_raw}/100  ({fg_label})")
        print(f"  Normalized: {fg_norm:+.1f}")
        scores["fear_greed"]  = fg_norm
        weights["fear_greed"] = 0.50
        has_fg = True

    else:
        print(f"\n[1/2] No fear/greed index available for {profile['label']}")
        print(f"  Scoring will rely on Reddit sentiment only.")
        weights["fear_greed"] = 0.0

    # ── Step 2: Reddit sentiment ─────────────────────────────
    step = "2" if has_fg else "1"
    print(f"\n[{step}/2] Scanning Reddit sentiment ({', '.join(['r/'+s for s in profile['subreddits']])})...")
    reddit_score, sub_results = fetch_reddit_sentiment(profile)

    for sub, res in sub_results.items():
        status = f"  r/{sub:<20} {res['posts']} posts  |  bull: {res['bull']}  bear: {res['bear']}"
        print(status)

    print(f"  Reddit composite: {reddit_score:+.1f}")
    scores["reddit"] = reddit_score

    # ── Composite calculation ─────────────────────────────────
    if has_fg:
        reddit_weight = 1.0 - weights["fear_greed"]
        composite = (scores["fear_greed"] * weights["fear_greed"]) + \
                    (scores["reddit"]     * reddit_weight)
    else:
        composite = scores["reddit"]

    composite = round(clamp(composite), 1)

    # ── Output ───────────────────────────────────────────────
    print()
    divider("─")
    print(f"  ASSET           :  {profile['label']}")
    if has_fg:
        fg_src = "Crypto F&G" if category == "crypto" else "CNN F&G"
        print(f"  {fg_src:<16}:  {scores['fear_greed']:+.1f}  (weight: {int(weights['fear_greed']*100)}%)")
    print(f"  Reddit          :  {scores['reddit']:+.1f}  (weight: {int((1-weights.get('fear_greed',0))*100)}%)")
    print(f"  COMPOSITE SCORE :  {composite:+.1f}")
    print(f"  ZONE            :  {zone_name(composite)}")
    divider("─")
    print(f"\n  → In TradingView:")
    print(f"    1. Open AISO Settings")
    print(f"    2. Enable  'Manual Bias'")
    print(f"    3. Set Bias Score to  {composite}")
    divider("═")
    print()

    # ── Save JSON ─────────────────────────────────────────────
    output = {
        "timestamp"     : datetime.now().isoformat(),
        "asset"         : asset_key,
        "asset_label"   : profile["label"],
        "category"      : category,
        "scores"        : scores,
        "weights"       : {k: round(v, 2) for k, v in weights.items()},
        "composite"     : composite,
        "zone"          : zone_name(composite).split(" ", 1)[1],
    }
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)
    print(f"  ✓  Saved to {OUTPUT_FILE}\n")

def list_assets():
    header("Supported Assets")
    cats = {}
    for key, p in ASSET_PROFILES.items():
        cats.setdefault(p["category"], []).append((key, p["label"]))
    for cat, items in cats.items():
        print(f"\n  {cat.upper()}")
        for key, label in items:
            print(f"    python3 fetcher_v2.py --asset {key:<10}  →  {label}")
    print()

# ── ENTRY POINT ───────────────────────────────────────────────
if __name__ == "__main__":
    args = sys.argv[1:]

    if "--list" in args:
        list_assets()
        sys.exit(0)

    asset = "BTC"  # default
    if "--asset" in args:
        idx = args.index("--asset")
        if idx + 1 < len(args):
            asset = args[idx + 1]
        else:
            print("\n  [ERROR] --asset flag requires a value.")
            print("  Example:  python3 fetcher_v2.py --asset GOLD\n")
            sys.exit(1)

    run(asset)