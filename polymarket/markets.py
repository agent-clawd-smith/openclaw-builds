"""
Polymarket market data fetcher.
Pulls active markets from the Gamma API.
"""
import requests
import json
from datetime import datetime

GAMMA_API = "https://gamma-api.polymarket.com"
CLOB_API = "https://clob.polymarket.com"


def get_active_markets(min_volume=10000, limit=50):
    """Fetch active markets sorted by volume."""
    url = f"{GAMMA_API}/markets"
    params = {
        "active": "true",
        "closed": "false",
        "limit": limit,
        "order": "volume",
        "ascending": "false",
        "volume_num_min": min_volume,
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    markets = r.json()
    if isinstance(markets, dict):
        markets = markets.get("data", markets.get("markets", []))
    return markets


def get_market_detail(condition_id):
    """Get full market detail including order book prices."""
    url = f"{CLOB_API}/markets/{condition_id}"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.json()


def summarize_market(m):
    """Return a clean summary dict for a market."""
    return {
        "condition_id": m.get("conditionId", m.get("condition_id", "")),
        "question": m.get("question", ""),
        "end_date": m.get("endDate", m.get("end_date_iso", "")),
        "volume": float(m.get("volume", 0)),
        "liquidity": float(m.get("liquidity", 0)),
        "outcomes": m.get("outcomes", []),
        "outcome_prices": m.get("outcomePrices", []),
        "fetched_at": datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    print("Fetching active high-volume markets...")
    markets = get_active_markets(min_volume=50000, limit=20)
    for m in markets:
        s = summarize_market(m)
        prices = dict(zip(s["outcomes"], s["outcome_prices"])) if s["outcomes"] else {}
        print(f"  ${s['volume']:>10,.0f} vol | {s['question'][:70]}")
        if prices:
            print(f"    Prices: {prices}")
    print(f"\nTotal: {len(markets)} markets")
