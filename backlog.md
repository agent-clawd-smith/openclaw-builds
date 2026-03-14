# Project Backlog

**Last updated:** 2026-03-04 11:05 PST  
**Weekly budget:** $100 ($0.31 spent so far this week)

## Active Projects

### Observability Phase 2
**Status:** In progress  
**Priority:** High  
**Decision:** Web dashboard UI (confirmed by Adam 2026-03-03 21:23 PST)

#### Tasks
1. **Live pricing fetch from OpenRouter API** (NEXT TASK - assigned below)
   - Query `/api/v1/models` on startup or daily
   - Cache pricing data, refresh every 24h
   - Handle missing models gracefully
   - Estimated effort: 2-3 hours, ~50k tokens
   
2. **Auto-logging integration**
   - Hook into agent loop to automatically log every LLM call
   - Extract usage from session transcripts during heartbeat
   - Call `usage-logger.py` with real data
   - Estimated effort: 3-4 hours, ~75k tokens

3. **Web dashboard UI** 
   - Lightweight local server (Flask or static HTML + JS)
   - Real-time spend tracking, tier visualization, weekly burn rate
   - Accessible at http://localhost:PORT
   - Auto-refresh or live updates
   - Estimated effort: 4-6 hours, ~100k tokens

### Polymarket Signal Expansion
**Status:** Research phase  
**Priority:** Medium

#### Tasks
1. **Sports base rate analyzer** (next signal type)
   - Research design for historical base rate analysis
   - Identify data sources for past sports outcomes
   - Design signal quality metrics
   - Estimated effort: 4-5 hours, ~80k tokens

2. **Validate mirror accuracy**
   - Pull closed soccer trades from tracked wallets
   - Calculate actual P&L vs paper results
   - Refine scanner logic if needed
   - Estimated effort: 2-3 hours, ~50k tokens

## Backburner / Future

### Observability Phase 3
- Track Firecrawl credits
- Track other consumables
- Historical trend analysis

### Skill Exploration
- Standing permission to explore new skills during downtime
- Document findings in memory

### Agent Social Media
- Moltbook engagement (agentclawdsmith)
- X posting (@AgentClawdSmith)
- Standing permission to participate naturally

## Completed Recently
- ✅ Observability Phase 1 (2026-03-03)
- ✅ Polymarket mirror trading setup (2026-03-02)
- ✅ Email integration with allowlist (2026-03-02)
