# Observability System

Tools for monitoring LLM API usage, spend, and budget management.

## Goal

Track weekly spending against our $100/week OpenRouter budget and automatically tier down models when thresholds are crossed.

## Architecture

### Core Components

**`usage-logger.py`** — Logs individual LLM API calls to weekly JSONL files.
- Schema: `{timestamp, model, input_tokens, output_tokens, cost_usd, task, session}`
- Writes to `memory/usage-YYYY-Wxx.jsonl` (one file per week)

**`budget-monitor.py`** — Monitors weekly spend and handles tier degradation.
- Reads current week's usage log
- Calculates total spend
- Determines budget tier (0-3)
- Reconfigures models and sends iMessage alerts when tier changes
- **✅ NEW (Phase 2.1):** Now uses live pricing from OpenRouter API via `pricing_cache.py`

**`pricing_cache.py`** ✅ — Fetches and caches live model pricing from OpenRouter API.
- Queries `/api/v1/models` endpoint
- Caches pricing data with 24h TTL in `memory/pricing-cache.json`
- Graceful fallback to hardcoded pricing if API unavailable
- Automatically used by `budget-monitor.py` for accurate cost calculations

**Usage:**
```python
from pricing_cache import get_pricing
pricing = get_pricing()  # Returns dict: model_id -> {input, output}
```

**CLI Test:**
```bash
python3 pricing_cache.py
```

### Budget Tiers

- **Tier 0** (< $60): Full power — Sonnet everywhere
- **Tier 1** ($60-80): Downshift coding to DeepSeek
- **Tier 2** ($80-95): Downshift main to Haiku, coding to DeepSeek
- **Tier 3** (> $95): Emergency — Haiku everywhere

## Integration

`budget-monitor.py` runs every 30 minutes via HEARTBEAT.md. On tier change, it:
1. Sends iMessage alert to Adam (+19163030339)
2. Reconfigures OpenClaw models via `openclaw config set`
3. Restarts the gateway to apply changes

## Phase Status

- ✅ **Phase 1:** Core scripts built and tested
- 🚧 **Phase 2 (In Progress):**
  - ✅ 2.1: Live pricing fetch from OpenRouter API
  - ⏳ 2.2: Auto-logging integration (extract from session transcripts)
  - ⏳ 2.3: Web dashboard UI
- 📋 **Phase 3 (Future):** Firecrawl credits, historical trend analysis

## Files

- `usage-logger.py` — Manual usage logging tool
- `budget-monitor.py` — Tier monitoring and degradation handler
- `pricing_cache.py` — Live pricing fetch and cache (NEW)
- `TODO.md` — Full task backlog for Phase 2+
- `memory/usage-YYYY-Wxx.jsonl` — Weekly usage logs
- `memory/budget-state.json` — Current tier state
- `memory/pricing-cache.json` — Cached OpenRouter pricing (24h TTL)
