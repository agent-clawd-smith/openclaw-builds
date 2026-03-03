"""
Mirror signal scanner — checks top trader wallets for recent buys,
cross-references with open markets, generates paper trade signals.

Run this during heartbeats to find actionable opportunities.
"""
import json
import os
import sys
import subprocess
from datetime import datetime, timezone

SECRETS_PATH = os.path.expanduser("~/.openclaw/secrets.json")
DATA_API = "https://data-api.polymarket.com"
GAMMA_API = "https://gamma-api.polymarket.com"

# Only mirror trades above this size (filters noise)
MIN_TRADE_SIZE_USDC = 500

# Only consider trades in the last N seconds
LOOKBACK_SECONDS = 1800  # 30 minutes


def curl_json(url):
    result = subprocess.run(
        ["curl", "-s", "--max-time", "10", url],
        capture_output=True, text=True
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    try:
        return json.loads(result.stdout)
    except Exception:
        return None


def load_wallets():
    if not os.path.exists(SECRETS_PATH):
        return {}
    with open(SECRETS_PATH) as f:
        return json.load(f).get("polymarket_wallets", {})


def get_recent_buys(address, label):
    """Get BUY trades from the last 30 minutes above minimum size."""
    url = f"{DATA_API}/activity?user={address}&limit=20"
    trades = curl_json(url) or []
    now = datetime.now(timezone.utc).timestamp()
    signals = []
    for t in trades:
        if t.get("type") != "TRADE" or t.get("side") != "BUY":
            continue
        age = now - t.get("timestamp", 0)
        if age > LOOKBACK_SECONDS:
            continue
        usdc = float(t.get("usdcSize", 0))
        if usdc < MIN_TRADE_SIZE_USDC:
            continue
        signals.append({
            "wallet": label,
            "address": address,
            "condition_id": t.get("conditionId", ""),
            "title": t.get("title", ""),
            "outcome": t.get("outcome", ""),
            "price": float(t.get("price", 0)),
            "usdc_size": usdc,
            "share_size": float(t.get("size", 0)),
            "timestamp": t.get("timestamp", 0),
            "age_minutes": round(age / 60, 1),
        })
    return signals


def scan_all_wallets():
    """Scan all tracked wallets and return consolidated signals."""
    wallets = load_wallets()
    if not wallets:
        print("No wallets configured.")
        return []

    all_signals = []
    for address, label in wallets.items():
        buys = get_recent_buys(address, label)
        if buys:
            print(f"  [{label}] {len(buys)} recent buy(s)")
            all_signals.extend(buys)

    # Deduplicate by condition_id+outcome — if multiple whales buying same thing, stronger signal
    seen = {}
    for s in all_signals:
        key = f"{s['condition_id']}:{s['outcome']}"
        if key not in seen:
            seen[key] = {"signal": s, "count": 1, "total_usdc": s["usdc_size"]}
        else:
            seen[key]["count"] += 1
            seen[key]["total_usdc"] += s["usdc_size"]

    consolidated = []
    for key, v in seen.items():
        entry = v["signal"].copy()
        entry["whale_count"] = v["count"]
        entry["total_usdc"] = v["total_usdc"]
        consolidated.append(entry)

    # Sort by whale count desc, then total USDC
    consolidated.sort(key=lambda x: (x["whale_count"], x["total_usdc"]), reverse=True)
    return consolidated


def generate_paper_trade(signal):
    """Decide whether to paper trade a signal using simple rules."""
    # Rule 1: Multiple whales = stronger signal
    if signal["whale_count"] >= 2:
        confidence = 0.75
    else:
        confidence = 0.55

    # Rule 2: Skip if price already > 0.85 (not much upside)
    if signal["price"] > 0.85:
        return None, "price too high"

    # Rule 3: Skip if price < 0.05 (too risky)
    if signal["price"] < 0.05:
        return None, "price too low/risky"

    # Paper trade size: flat $50 per signal (paper money)
    size = 50.0

    return {
        "condition_id": signal["condition_id"],
        "question": signal["title"],
        "outcome": signal["outcome"],
        "price": signal["price"],
        "size": size,
        "signal": f"mirror:{signal['wallet']} (x{signal['whale_count']} whales, ${signal['total_usdc']:,.0f} USDC)",
        "confidence": confidence,
    }, None


if __name__ == "__main__":
    print(f"\n🔍 Scanning {len(load_wallets())} wallets for signals...")
    print(f"   Lookback: {LOOKBACK_SECONDS//60} min | Min trade: ${MIN_TRADE_SIZE_USDC:,} USDC\n")

    signals = scan_all_wallets()

    if not signals:
        print("No signals found in the last 30 minutes.")
        sys.exit(0)

    print(f"\n📊 {len(signals)} consolidated signal(s):\n")
    for s in signals:
        trade, reason = generate_paper_trade(s)
        if trade:
            print(f"  ✅ PAPER TRADE: {s['outcome']} @ {s['price']:.2f}")
            print(f"     Market: {s['title'][:65]}")
            print(f"     Signal: {s['whale_count']} whale(s), ${s['total_usdc']:,.0f} USDC total")
            print(f"     Age: {s['age_minutes']} min ago")

            # Log to paper trader
            sys.path.insert(0, os.path.dirname(__file__))
            from paper_trader import log_trade
            log_trade(
                trade["condition_id"], trade["question"], trade["outcome"],
                trade["price"], trade["size"], trade["signal"], trade["confidence"]
            )
        else:
            print(f"  ⏭  SKIP: {s['outcome']} @ {s['price']:.2f} ({reason})")
            print(f"     Market: {s['title'][:65]}")
        print()

    # Summary
    from paper_trader import portfolio_summary
    portfolio_summary()
