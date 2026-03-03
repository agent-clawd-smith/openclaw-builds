"""
Mirror signal scanner.
Checks top trader wallets for recent activity, cross-references with
open markets, and generates paper trade signals.
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

# Use curl instead of requests to avoid dependency issues
def curl_json(url):
    result = subprocess.run(
        ["curl", "-s", "--max-time", "10", url],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except Exception:
        return None


SECRETS_PATH = os.path.expanduser("~/.openclaw/secrets.json")
DATA_API = "https://data-api.polymarket.com"
GAMMA_API = "https://gamma-api.polymarket.com"

# How recent a trade must be to count as a signal (seconds)
RECENCY_WINDOW = 3600  # 1 hour


def load_wallets():
    if not os.path.exists(SECRETS_PATH):
        return {}
    with open(SECRETS_PATH) as f:
        return json.load(f).get("polymarket_wallets", {})


def get_recent_buys(address, label):
    """Fetch recent BUY trades for a wallet."""
    data = curl_json(f"{DATA_API}/activity?user={address}&limit=30")
    if not data or not isinstance(data, list):
        return []

    now = datetime.now(timezone.utc).timestamp()
    buys = []
    for t in data:
        if t.get("type") != "TRADE" or t.get("side") != "BUY":
            continue
        age = now - t.get("timestamp", 0)
        if age > RECENCY_WINDOW:
            continue
        buys.append({
            "wallet": label,
            "address": address,
            "condition_id": t.get("conditionId", ""),
            "title": t.get("title", ""),
            "outcome": t.get("outcome", ""),
            "price": float(t.get("price", 0)),
            "usdc_size": float(t.get("usdcSize", 0)),
            "timestamp": t.get("timestamp", 0),
            "age_minutes": round(age / 60, 1),
        })
    return buys


def get_market_price(condition_id):
    """Get current YES price for a market."""
    data = curl_json(f"{GAMMA_API}/markets/{condition_id}")
    if not data:
        return None
    prices = data.get("outcomePrices", [])
    outcomes = data.get("outcomes", [])
    if prices and outcomes:
        return dict(zip(outcomes, [float(p) for p in prices]))
    return None


def scan():
    wallets = load_wallets()
    if not wallets:
        print("No wallets configured.")
        return []

    print(f"\n{'='*60}")
    print(f"MIRROR SCAN — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Checking {len(wallets)} wallets | window: last {RECENCY_WINDOW//60} min")
    print(f"{'='*60}")

    all_signals = []
    for address, label in wallets.items():
        buys = get_recent_buys(address, label)
        if buys:
            for b in buys:
                print(f"\n  🟢 {label} bought {b['outcome']} @ {b['price']:.2f}")
                print(f"     Market: {b['title'][:65]}")
                print(f"     Size: ${b['usdc_size']:,.0f} | {b['age_minutes']}m ago")
                all_signals.append(b)

    if not all_signals:
        print("\n  No fresh buys from tracked wallets in the last hour.")

    # Deduplicate by condition_id — if multiple whales bought same market, stronger signal
    from collections import defaultdict
    market_signals = defaultdict(list)
    for s in all_signals:
        market_signals[s["condition_id"]].append(s)

    print(f"\n{'='*60}")
    print("SIGNAL SUMMARY")
    print(f"{'='*60}")
    for cid, signals in sorted(market_signals.items(), key=lambda x: len(x[1]), reverse=True):
        wallets_buying = [s["wallet"] for s in signals]
        total_size = sum(s["usdc_size"] for s in signals)
        outcome = signals[0]["outcome"]
        price = signals[0]["price"]
        title = signals[0]["title"]
        strength = "🔴 STRONG" if len(signals) >= 2 else "🟡 WEAK"
        print(f"\n  {strength} | {len(signals)} whale(s) | ${total_size:,.0f} total")
        print(f"  {outcome} @ {price:.2f} — {title[:60]}")
        print(f"  Buyers: {', '.join(wallets_buying)}")

    return all_signals


if __name__ == "__main__":
    signals = scan()

    if signals:
        # Auto-log to paper trader
        sys.path.insert(0, os.path.dirname(__file__))
        from paper_trader import log_trade, init_db
        init_db()
        logged = set()
        for s in signals:
            key = f"{s['condition_id']}:{s['outcome']}"
            if key in logged:
                continue
            logged.add(key)
            log_trade(
                condition_id=s["condition_id"],
                question=s["title"],
                outcome=s["outcome"],
                price=s["price"],
                size=min(s["usdc_size"] * 0.1, 100),  # paper trade at 10% of whale size, max $100
                signal=f"mirror:{s['wallet']}",
                confidence=0.6,
                notes=f"Mirror signal from {s['wallet']}, ${s['usdc_size']:,.0f} buy"
            )
