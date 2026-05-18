"""
╔══════════════════════════════════════════════════════════════╗
║   AI SENTIMENT OSCILLATOR — Multi-Asset Fetcher v3.0        ║
║                                                              ║
║   Usage:                                                     ║
║     All assets:   python3 fetcher_v2.py --all               ║
║     One asset:    python3 fetcher_v2.py --asset BTC         ║
║     List assets:  python3 fetcher_v2.py --list              ║
║                                                              ║
║   Outputs:                                                   ║
║     scores/BTC.json  scores/ETH.json  scores/GOLD.json ...  ║
║     aiso_all_scores.json  (all assets in one file)          ║
║     aiso_score.json       (latest / BTC — backward compat)  ║
╚══════════════════════════════════════════════════════════════╝

Install:  pip3 install requests
"""

import requests, json, sys, os, time
from datetime import datetime, timezone

# ── OUTPUT ────────────────────────────────────────────────────
SCORES_DIR   = "scores"
SUMMARY_FILE = "aiso_score.json"
ALL_FILE     = "aiso_all_scores.json"

# ── ASSET PROFILES ────────────────────────────────────────────
ASSET_PROFILES = {
    "BTC": {
        "label":"Bitcoin","ticker":"BTC","category":"crypto",
        "subreddits":["CryptoCurrency","Bitcoin","btc"],
        "has_fg":True,"cnn_fg":False,
        "keywords":{"bull":["bitcoin","btc","sats","halving","etf","hodl","accumulate","laser eyes"],
                    "bear":["btc crash","bitcoin dead","crypto winter","sell btc","mt gox","sec ban"]},
    },
    "ETH": {
        "label":"Ethereum","ticker":"ETH","category":"crypto",
        "subreddits":["ethereum","ethtrader","CryptoCurrency"],
        "has_fg":True,"cnn_fg":False,
        "keywords":{"bull":["ethereum","eth","staking","degen","defi","l2","ultrasound","burn"],
                    "bear":["eth crash","gas fees","overvalued","sell eth","ethereum killer"]},
    },
    "SOL": {
        "label":"Solana","ticker":"SOL","category":"crypto",
        "subreddits":["solana","CryptoCurrency"],
        "has_fg":True,"cnn_fg":False,
        "keywords":{"bull":["solana","sol","fast","cheap","nft","pump fun","meme coin"],
                    "bear":["solana down","outage","centralized","sol dump","network halt"]},
    },
    "SPY": {
        "label":"S&P 500","ticker":"SPY","category":"stocks",
        "subreddits":["stocks","investing","wallstreetbets","StockMarket"],
        "has_fg":False,"cnn_fg":True,
        "keywords":{"bull":["bull run","ath","buy the dip","fed pivot","earnings beat","rally","calls"],
                    "bear":["recession","crash","bear market","puts","fed hike","inflation","layoffs"]},
    },
    "QQQ": {
        "label":"Nasdaq 100","ticker":"QQQ","category":"stocks",
        "subreddits":["stocks","investing","wallstreetbets"],
        "has_fg":False,"cnn_fg":True,
        "keywords":{"bull":["tech rally","ai boom","big tech","qqq calls","growth stocks"],
                    "bear":["tech selloff","rate hike","qqq puts","overvalued","bubble","layoffs"]},
    },
    "NVDA": {
        "label":"Nvidia","ticker":"NVDA","category":"stocks",
        "subreddits":["nvidia","stocks","wallstreetbets"],
        "has_fg":False,"cnn_fg":True,
        "keywords":{"bull":["nvda","nvidia","ai","gpu","datacenter","blackwell","earnings beat"],
                    "bear":["nvda puts","overvalued","amd","intel","china ban","short nvda"]},
    },
    "TSLA": {
        "label":"Tesla","ticker":"TSLA","category":"stocks",
        "subreddits":["teslainvestorsclub","stocks","wallstreetbets"],
        "has_fg":False,"cnn_fg":True,
        "keywords":{"bull":["tsla","tesla","elon","fsd","optimus","calls","delivery beat"],
                    "bear":["tsla puts","boycott","delivery miss","overvalued","short tsla"]},
    },
    "MSTR": {
        "label":"MicroStrategy","ticker":"MSTR","category":"stocks",
        "subreddits":["MSTR","wallstreetbets","Bitcoin"],
        "has_fg":True,"cnn_fg":True,
        "keywords":{"bull":["mstr","microstrategy","saylor","bitcoin treasury","calls"],
                    "bear":["mstr puts","overleveraged","margin call","short mstr"]},
    },
    "GOLD": {
        "label":"Gold","ticker":"XAU","category":"commodity",
        "subreddits":["Gold","Silverbugs","investing"],
        "has_fg":False,"cnn_fg":False,
        "keywords":{"bull":["gold","xau","safe haven","inflation hedge","buy gold","central bank",
                            "all time high","bullion","gold rally","precious metals"],
                    "bear":["gold dump","sell gold","gold crash","dollar strong","gold bearish"]},
    },
    "SILVER": {
        "label":"Silver","ticker":"XAG","category":"commodity",
        "subreddits":["Silverbugs","Gold","investing"],
        "has_fg":False,"cnn_fg":False,
        "keywords":{"bull":["silver","xag","silver squeeze","buy silver","solar","ev demand","stack"],
                    "bear":["silver dump","sell silver","silver crash","dollar strong"]},
    },
    "OIL": {
        "label":"Crude Oil","ticker":"WTI","category":"commodity",
        "subreddits":["energy","investing","Economics"],
        "has_fg":False,"cnn_fg":False,
        "keywords":{"bull":["oil rally","opec cut","supply cut","crude up","wti","brent","buy oil"],
                    "bear":["oil crash","opec increase","demand drop","crude down","oversupply"]},
    },
    "EURUSD": {
        "label":"EUR / USD","ticker":"EUR","category":"forex",
        "subreddits":["Forex","investing","Economics"],
        "has_fg":False,"cnn_fg":False,
        "keywords":{"bull":["euro rally","eur up","ecb hike","dollar weak","euro strong","dxy down"],
                    "bear":["euro crash","eur down","dollar strong","dxy up","ecb cut","parity"]},
    },
    "GBPUSD": {
        "label":"GBP / USD","ticker":"GBP","category":"forex",
        "subreddits":["Forex","investing","unitedkingdom"],
        "has_fg":False,"cnn_fg":False,
        "keywords":{"bull":["pound rally","gbp up","boe hike","cable up","dollar weak"],
                    "bear":["pound crash","gbp down","dollar strong","boe cut","uk recession"]},
    },
    "USDJPY": {
        "label":"USD / JPY","ticker":"JPY","category":"forex",
        "subreddits":["Forex","investing","japan"],
        "has_fg":False,"cnn_fg":False,
        "keywords":{"bull":["dollar yen","usdjpy up","boj dovish","yen weak","carry trade"],
                    "bear":["yen rally","boj hike","intervention","usdjpy down","yen strong"]},
    },
}

