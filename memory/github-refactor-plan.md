# GitHub Refactor Plan (2026-03-04)

## Decision
Move from monorepo workspace to dedicated repos per project.
All projects go into a shared org (Adam + Agent Clawd Smith).

## Shared Org Setup
- **Name:** TBD (waiting for Adam's input)
- **Repos to create:**
  1. `BingoBango` (private) - new project, details TBD
  2. `AgentOps` (private) - agent operations/coordination tooling
  3. `polymarket-paper-trader` (private) - refactored from workspace/polymarket/
  4. `llm-observability` (private) - refactored from workspace/observability/
  5. `imessage-agent-router` (private) - refactored from workspace/imessage-processor.js

## Migration Steps

### 1. Polymarket Paper Trader
- [ ] Create repo in shared org
- [ ] Move `~/.openclaw/workspace/polymarket/*` to new repo
- [ ] Update README with setup instructions
- [ ] Update workspace to clone/symlink to new repo location
- [ ] Update HEARTBEAT.md scanner path

### 2. LLM Observability
- [ ] Create repo in shared org
- [ ] Move `~/.openclaw/workspace/observability/*` to new repo
- [ ] Update README
- [ ] Update HEARTBEAT.md budget-monitor path

### 3. iMessage Agent Router
- [ ] Create repo in shared org
- [ ] Move imessage-processor.js + related scripts
- [ ] Document LaunchAgent setup
- [ ] Update running process to point to new location

### 4. BingoBango (new)
- [ ] Create repo in shared org
- [ ] Initialize with README
- [ ] Wait for Adam to define what it is

### 5. AgentOps (new)
- [ ] Create repo in shared org
- [ ] Initialize with README
- [ ] Define scope (agent coordination, PM agent, etc.?)

## Workspace Post-Refactor
What stays in workspace:
- MEMORY.md, SOUL.md, AGENTS.md, USER.md, IDENTITY.md, TOOLS.md, HEARTBEAT.md
- memory/ (daily notes, state files)
- family-contacts.json, agent-inbox.md
- Configuration/coordination files

What moves out:
- All project code (polymarket, observability, imessage)
- Standalone tools

## Blockers
- [x] Need shared org created (Adam must do via web UI)
- [ ] Need org name decision
- [ ] Need to know what BingoBango is
