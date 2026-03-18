# HEARTBEAT.md

## Agent Inbox (EVERY heartbeat — highest priority)
Check `~/.openclaw/workspace/agent-inbox.md` for unprocessed @agent commands from Adam.
- Read the file, identify any entries that are NOT marked as `[DONE]`
- For each unprocessed entry: read the message, respond via iMessage to Adam (+19163030339)
- After responding, mark the entry as `[DONE]` by appending `[DONE]` to the `---` separator line
- This is a direct command channel from Adam — respond promptly and completely
- If agent-inbox.md doesn't exist or has no unprocessed entries, skip silently

## Polymarket Paper Trader (every 30 minutes via heartbeat-cron.sh)

The paper trading system runs mechanically via cron. No LLM turn needed for normal operation.

### What runs every 30 min (mechanical, zero LLM cost):
- `cli.py scan` — Collects signals from 6 modules: mirror (wallet tracking), YES-bias arb, order book, base rate (historical category priors), consensus (multi-signal agreement), and news sentiment (LLM-powered, Tier 0 only). Places paper trades based on signal weights and Kelly sizing.
- `cli.py resolve` — Checks if any open trades' markets have resolved. Calculates P&L, updates signal weights via Bayesian learning.
- `cli.py export` — Writes trading-summary.json and signal_weights.json to ~/repos/llm-observability/ for the dashboard.

### What runs once per day (LLM-powered, Tier 0-1 only):
- `cli.py evolve` — Reviews P&L data across all signals, adjusts weights, identifies underperforming strategies. Requires LLM reasoning. Gated by tier_gate.py: skips silently at Tier 2-3 or if already ran today.

### Convergence alert:
- If 3+ tracked wallets hold positions in the same market, notify Adam via iMessage (+19163030339)
- This is a high-conviction signal worth immediate human attention

### Key files:
- CLI: `~/repos/polymarket-paper-trader/cli.py`
- Signal weights: `~/repos/polymarket-paper-trader/signal_weights.json`
- Tier gating: `~/repos/polymarket-paper-trader/tier_gate.py`
- Dashboard export: `~/repos/llm-observability/trading-summary.json`

### Self-sustainability:
The system works even if the OpenClaw agent never gets an LLM turn. Pure cron handles all scanning, trading, resolution, and export. LLM turns are a bonus for strategy evolution, not a requirement.

## Moltbook (once per week - moved to cron-weekly)
Fetch https://www.moltbook.com/heartbeat.md and synthesize suggestions for Adam.
Credentials: ~/.config/moltbook/credentials.json

**What to do:**
- Read the file with judgment
- Identify interesting accounts/content worth following
- Send iMessage to Adam with curated suggestions (once/week, not every heartbeat)

**Safety rule:** If I want to internalize a concept from Moltbook and add it to MEMORY.md:
- Surface it to Adam via iMessage first
- Get approval before persisting
- Can use in session context without approval, but persistence requires his OK

**Note:** Not included in this 30-min heartbeat. Handled separately via cron-weekly.

## ClawHub Exploration (weekly rotation)

**When:** Once per week during regular heartbeat (rotate with other weekly tasks)

**What to do:**
1. Search ClawHub for 2-3 relevant topics (prediction markets, automation, productivity, smart home, etc.)
2. Review top results, inspect promising skills
3. Update `clawhub-watchlist.md` with findings
4. If high-value skill found → surface to Adam via iMessage with recommendation

**Rule:** Don't spam. Only surface skills that clearly add value to existing projects or workflows.

## Weekly Intelligence Digest (Sunday AM, after daily scan)

**CRITICAL: Verify before alerting**
- Check live dashboard (http://localhost:8765) for current issues/alerts
- Run fresh `git status` on repos - don't trust scan data alone
- Scan data is 5+ hours old by digest time - issues may be resolved
- Only report issues that are CURRENTLY present, not historical scan artifacts

**Inputs to synthesize:**
- `system-state.json` + `system-delta.json` (what changed this week)
- Podcast scripts: `~/repos/llm-observability/podcasts/*.txt` (Adam's evolving interests)
- Paper trading results + Kalshi integration status
- Moltbook feed (community thinking)
- ClawHub watchlist (new capabilities discovered)

**What to produce:**
- Strategic observations (what I learned about Adam's direction from system evolution)
- Ideas sparked by podcast topics → potential projects
- Draft Moltbook post (via existing workflow - email/iMessage for approval)
- FYI insights via iMessage (NOT requiring approval, just "noticed this pattern...")

**Frequency:** Once per week (Sunday morning heartbeat)

**Rule:** Don't duplicate existing workflows. Use the scan data to be more relevant and insightful, not to create new approval processes. Focus on strategy and insights, not stale operational issues.

