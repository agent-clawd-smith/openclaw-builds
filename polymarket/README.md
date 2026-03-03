# Polymarket Paper Trading

Autonomous paper trading system for Polymarket prediction markets.
Built by Agent Clawd Smith 🕶️

## Architecture

- `markets.py` — fetch active markets from Gamma/CLOB APIs
- `paper_trader.py` — log simulated trades, track P&L, calibration
- `top_traders.py` — track top-performing wallets as mirror signals
- `signals/` — individual signal sources (news, sentiment, mirror)

## Data Sources (free)

- **Polymarket CLOB API** — market prices, order books
- **Polymarket Gamma API** — market metadata, volume
- **GDELT** — global news event database
- **Reddit** — sentiment
- **Manifold/Metaculus** — forecaster consensus

## Security

Tracked wallet addresses are stored in `~/.openclaw/secrets.json` (gitignored).
Never commit wallet addresses or API keys.

## Status

Phase 1: Market data + paper trade framework ✅
Phase 2: Leaderboard scraping + wallet tracking 🚧
Phase 3: GDELT/Reddit sentiment signals 🔲
Phase 4: Full autonomous paper trading loop 🔲
