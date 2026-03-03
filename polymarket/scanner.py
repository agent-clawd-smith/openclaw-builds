"""
Mirror signal scanner — checks top trader wallets for recent buys
and generates paper trade signals.
"""
import json
import os
import subprocess
from datetime import datetime, timezone
from paper_trader import log_trade, log_signal, portfolio_summary

SECRETS_PATH = os.path.expanduser("~/.openclaw/secrets.json")
DATA_API = "https://data-api.polymarket.com"
GAMMA_API = "https://gamma-api.polymarket.com"

# Only mirror trades placed in last N minutes
RECENCY_MINUTES = 60
# Minimum buy size to consider a signal meaningful
MIN_BUY_SIZE = 500


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


def load_wallets():
    if not os.path.exists(SECRETS_PATH):
        return {}
    with open(SECRETS_PATH) as f:
        return json.load(f).get("polymarket_wallets", {})


def get_recent_buys(address, since_minutes=RECENCY_MINUTES):
    data = curl_json(f"{DATA_API}/activity?user={address}&limit=20")
    if not data or not isinstance(data, list):
        return []
    cutoff = datetime.now(timezone.utc).timestamp() - (since_minutes * 60)
    buys = []
    for t in data:
        if t.get("type") != "TRADE" or t.get("side") != "BUY":
            continue
        if float(t.get("timestamp", 0)) < cutoff:
            continue
        size = float(t.get("usdcSize", 0))
        if size < MIN_BUY_SIZE:
            continue
        buys.append(t)
    return buys


def get_market_price(condition_id):
    """Get current YES price for a market."""
    data = curl_json(f"{GAMMA_API}/markets/{condition_id}")
    if not data:
        return None
    prices = data.get("outcomePrices", [])
    outcomes = data.get("outcomes", [])
    if prices and outcomes:
        price_map = dict(zip(outcomes, prices))
        return price_map
    return None


def scan_and_signal():
    wallets = load_wallets()
    if not wallets:
        print("No wallets configured.")
        return []

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Scanning {len(wallets)} wallets for recent buys (last {RECENCY_MINUTES}min, min ${MIN_BUY_SIZE})...")

    all_signals = []
    seen_conditions = {}  # condition_id -> list of (wallet, trade)

    for address, label in wallets.items():
        buys = get_recent_buys(address)
        if buys:
            print(f"  {label}: {len(buys)} qualifying buy(s)")
        for t in buys:
            cid = t.get("conditionId", "")
            if cid not in seen_conditions:
                seen_conditions[cid] = []
            seen_conditions[cid].append((label, t))

    # Markets with multiple top traders buying = stronger signal
    for cid, entries in seen_conditions.items():
        confidence = min(0.5 + (len(entries) * 0.15), 0.95)
        first = entries[0][1]
        title = first.get("title", "")
        outcome = first.get("outcome", "Yes")
        price = float(first.get("price", 0))
        total_size = sum(float(e[1].get("usdcSize", 0)) for e in entries)
        wallets_buying = [e[0] for e in entries]

        signal = {
            "condition_id": cid,
            "title": title,
            "outcome": outcome,
            "price": price,
            "total_mirror_size": total_size,
            "wallets": wallets_buying,
            "confidence": confidence,
            "timestamp": datetime.utcnow().isoformat(),
        }
        all_signals.append(signal)

        # Log signal
        log_signal(cid, "mirror", outcome, confidence,
                   raw=json.dumps({"wallets": wallets_buying, "total_size": total_size}))

        print(f"\n  [SIGNAL] {title[:65]}")
        print(f"    Outcome: {outcome} @ {price:.2f}")
        print(f"    Mirror wallets: {', '.join(wallets_buying)}")
        print(f"    Combined size: ${total_size:,.0f} | Confidence: {confidence:.0%}")

        # Paper trade: size proportional to confidence, max $50 simulated
        paper_size = round(confidence * 50, 2)
        log_trade(
            condition_id=cid,
            question=title,
            outcome=outcome,
            price=price,
            size=paper_size,
            signal="mirror",
            confidence=confidence,
            notes=f"Mirroring: {', '.join(wallets_buying)}"
        )

    if not all_signals:
        print("  No qualifying signals found.")

    print()
    portfolio_summary()
    return all_signals


if __name__ == "__main__":
    scan_and_signal()
