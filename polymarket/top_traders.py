"""
Top trader tracker for Polymarket.
Identifies high-profit wallets via on-chain data and uses their
positions as signals.

SECURITY: Tracked wallet addresses are stored in ~/.openclaw/secrets.json
and are NEVER committed to git.
"""
import requests
import json
import os
from datetime import datetime

SECRETS_PATH = os.path.expanduser("~/.openclaw/secrets.json")
DATA_API = "https://data-api.polymarket.com"
GAMMA_API = "https://gamma-api.polymarket.com"


def load_target_wallets():
    """Load tracked wallet addresses from secrets file (gitignored)."""
    if not os.path.exists(SECRETS_PATH):
        return {}
    with open(SECRETS_PATH) as f:
        secrets = json.load(f)
    return secrets.get("polymarket_wallets", {})


def save_target_wallets(wallets):
    """Save tracked wallets to secrets file."""
    if os.path.exists(SECRETS_PATH):
        with open(SECRETS_PATH) as f:
            secrets = json.load(f)
    else:
        secrets = {}
    secrets["polymarket_wallets"] = wallets
    with open(SECRETS_PATH, "w") as f:
        json.dump(secrets, f, indent=2)
    print(f"Saved {len(wallets)} tracked wallets to secrets.json")


def get_leaderboard_via_browser():
    """
    Placeholder — Polymarket leaderboard requires JS rendering.
    Use browser tool or scrape via alternative means.
    Returns known top wallet addresses from research.
    """
    # TODO: automate leaderboard scraping via browser tool
    # For now, seed with manually identified wallets from Polymarket leaderboard
    return {}


def get_wallet_positions(address):
    """Fetch current open positions for a wallet."""
    url = f"{DATA_API}/positions"
    params = {"user": address, "sizeThreshold": "0.01", "limit": 50}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data if isinstance(data, list) else data.get("data", [])
    except Exception as e:
        print(f"Error fetching positions for {address}: {e}")
        return []


def get_wallet_trades(address, limit=20):
    """Fetch recent trades for a wallet via activity endpoint."""
    url = f"{DATA_API}/activity"
    params = {"user": address, "limit": limit}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data if isinstance(data, list) else data.get("data", [])
    except Exception as e:
        print(f"Error fetching trades for {address}: {e}")
        return []


def get_recent_buys(address, limit=10):
    """Get only recent BUY trades for a wallet — the actionable signal."""
    trades = get_wallet_trades(address, limit=limit * 3)
    buys = [t for t in trades if t.get("type") == "TRADE" and t.get("side") == "BUY"]
    return buys[:limit]


def get_mirror_signals(min_position_size=100):
    """
    Check all tracked wallets and return their current positions
    as trading signals.
    """
    wallets = load_target_wallets()
    if not wallets:
        print("No target wallets configured. Add wallets to ~/.openclaw/secrets.json")
        return []

    signals = []
    for address, label in wallets.items():
        positions = get_wallet_positions(address)
        for pos in positions:
            size = float(pos.get("size", pos.get("currentValue", 0)))
            if size < min_position_size:
                continue
            signals.append({
                "source": f"mirror:{label}",
                "condition_id": pos.get("conditionId", pos.get("market", "")),
                "outcome": pos.get("outcome", ""),
                "price": float(pos.get("avgPrice", pos.get("price", 0))),
                "size": size,
                "wallet": address,
                "timestamp": datetime.utcnow().isoformat(),
            })
    return signals


if __name__ == "__main__":
    wallets = load_target_wallets()
    print(f"Tracking {len(wallets)} wallets")
    if wallets:
        for addr, label in list(wallets.items())[:3]:
            print(f"\n  {label} ({addr[:10]}...)")
            positions = get_wallet_positions(addr)
            print(f"  Open positions: {len(positions)}")
            for p in positions[:3]:
                print(f"    {p}")
    else:
        print("No wallets configured yet.")
        print("Populate polymarket_wallets in ~/.openclaw/secrets.json")
        print("Format: {\"address\": \"label\"}")
