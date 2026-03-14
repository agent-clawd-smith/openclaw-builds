# Priority Queue & Work Assignments

**Current week:** 2026-03-02 to 2026-03-08  
**Budget:** $100 weekly ($0.31 spent so far)  
**Updated:** 2026-03-04 11:05 PST

## Assigned Work

### ACTIVE: Live Pricing Fetch (Observability Phase 2.1)
**Assigned to:** Main agent  
**Assigned at:** 2026-03-04 11:05 PST  
**Token budget:** 50,000 tokens (~$0.15-0.20)  
**Time estimate:** 2-3 hours

**Scope:**
1. Modify `budget-monitor.py` to fetch live pricing from OpenRouter API
2. Query `/api/v1/models` endpoint
3. Parse JSON response and build PRICING dict dynamically
4. Cache pricing data (24h TTL), fallback to hardcoded on API failure
5. Handle edge cases: missing models, API errors, rate limits
6. Test with current usage data
7. Document changes in observability/README.md

**Success criteria:**
- Script runs without errors
- Pricing dict built from live API data
- Cached pricing refreshes daily
- Graceful fallback if API unavailable
- Test passes with real usage-log.jsonl

**When to stop:**
- Feature complete and tested, OR
- Token budget reached (50k tokens), OR
- 3 hours elapsed (whichever comes first)
- **Report back via @agent** with status and what's left (if incomplete)

**Delivery:**
- Commit changes to git with clear message
- Update observability/TODO.md to mark task complete
- Report completion via @agent message to Adam

---

## Queue (Next Up)

### Priority 1: Auto-logging Integration (Observability Phase 2.2)
**Estimate:** 75k tokens, 3-4 hours  
**Blockers:** None (can start after pricing fetch)

### Priority 2: Web Dashboard UI (Observability Phase 2.3)
**Estimate:** 100k tokens, 4-6 hours  
**Blockers:** Auto-logging should be done first (provides real data)

### Priority 3: Sports Base Rate Analyzer (Polymarket)
**Estimate:** 80k tokens, 4-5 hours  
**Blockers:** None (can run in parallel)

---

## Weekly Pacing Plan

**Target this week:** Complete Observability Phase 2 (~225k tokens total, ~$0.70)

- **Wed PM:** Live pricing fetch (50k tokens)
- **Thu:** Auto-logging integration (75k tokens)
- **Fri/Weekend:** Web dashboard UI (100k tokens)

**Budget cushion:** ~$99.00 remaining for the week — comfortable margin for exploration, heartbeats, and iMessage handling.

---

## Tracking

### Budget Burn
- Week start (Mar 2): $0.00
- Current (Mar 4 11:05 AM): $0.31
- Remaining: $99.69

### Completed This Week
- (none yet — PM just created)