BASE_BULL = ["moon","bull","buy","pump","surge","rally","up","gain","profit",
             "bullish","breakout","accumulate","undervalued","recovery","long",
             "calls","uptrend","ath","all time high","squeeze"]
BASE_BEAR = ["crash","dump","bear","sell","down","loss","drop","fear","bearish",
             "correction","rekt","capitulate","overvalued","downtrend","collapse",
             "bubble","puts","short","recession","tank","plunge"]

# ── HELPERS ───────────────────────────────────────────────────
def clamp(v, lo=-100, hi=100):
    return max(lo, min(hi, v))

def zone_name(s):
    if s >=  60: return "EXTREME GREED"
    if s >=  20: return "GREED"
    if s >= -20: return "NEUTRAL"
    if s >= -60: return "FEAR"
    return "EXTREME FEAR"

def zone_emoji(z):
    return {"EXTREME GREED":"🟢","GREED":"🔵","NEUTRAL":"⚪",
            "FEAR":"🟡","EXTREME FEAR":"🔴"}.get(z,"⚪")

def now_utc():
    return datetime.now(timezone.utc).isoformat()

# ── DATA SOURCES ──────────────────────────────────────────────
def fetch_crypto_fg():
    try:
        r   = requests.get("https://api.alternative.me/fng/", timeout=12)
        d   = r.json()["data"][0]
        raw = int(d["value"])
        return clamp((raw - 50) * 2), d["value_classification"], raw
    except Exception as e:
        print(f"    [WARN] Crypto F&G: {e}")
        return None, "Unavailable", None

def fetch_cnn_fg():
    try:
        url  = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        hdrs = {"User-Agent":"AISO/3.0","Referer":"https://edition.cnn.com/"}
        r    = requests.get(url, headers=hdrs, timeout=12)
        d    = r.json()["fear_and_greed"]
        raw  = float(d["score"])
        return clamp((raw - 50) * 2), d["rating"].replace("_"," ").title(), round(raw)
    except Exception as e:
        print(f"    [WARN] CNN F&G: {e}")
        return None, "Unavailable", None

def fetch_reddit(profile):
    bull = BASE_BULL + profile["keywords"]["bull"]
    bear = BASE_BEAR + profile["keywords"]["bear"]
    hdrs = {"User-Agent":"AISO/3.0"}
    total_score = 0
    total_posts = 0
    for sub in profile["subreddits"]:
        try:
            r     = requests.get(f"https://www.reddit.com/r/{sub}/hot.json?limit=50",
                                 headers=hdrs, timeout=12)
            posts = r.json()["data"]["children"]
            for p in posts:
                t = p["data"]["title"].lower()
                total_score += sum(1 for w in bull if w in t) - sum(1 for w in bear if w in t)
                total_posts += 1
            time.sleep(0.8)
        except Exception as e:
            print(f"    [WARN] r/{sub}: {e}")
    if total_posts == 0:
        return 0.0
    return round(clamp(total_score / total_posts * 40), 1)

