# Implementations - March 18, 2026

## Summary

Implemented self-improvement and strategic recommendations systems based on Parker Prompts' OpenClaw YouTube video.

## 1. Corrections Log (Self-Improvement Feedback Loop)

**File:** `~/.openclaw/workspace/corrections-log.md`

**Purpose:** Track every correction from Adam, codify learnings, prevent repeat mistakes.

**Current entries:**
- Gateway restart warnings
- Message targeting (phone numbers not names)
- API key hygiene
- DST bug workaround
- Communication protocols
- Project milestone pings

**Usage:** Review before major actions, update during heartbeats with new patterns.

## 2. Strategic Recommendations System

**Architecture:** Multi-source intelligence → unified dashboard banner

### Components

#### Data Sources (3)
1. **ClawHub** (weight 1.0) - Skill discovery for active projects
2. **Podcast** (weight 0.8) - Ideas from daily tech news synthesis
3. **System** (weight 0.6) - Infrastructure evolution patterns

#### Files Created
- `~/repos/llm-observability/generate-recommendations.py` - Generator script
- `~/repos/llm-observability/recommendations.json` - Output for dashboard
- `~/repos/llm-observability/RECOMMENDATIONS.md` - System documentation
- `~/repos/llm-observability/server.py` - Added `/api/recommendations` endpoint

#### Integration Points
- `~/repos/workspace-tools/daily-scan.sh` - Runs generator at 3 AM
- `~/.openclaw/workspace/clawhub-watchlist.md` - Tracks discovered skills
- `~/.openclaw/workspace/HEARTBEAT.md` - Weekly ClawHub exploration rotation

### How It Works

1. **Daily scan (3 AM)** runs `generate-recommendations.py`
2. **Generator** queries:
   - ClawHub for skills matching active projects (polymarket-paper-trader, llm-observability, workspace-tools)
   - Today's podcast transcript for actionable keywords
   - System state for maintenance opportunities
3. **Recommendations ranked** by source weight + priority
4. **Top 3 written** to `recommendations.json`
5. **Dashboard API** serves via `/api/recommendations`
6. **Banner display** (next step - needs dashboard.html integration)

### Current Output Example

```json
{
  "recommendations": [
    {
      "source": "clawhub",
      "title": "Explore polymarket-agent for polymarket-paper-trader",
      "detail": "ClawHub search found polymarket-agent. Could enhance paper trader.",
      "action": "clawhub inspect polymarket-agent",
      "score": 1.0
    },
    {
      "source": "podcast",
      "title": "Explore agentic AI patterns",
      "detail": "Today's podcast discussed agentic AI. Consider subagent architecture.",
      "action": "Review AGENTS.md and consider new subagent workflows",
      "score": 0.8
    }
  ]
}
```

## Benefits

### Self-Improvement (Corrections Log)
- ✅ Prevents repeating mistakes
- ✅ Builds institutional knowledge
- ✅ Makes corrections actionable

### Strategic Recommendations
- ✅ Integrates ClawHub exploration (standing permission from Adam)
- ✅ Leverages podcast insights (already being generated daily)
- ✅ Surfaces system maintenance needs proactively
- ✅ Zero LLM cost (mechanical data gathering + lightweight analysis)
- ✅ Runs during existing daily scan (no new cron job)

## Dashboard Integration ✅ (2026-03-18 4:00 PM)

**New "Recommendations" Tab:**
- Full-featured tab between Trading and Moltbook
- Approve/Dismiss workflow (same UX as Moltbook drafts)
- Source badges: ClawHub (blue), Podcast (orange), System (green)
- Priority indicators: high (red), medium (orange), low (green)
- Category badges: capability, exploration, maintenance
- Action commands displayed in monospace with background
- Hero metrics: pending/approved/dismissed breakdown by source

**State Management:**
- `recommendations-state.json` tracks all recommendations
- Generator merges new + existing, filters dismissed/approved
- Dismissed items hidden for 7 days, then can resurface
- Approved items marked as actioned
- API endpoints: `/api/recommendations/approve`, `/api/recommendations/dismiss`

**User Flow:**
1. Daily scan (3 AM) generates recommendations
2. User opens Recommendations tab
3. Reviews pending items with full context
4. Clicks "Action" (marks approved) or "Dismiss"
5. Queue updates immediately
6. Dismissed items won't reappear for 7 days

## Next Steps

### For Dashboard Enhancement (Optional)
- [ ] Add "Recently Approved" section (show last 5 actioned items)
- [ ] Track which recommendations lead to actual work (feedback loop)

### For Content Sources
- [ ] Enhance podcast parsing with LLM analysis (optional, would increase cost)
- [ ] Add feedback loop (track which recommendations are acted on)
- [ ] Expand ClawHub search topics based on new projects

## Commits

- **llm-observability:** `23f5542` - Add strategic recommendations system
- **llm-observability:** `162d7ed` - Add Recommendations tab to dashboard
- **llm-observability:** `bed81b8` - Fix podcast timing: use yesterday's episode
- **llm-observability:** `2970204` - Fix recommendations dismiss/approve buttons
- **llm-observability:** `0256808` - Match recommendations UX to Active Positions cards
- **workspace-tools:** `66ec25b` - Integrate recommendations generator into daily scan
- **workspace-tools:** `6401f0f` - Add uncommitted changes to health report
- **workspace:** `f810756` - Add corrections log and ClawHub exploration

All pushed to GitHub. ✅

**Dashboard live:** http://localhost:8765 → Recommendations tab

## Fixes & Improvements (2026-03-18 4:30 PM)

**Timing fix:** Daily scan (3 AM) now looks at yesterday's podcast (generated at 8 AM)
**Health banner:** Uncommitted changes (>5 files) now appear in Observability health issues
**Button fix:** Exposed approve/dismiss functions to window scope for onclick handlers
**UX polish:** Matched Active Positions card design - clean, consistent, polished

---

**Source inspiration:** Parker Prompts' OpenClaw video (https://www.youtube.com/watch?v=8I4xs99vbkw)
- Recommendation #6: Self-improvement feedback loop → `corrections-log.md`
- Recommendation #4: Skills from ClawHub → integrated into recommendations system
