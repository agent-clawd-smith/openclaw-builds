"""
Mirror signal scanner.
Checks top trader wallets for recent buys and generates paper trade signals.
Runs periodically during agent downtime.
"""
import json
import os
import sqlite3
import subprocess
from datetime import datetime, timezone
from collections import defaultdict

SECRETS_PATH = os.path.expanduser("~/.openclaw/secrets.json")
DB_PATH = os.path.expanduser("~/.openclaw/workspace/polymarket/paper_trades.db")
DATA_API = "https://data-api.polymarket.com"
GAMMA_API = "https://gamma-api.polymarket.com"
LOOKBACK_HOURS = 6  # Only look at trades in the last N hours
MIN_BUY_SIZE = 5000  # Minimum USDC size to consider signal-worthy


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


def get_recent_buys(address, lookback_hours=LOOKBACK_HOURS):
    """Fetch recent BUY trades for a wallet within lookback window."""
    data = curl_json(f"{DATA_API}/activity?user={address}&limit=50")
    if not data or not isinstance(data, list):
        return []
    cutoff = datetime.now(timezone.utc).timestamp() - (lookback_hours * 3600)
    buys = [
        t for t in data
        if t.get("type") == "TRADE"
        and t.get("side") == "BUY"
        and t.get("timestamp", 0) > cutoff
        and float(t.get("usdcSize", 0)) >= MIN_BUY_SIZE
    ]
    return buys


def get_market_price(condition_id):
    """Get current YES price for a market."""
    data = curl_json(f"{GAMMA_API}/markets/{condition_id}")
    if not data:
        return None
    prices = data.get("outcomePrices", [])
    outcomes = data.get("outcomes", [])
    if prices and outcomes:
        price_map = dict(zip(outcomes, [float(p) for p in prices]))
        return price_map
    return None


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            condition_id TEXT,
            question TEXT,
            outcome TEXT,
            price REAL,
            size REAL,
            signal TEXT,
            signal_confidence REAL,
            notes TEXT,
            resolved INTEGER DEFAULT 0,
            resolution TEXT,
            pnl REAL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            condition_id TEXT,
            source TEXT,
            signal TEXT,
            confidence REAL,
            raw TEXT
        )
    """)
    conn.commit()
    return conn


def log_signal(conn, condition_id, source, signal, confidence, raw=""):
    c = conn.cursor()
    c.execute("""
        INSERT INTO signals (timestamp, condition_id, source, signal, confidence, raw)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (datetime.utcnow().isoformat(), condition_id, source, signal, confidence, raw))
    conn.commit()


def log_paper_trade(conn, condition_id, question, outcome, price, size, signal, confidence, notes=""):
    c = conn.cursor()
    # Check for duplicate (same market + outcome already open)
    c.execute("SELECT id FROM trades WHERE condition_id=? AND outcome=? AND resolved=0", (condition_id, outcome))
    if c.fetchone():
        return None  # Already have this position
    c.execute("""
        INSERT INTO trades (timestamp, condition_id, question, outcome, price, size, signal, signal_confidence, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (datetime.utcnow().isoformat(), condition_id, question, outcome, price, size, signal, confidence, notes))
    conn.commit()
    return c.lastrowid


def run_scan():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Running mirror signal scan...")
    wallets = load_wallets()
    if not wallets:
        print("No wallets configured.")
        return

    conn = init_db()
    # Aggregate signals by market
    market_signals = defaultdict(list)

    for address, name in wallets.items():
        buys = get_recent_buys(address)
        for buy in buys:
            cid = buy.get("conditionId", "")
            outcome = buy.get("outcome", "Yes")
            usdc = float(buy.get("usdcSize", 0))
            price = float(buy.get("price", 0))
            title = buy.get("title", "")
            signal_str = f"{name} bought {outcome} @ {price:.2f} (${usdc:,.0f})"
            market_signals[cid].append({
                "wallet": name,
                "outcome": outcome,
                "price": price,
                "usdc": usdc,
                "title": title,
                "signal": signal_str,
            })
            log_signal(conn, cid, f"mirror:{name}", outcome, min(usdc / 50000, 1.0), signal_str)

    # Find markets with multiple top traders aligned
    new_trades = 0
    for cid, signals in market_signals.items():
        if not signals:
            continue
        title = signals[0]["title"]
        # Count unique wallets and dominant outcome
        outcome_votes = defaultdict(float)
        for s in signals:
            outcome_votes[s["outcome"]] += s["usdc"]
        top_outcome = max(outcome_votes, key=outcome_votes.get)
        total_usdc = sum(outcome_votes.values())
        wallet_count = len(set(s["wallet"] for s in signals))
        confidence = min(wallet_count / 3.0, 1.0)  # 3 wallets = full confidence
        avg_price = sum(s["price"] for s in signals if s["outcome"] == top_outcome) / max(
            len([s for s in signals if s["outcome"] == top_outcome]), 1)

        note = f"{wallet_count} top traders | ${total_usdc:,.0f} total | {', '.join(set(s['wallet'] for s in signals))}"
        print(f"  Signal [{confidence:.0%} conf]: {top_outcome} on '{title[:60]}' — {note}")

        # Paper trade if confidence > 30% and price < 0.90 (not already near resolved)
        if confidence >= 0.33 and avg_price < 0.90:
            paper_size = min(total_usdc / 100, 500)  # 1% of whale size, max $500
            trade_id = log_paper_trade(conn, cid, title, top_outcome, avg_price, paper_size,
                                       "mirror", confidence, note)
            if trade_id:
                print(f"    → PAPER TRADE #{trade_id}: {top_outcome} @ {avg_price:.2f}, ${paper_size:.2f}")
                new_trades += 1

    conn.close()
    print(f"Scan complete. {len(market_signals)} markets with signals, {new_trades} new paper trades.")
    return new_trades


if __name__ == "__main__":
    run_scan()

    # Print portfolio summary
    conn = init_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*), SUM(size) FROM trades WHERE resolved=0")
    open_count, exposure = c.fetchone()
    c.execute("SELECT COUNT(*), SUM(pnl) FROM trades WHERE resolved=1")
    closed, pnl = c.fetchone()
    conn.close()
    print(f"\n=== PAPER PORTFOLIO ===")
    print(f"Open: {open_count or 0} | Exposure: ${exposure or 0:.2f}")
    print(f"Closed: {closed or 0} | P&L: ${pnl or 0:+.2f}")
