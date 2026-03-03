"""
Mirror signal scanner.
Checks top trader wallets for recent buys and logs paper trades.
Run periodically during heartbeats.
"""
import json
import os
import sys
import subprocess
from datetime import datetime, timezone

# Use curl for HTTP to avoid import issues
def curl_get(url):
    result = subprocess.run(
        ["curl", "-s", "--max-time", "10", url],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except:
        return None


def load_wallets():
    secrets_path = os.path.expanduser("~/.openclaw/secrets.json")
    if not os.path.exists(secrets_path):
        return {}
    with open(secrets_path) as f:
        return json.load(f).get("polymarket_wallets", {})


def get_recent_buys(address, since_minutes=35):
    """Get BUY trades from the last N minutes for a wallet."""
    data = curl_get(f"https://data-api.polymarket.com/activity?user={address}&limit=20")
    if not data or not isinstance(data, list):
        return []
    cutoff = datetime.now(timezone.utc).timestamp() - (since_minutes * 60)
    buys = [
        t for t in data
        if t.get("type") == "TRADE"
        and t.get("side") == "BUY"
        and t.get("timestamp", 0) > cutoff
    ]
    return buys


def get_current_price(condition_id, outcome_index=0):
    """Get current market price for an outcome."""
    data = curl_get(f"https://gamma-api.polymarket.com/markets?conditionIds={condition_id}")
    if not data or not isinstance(data, list) or not data:
        return None
    market = data[0]
    prices = market.get("outcomePrices", [])
    try:
        return float(prices[outcome_index])
    except:
        return None


def load_state():
    state_path = os.path.expanduser("~/.openclaw/workspace/polymarket/scanner_state.json")
    if os.path.exists(state_path):
        with open(state_path) as f:
            return json.load(f)
    return {"seen_txns": [], "last_run": None}


def save_state(state):
    state_path = os.path.expanduser("~/.openclaw/workspace/polymarket/scanner_state.json")
    # Keep seen_txns bounded
    state["seen_txns"] = state["seen_txns"][-500:]
    state["last_run"] = datetime.utcnow().isoformat()
    with open(state_path, "w") as f:
        json.dump(state, f, indent=2)


def run_scan():
    wallets = load_wallets()
    state = load_state()
    seen = set(state.get("seen_txns", []))
    signals = []

    print(f"[{datetime.utcnow().strftime('%H:%M:%S')}] Scanning {len(wallets)} wallets...")

    for address, name in wallets.items():
        buys = get_recent_buys(address, since_minutes=35)
        for trade in buys:
            txn = trade.get("transactionHash", "")
            if not txn or txn in seen:
                continue
            seen.add(txn)

            condition_id = trade.get("conditionId", "")
            outcome = trade.get("outcome", "")
            price = float(trade.get("price", 0))
            usdc_size = float(trade.get("usdcSize", 0))
            title = trade.get("title", "")
            outcome_index = trade.get("outcomeIndex", 0)

            # Only flag meaningful size trades
            if usdc_size < 500:
                continue

            current_price = get_current_price(condition_id, outcome_index)

            signal = {
                "wallet": name,
                "address": address[:12] + "...",
                "title": title,
                "outcome": outcome,
                "entry_price": price,
                "current_price": current_price,
                "size_usdc": usdc_size,
                "condition_id": condition_id,
                "txn": txn[:16] + "...",
                "timestamp": trade.get("timestamp"),
            }
            signals.append(signal)
            print(f"  🎯 SIGNAL: {name} bought {outcome} @ {price:.2f} (${usdc_size:,.0f}) — {title[:60]}")
            if current_price and abs(current_price - price) > 0.02:
                print(f"     Current price: {current_price:.2f} (moved {current_price - price:+.2f})")

    state["seen_txns"] = list(seen)
    save_state(state)

    if not signals:
        print("  No new signals.")

    return signals


def log_paper_trades(signals):
    """Log mirror signals as paper trades."""
    if not signals:
        return

    # Import paper trader
    sys.path.insert(0, os.path.dirname(__file__))
    from paper_trader import log_trade, init_db
    init_db()

    PAPER_SIZE = 100  # Simulate $100 per mirrored trade

    for s in signals:
        price = s["current_price"] or s["entry_price"]
        log_trade(
            condition_id=s["condition_id"],
            question=s["title"],
            outcome=s["outcome"],
            price=price,
            size=PAPER_SIZE,
            signal=f"mirror:{s['wallet']}",
            confidence=0.6,
            notes=f"Mirrored {s['wallet']} buy of ${s['size_usdc']:,.0f} @ {s['entry_price']:.2f}"
        )


if __name__ == "__main__":
    signals = run_scan()
    if signals:
        log_paper_trades(signals)
        print(f"\n{len(signals)} signals logged as paper trades.")
    else:
        print("Scan complete — nothing to trade.")
