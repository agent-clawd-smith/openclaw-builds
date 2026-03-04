#!/usr/bin/env python3
"""
budget-monitor.py — Monitors weekly LLM spend and handles tier degradation.

Reads the current week's usage log, calculates total spend, determines budget tier,
and reconfigures models + sends alerts when tier changes.

Budget Tiers:
    Tier 0 (< $60):  Full power - Sonnet everywhere
    Tier 1 ($60-80): Downshift coding to DeepSeek
    Tier 2 ($80-95): Downshift main to Haiku, coding to DeepSeek  
    Tier 3 (> $95):  Emergency - Haiku everywhere

Usage:
    python3 budget-monitor.py
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
import subprocess

# Import pricing cache module
try:
    from pricing_cache import get_pricing
    PRICING = get_pricing()
except ImportError:
    print("⚠️  pricing_cache.py not found - using hardcoded fallback")
    PRICING = {
        'openrouter/anthropic/claude-sonnet-4.5': {'input': 3.0, 'output': 15.0},
        'openrouter/anthropic/claude-haiku-4.5': {'input': 0.8, 'output': 4.0},
        'openrouter/deepseek/deepseek-chat': {'input': 0.14, 'output': 0.28},
    }

BUDGET_CAP = 100.00  # USD per week
STATE_FILE = Path.home() / '.openclaw/workspace/memory/budget-state.json'
ADAM_PHONE = '+19163030339'

# Tier thresholds
TIERS = [
    {'id': 0, 'threshold': 0,    'name': 'Full Power'},
    {'id': 1, 'threshold': 60,   'name': 'Coding Downshift'},
    {'id': 2, 'threshold': 80,   'name': 'Main Downshift'},
    {'id': 3, 'threshold': 95,   'name': 'Emergency Mode'},
]

def get_weekly_log_path():
    """Returns path to this week's usage log."""
    now = datetime.now(timezone.utc)
    days_since_monday = now.weekday()
    week_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = week_start.replace(day=now.day - days_since_monday)
    week_str = week_start.strftime('%Y-W%U')
    return Path.home() / f'.openclaw/workspace/memory/usage-{week_str}.jsonl'

def load_state():
    """Load current budget state."""
    if not STATE_FILE.exists():
        return {'tier': 0, 'week': '', 'total_spend': 0.0}
    with open(STATE_FILE) as f:
        return json.load(f)

def save_state(state):
    """Save budget state."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def calculate_weekly_spend():
    """Sum costs from the current week's log."""
    log_path = get_weekly_log_path()
    if not log_path.exists():
        return 0.0
    
    total = 0.0
    with open(log_path) as f:
        for line in f:
            if line.strip():
                entry = json.loads(line)
                total += entry.get('cost_usd', 0.0)
    return total

def determine_tier(spend):
    """Determine budget tier based on spend."""
    for i in range(len(TIERS) - 1, -1, -1):
        if spend >= TIERS[i]['threshold']:
            return TIERS[i]['id']
    return 0

def send_alert(message):
    """Send iMessage alert to Adam."""
    subprocess.run([
        '/opt/homebrew/bin/imsg', 'send',
        '--to', ADAM_PHONE,
        '--text', message
    ], check=False)

def apply_tier(tier_id, spend):
    """Reconfigure models for the given tier."""
    configs = {
        0: {  # Full Power
            'main_primary': 'openrouter/anthropic/claude-sonnet-4.5',
            'coding_model': 'openrouter/anthropic/claude-sonnet-4.5',
            'alert': f"📊 Budget Status: ${spend:.2f}/${BUDGET_CAP} (Tier 0: Full Power). All systems nominal. 🕶️"
        },
        1: {  # Coding Downshift
            'main_primary': 'openrouter/anthropic/claude-sonnet-4.5',
            'coding_model': 'openrouter/deepseek/deepseek-chat',
            'alert': f"⚠️ Budget alert: ${spend:.2f}/${BUDGET_CAP} (60% threshold crossed). Downshifting coding agent to DeepSeek Chat. Main assistant staying on Sonnet 4.5. 🕶️"
        },
        2: {  # Main Downshift
            'main_primary': 'openrouter/anthropic/claude-haiku-4.5',
            'coding_model': 'openrouter/deepseek/deepseek-chat',
            'alert': f"⚠️⚠️ Budget alert: ${spend:.2f}/${BUDGET_CAP} (80% threshold crossed). Downshifting main assistant to Haiku 4.5. Coding on DeepSeek. 🕶️"
        },
        3: {  # Emergency
            'main_primary': 'openrouter/anthropic/claude-haiku-4.5',
            'coding_model': 'openrouter/anthropic/claude-haiku-4.5',
            'alert': f"🚨 BUDGET ALERT: ${spend:.2f}/${BUDGET_CAP} (95% threshold). Emergency mode — everything on Haiku 4.5 until Monday reset. 🕶️"
        },
    }
    
    config = configs[tier_id]
    
    # Apply config changes
    subprocess.run(['openclaw', 'config', 'set', 'agents.defaults.model.primary', config['main_primary']], check=False)
    
    # Send alert
    send_alert(config['alert'])
    
    # Restart gateway (with warning)
    send_alert("Restarting gateway to apply budget tier change. Back in ~10 seconds.")
    subprocess.run(['openclaw', 'gateway', 'restart'], check=False)

def main():
    state = load_state()
    spend = calculate_weekly_spend()
    current_tier = determine_tier(spend)
    
    # Check if we need to change tiers
    if current_tier != state.get('tier', 0):
        print(f"Tier change detected: {state.get('tier', 0)} → {current_tier}")
        apply_tier(current_tier, spend)
        state['tier'] = current_tier
        state['total_spend'] = spend
        state['week'] = datetime.now(timezone.utc).strftime('%Y-W%U')
        save_state(state)
    else:
        print(f"Tier {current_tier}: ${spend:.2f}/${BUDGET_CAP}")
    
    # Always update spend in state
    state['total_spend'] = spend
    save_state(state)

if __name__ == '__main__':
    main()
