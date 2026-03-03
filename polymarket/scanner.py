"""
Market scanner — the main autonomous loop.
Checks top trader OPEN POSITIONS, identifies mirror signals,
logs paper trades.
"""
import json, os, sys, time
from datetime import datetime, timezone

DATA_API = "https://data-api.polymarket.com"
GAMMA_API = "https://gamma-api.polymarket.com"
CLOB_API  = "https://clob.polymarket.com"
SECRETS_PATH = os.path.expanduser("~/.openclaw/secrets.json")
TRADES_PATH  = os.path.expanduser("~/.openclaw/workspace/polymarket/paper_trades.json")

MIN_POSITION_VALUE = 5000   # Min USD position to mirror
PAPER_TRADE_SIZE   = 100    # Simulated USD per trade
MAX_POSITIONS      = 10


def fetch(url):
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": "AgentClawdSmith/1.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def load_wallets():
    if not os.path.exists(SECRETS_PATH):
        return {}
    with open(SECRETS_PATH) as f:
        return json.load(f).get("polymarket_wallets", {})


def get_open_positions(address):
    """Get currently open positions with real value."""
    url = f"{DATA_API}/positions?user={address}&sizeThreshold=100&limit=50&redeemable=false"
    try:
        data = fetch(url)
        positions = data if isinstance(data, list) else []
        return [p for p in positions if float(p.get("currentValue", 0)) > 10]
    except:
        return []


def get_clob_price(condition_id, outcome="Yes"):
    """Get current market price from CLOB API."""
    import urllib.request
    url = f"{CLOB_API}/markets/{condition_id}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AgentClawdSmith/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            m = json.loads(r.read())
        if m.get("closed"):
            return None
        for token in m.get("tokens", []):
            if token.get("outcome", "").lower() == outcome.lower():
                return float(token.get("price", 0))
        # fallback: first token
        tokens = m.get("tokens", [])
        return float(tokens[0]["price"]) if tokens else None
    except:
        return None


def load_trades():
    if os.path.exists(TRADES_PATH):
        with open(TRADES_PATH) as f:
            return json.load(f)
    return []


def save_trades(trades):
    with open(TRADES_PATH, "w") as f:
        json.dump(trades, f, indent=2)


def print_portfolio(trades):
    open_t  = [t for t in trades if not t.get("resolved")]
    closed_t = [t for t in trades if t.get("resolved")]
    pnl = sum(t.get("pnl", 0) or 0 for t in closed_t)
    print(f"\n=== PAPER PORTFOLIO ===")
    print(f"Open: {len(open_t)} | Closed: {len(closed_t)} | Total P&L: ${pnl:+.2f}")
    for t in open_t:
        print(f"  #{t['id']} {t['outcome']} @ {t['entry_price']:.3f} | {t['title'][:55]}")
        print(f"       Signal: {t['signal_source']} (${t['signal_size']:,.0f})")
    print("=======================\n")


def run_scan():
    wallets = load_wallets()
    trades  = load_trades()
    open_count = sum(1 for t in trades if not t.get("resolved"))
    open_markets = {t["condition_id"] for t in trades if not t.get("resolved")}

    print(f"[{datetime.now():%H:%M:%S}] Scanning {len(wallets)} wallets...")

    signals = []
    for address, name in wallets.items():
        positions = get_open_positions(address)
        for pos in positions:
            val = float(pos.get("currentValue", 0))
            if val < MIN_POSITION_VALUE:
                continue
            signals.append({
                "source":       f"mirror:{name}",
                "condition_id": pos.get("conditionId", ""),
                "title":        pos.get("title", ""),
                "outcome":      pos.get("outcome", "Yes"),
                "price":        float(pos.get("curPrice", pos.get("price", 0))),
                "signal_size":  val,
            })
        time.sleep(0.2)

    # Deduplicate by condition_id, keep largest signal
    seen = {}
    for s in signals:
        cid = s["condition_id"]
        if cid not in seen or s["signal_size"] > seen[cid]["signal_size"]:
            seen[cid] = s
    signals = sorted(seen.values(), key=lambda x: x["signal_size"], reverse=True)

    print(f"Found {len(signals)} unique open-position signals ≥ ${MIN_POSITION_VALUE:,}")

    new_trades = 0
    for sig in signals:
        if open_count + new_trades >= MAX_POSITIONS:
            break
        if sig["condition_id"] in open_markets:
            continue  # already in this market

        price = get_clob_price(sig["condition_id"], sig["outcome"])
        if price is None or price > 0.97 or price < 0.02:
            continue  # closed or at extremes

        trade = {
            "id":            len(trades) + 1,
            "timestamp":     datetime.now(timezone.utc).isoformat(),
            "condition_id":  sig["condition_id"],
            "title":         sig["title"],
            "outcome":       sig["outcome"],
            "entry_price":   price,
            "paper_size":    PAPER_TRADE_SIZE,
            "signal_source": sig["source"],
            "signal_size":   sig["signal_size"],
            "resolved":      False,
            "resolution":    None,
            "pnl":           None,
        }
        trades.append(trade)
        open_markets.add(sig["condition_id"])
        new_trades += 1
        print(f"  [PAPER #{trade['id']}] {sig['outcome']} @ {price:.3f} | {sig['title'][:58]}")
        print(f"    Mirror: {sig['source']} has ${sig['signal_size']:,.0f} on this")
        time.sleep(0.2)

    save_trades(trades)
    if new_trades == 0 and not signals:
        print("No new signals.")
    print_portfolio(trades)


if __name__ == "__main__":
    run_scan()