# ── FETCH ONE ASSET ───────────────────────────────────────────
def fetch_asset(key):
    p   = ASSET_PROFILES[key]
    cat = p["category"]
    print(f"  [{key}] {p['label']}")

    scores  = {}
    weights = {}
    fg_norm = None

    if p["has_fg"] and cat == "crypto":
        fg_norm, fg_lbl, fg_raw = fetch_crypto_fg()
        if fg_norm is not None:
            scores["fear_greed"]  = round(fg_norm, 1)
            weights["fear_greed"] = 0.55
            print(f"    Crypto F&G : {fg_raw}/100 → {fg_norm:+.1f}")

    elif p["cnn_fg"]:
        fg_norm, fg_lbl, fg_raw = fetch_cnn_fg()
        if fg_norm is not None:
            scores["fear_greed"]  = round(fg_norm, 1)
            weights["fear_greed"] = 0.50
            print(f"    CNN F&G    : {fg_raw}/100 → {fg_norm:+.1f}")

    reddit = fetch_reddit(p)
    scores["reddit"] = reddit
    print(f"    Reddit     : {reddit:+.1f}")

    fw = weights.get("fear_greed", 0.0)
    composite = round(clamp(
        (scores["fear_greed"] * fw + reddit * (1 - fw)) if fw > 0 else reddit
    ), 1)
    zone = zone_name(composite)
    sign = "+" if composite >= 0 else ""
    print(f"    Composite  : {sign}{composite}  {zone_emoji(zone)} {zone}\n")

    return {
        "timestamp"   : now_utc(),
        "asset"       : key,
        "asset_label" : p["label"],
        "ticker"      : p["ticker"],
        "category"    : cat,
        "composite"   : composite,
        "zone"        : zone,
        "scores"      : scores,
        "weights"     : {k: round(v, 2) for k, v in weights.items()},
    }

def save_asset(data):
    os.makedirs(SCORES_DIR, exist_ok=True)
    path = os.path.join(SCORES_DIR, f"{data['asset']}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return path

# ── RUN ALL ───────────────────────────────────────────────────
def run_all():
    print("\n" + "═"*52)
    print("  AISO v3.0 — Full Market Fetch")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("═"*52 + "\n")

    all_data = []
    failed   = []

    for key in ASSET_PROFILES:
        try:
            data = fetch_asset(key)
            save_asset(data)
            all_data.append(data)
            if key == "BTC":
                with open(SUMMARY_FILE, "w") as f:
                    json.dump(data, f, indent=2)
            time.sleep(1.2)
        except Exception as e:
            print(f"  [ERROR] {key}: {e}\n")
            failed.append(key)

    # Combined summary — this is what the dashboard loads
    summary = {
        "generated_at" : now_utc(),
        "count"        : len(all_data),
        "assets"       : {d["asset"]: d for d in all_data},
    }
    with open(ALL_FILE, "w") as f:
        json.dump(summary, f, indent=2)

    print("─"*52)
    print(f"  {'ASSET':<10} {'SCORE':>7}  ZONE")
    print("─"*52)
    for d in sorted(all_data, key=lambda x: x["composite"], reverse=True):
        sign = "+" if d["composite"] >= 0 else ""
        print(f"  {d['asset']:<10} {sign}{d['composite']:>5.1f}   "
              f"{zone_emoji(d['zone'])} {d['zone']}")
    print("─"*52)
    print(f"  ✓ {len(all_data)} fetched"
          + (f"  ✗ {len(failed)} failed: {', '.join(failed)}" if failed else ""))
    print("═"*52 + "\n")

# ── RUN SINGLE ────────────────────────────────────────────────
def run_single(key):
    key = key.upper()
    if key not in ASSET_PROFILES:
        print(f"\n  Unknown asset '{key}'. Run --list to see options.\n")
        sys.exit(1)
    print("\n" + "═"*52)
    print(f"  AISO v3.0 — {key}")
    print("═"*52 + "\n")
    data = fetch_asset(key)
    save_asset(data)
    with open(SUMMARY_FILE, "w") as f:
        json.dump(data, f, indent=2)
    sign = "+" if data["composite"] >= 0 else ""
    print(f"  ✓ Saved → scores/{key}.json")
    print(f"  → Paste into TradingView Bias Score: {sign}{data['composite']}")
    print("═"*52 + "\n")

def list_assets():
    cats = {}
    for k, p in ASSET_PROFILES.items():
        cats.setdefault(p["category"], []).append((k, p["label"]))
    print()
    for cat, items in cats.items():
        print(f"  {cat.upper()}")
        for k, lbl in items:
            print(f"    --asset {k:<10}  {lbl}")
    print()

# ── ENTRY ─────────────────────────────────────────────────────
if __name__ == "__main__":
    args = sys.argv[1:]
    if "--list"  in args: list_assets()
    elif "--all" in args: run_all()
    elif "--asset" in args:
        idx = args.index("--asset")
        if idx + 1 >= len(args):
            print("\n  --asset requires a value. E.g. --asset GOLD\n"); sys.exit(1)
        run_single(args[idx + 1])
    else:
        run_single("BTC")
