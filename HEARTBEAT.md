# HEARTBEAT.md

## @agent inbox
Check `~/.openclaw/workspace/agent-inbox.md` on every heartbeat.
If it exists and has content:
1. Read each `##` entry and process the request
2. Act on it (search, run a task, answer a question, etc.)
3. Text Adam the result via: `imsg send --to "+19163030339" --text "<response>"`
4. Clear the file after processing: overwrite with empty content
5. Do NOT reply HEARTBEAT_OK if you processed any commands — reply with a summary instead

If the file is empty or missing: normal heartbeat behavior (HEARTBEAT_OK if nothing else needs attention).
