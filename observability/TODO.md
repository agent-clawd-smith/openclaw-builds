# Observability Project TODO

## Phase 1 ✅ (Complete)
- [x] Core scripts: `usage-logger.py`, `budget-monitor.py`
- [x] Test with dummy data
- [x] Integrate budget monitor into HEARTBEAT.md

## Phase 2 (In Progress — Autonomous Work)
- [ ] **Auto-logging integration** — Hook into agent loop to automatically log every LLM call
  - Extract usage from session transcripts during heartbeat
  - Call `usage-logger.py` with real data
  - Test with a full day of actual usage
- [x] **Fetch live pricing from OpenRouter API** — Replace hardcoded PRICING dict ✅ (2026-03-04)
  - Query `/api/v1/models` on startup or daily
  - Cache pricing data, refresh every 24h
  - Handle missing models gracefully
  - **COMPLETE:** `pricing_cache.py` integrated into `budget-monitor.py`
- [ ] **Observability UI** — Web dashboard (Adam's preference, 2026-03-03)
  - Lightweight local server (Flask or static HTML + JS)
  - Real-time spend tracking, tier visualization, weekly burn rate
  - Accessible at http://localhost:PORT
  - Auto-refresh or live updates via SSE/polling

## Phase 3 (Future)
- [ ] Track Firecrawl credits
- [ ] Track other consumables (if any)
- [ ] Historical trend analysis (spending velocity, tier prediction)

## Notes
- Standing permission from Adam (March 2): refactor/improve things I've built
- Work during downtime, surface milestones via iMessage
- Don't wait for prompting — just do it and report back
