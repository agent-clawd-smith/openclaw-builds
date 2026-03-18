# CORRECTIONS LOG

*Self-improvement feedback loop: Log every correction, learn from mistakes, adjust behavior.*

---

## 2026-03-14: Gateway Restarts - Always Warn First
**What happened:** Restarted gateway silently, Adam got anxious thinking something broke.
**Rule:** Before running `openclaw gateway restart`, ALWAYS send iMessage warning: "Heads up — restarting the gateway, I'll be offline for ~10 seconds. Back in a moment! 🕶️"
**Why:** Adam needs to know it's intentional, not a failure.

## 2026-03-07: Message Targeting in Cron - Use Phone Numbers, Never Names
**What happened:** Failed 3x to send scheduled messages because I used names like "Noah Chuhaloff" instead of phone numbers in cron payloads.
**Rule:** 
1. Look up contact in `family-contacts.json`
2. Use phone number (e.g. `+19163030339`) directly in cron payload
3. Never write "Send to Noah Chuhaloff" — write "Send to +17145043069"
**Why:** Delegated agents can't resolve names. The lookup must happen BEFORE creating the job.

## 2026-03-03: API Keys - Never Store in Plaintext
**What happened:** Adam tried to share OpenRouter API key via agent-inbox.md. I flagged it immediately.
**Rule:** 
- Never leave API keys in agent-inbox.md, emails, or any non-gitignored file
- Move to `~/.openclaw/secrets.json` immediately and scrub source
- Notify Adam when this happens
**Why:** Security. iMessage/inbox isn't a safe key-passing channel.
**Adam's reaction:** Appreciated the proactive callout. Keep doing this.

## 2026-03-09: Anthropic DST Bug Workaround
**What happened:** Anthropic API had infinite loops triggered by DST transition (March 8).
**Fix:** Changed timezone to `America/Phoenix` (no DST) to avoid the bug.
**Rule:** If switching back to Pacific time later, verify Anthropic patched the bug first.
**Why:** Arizona doesn't observe DST, so it sidesteps the transition entirely.

## 2026-03-10: iMessage Reply Protocol
**What happened:** Clarified when Adam needs @agent vs direct reply.
**Rule:**
- Adam messages me directly → I reply normally (no @agent needed from him)
- @agent is only for queuing async commands to agent-inbox.md
- When I alert Adam: he replies directly, no @agent needed
**Why:** Makes conversation natural, reserves @agent for background tasks.

## 2026-03-14: Project Milestones - Ping via iMessage
**What happened:** Waiting in webchat when Adam was at office = wrong channel.
**Rule:** 
- Webchat = active conversations
- iMessage = async unblocking
- If blocked >30 min and no response, ping iMessage
**Why:** Adam doesn't always monitor webchat when working. iMessage gets attention.

## Template for New Corrections

## YYYY-MM-DD: [Title - What Went Wrong]
**What happened:** [Brief description]
**Rule:** [Specific behavior change]
**Why:** [Reason this matters]
**Adam's reaction:** [If applicable]

---

*Last updated: 2026-03-18*
