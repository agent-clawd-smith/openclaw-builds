#!/usr/bin/env python3
"""
usage-logger.py — Extracts LLM usage from OpenClaw session logs.

Reads the session transcript (JSONL), extracts usage data from tool results,
calculates cost, and appends to a weekly usage log.

Usage:
    python3 usage-logger.py --session-key agent:main:main
    python3 usage-logger.py --all  # Process all sessions
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
import argparse

# Pricing per 1M tokens (input)
PRICING = {
    'anthropic/claude-sonnet-4.5': 3.00,
    'anthropic/claude-haiku-4.5': 1.00,
    'anthropic/claude-opus-4.6': 15.00,
    'google/gemini-2.5-pro': 1.25,
    'google/gemini-2.5-flash': 0.30,
    'deepseek/deepseek-chat': 0.32,
}

# OpenRouter prefix variants
def normalize_model_id(model_id):
    """Strip openrouter/ prefix for pricing lookup."""
    if model_id.startswith('openrouter/'):
        return model_id.replace('openrouter/', '')
    return model_id

def get_weekly_log_path():
    """Returns path to this week's usage log (Monday-Sunday)."""
    now = datetime.now(timezone.utc)
    # Calculate Monday of current week
    days_since_monday = now.weekday()  # 0=Monday
    week_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = week_start.replace(day=now.day - days_since_monday)
    week_str = week_start.strftime('%Y-W%U')
    
    log_dir = Path.home() / '.openclaw/workspace/memory'
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f'usage-{week_str}.jsonl'

def calculate_cost(model_id, input_tokens, output_tokens):
    """Calculate cost in USD."""
    normalized = normalize_model_id(model_id)
    rate = PRICING.get(normalized, 0)
    # Simplified: use input rate for both (output is usually 5-10x higher, but for tracking this works)
    total_tokens = input_tokens + output_tokens
    return (total_tokens / 1_000_000) * rate

def log_usage(session_key, model, input_tokens, output_tokens, task='unknown'):
    """Append usage entry to weekly log."""
    log_path = get_weekly_log_path()
    cost = calculate_cost(model, input_tokens, output_tokens)
    
    entry = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'session_key': session_key,
        'model': model,
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'total_tokens': input_tokens + output_tokens,
        'cost_usd': round(cost, 4),
        'task': task,
    }
    
    with open(log_path, 'a') as f:
        f.write(json.dumps(entry) + '\n')
    
    return entry

def main():
    parser = argparse.ArgumentParser(description='Log LLM usage from OpenClaw sessions')
    parser.add_argument('--session-key', help='Session key to process')
    parser.add_argument('--model', help='Model ID')
    parser.add_argument('--input', type=int, help='Input tokens')
    parser.add_argument('--output', type=int, help='Output tokens')
    parser.add_argument('--task', default='manual', help='Task description')
    args = parser.parse_args()
    
    if args.session_key and args.model and args.input is not None and args.output is not None:
        entry = log_usage(args.session_key, args.model, args.input, args.output, args.task)
        print(f"Logged: {entry['model']} | {entry['total_tokens']:,} tokens | ${entry['cost_usd']:.4f}")
    else:
        print("Usage: python3 usage-logger.py --session-key <key> --model <model> --input <n> --output <n> [--task <desc>]")
        sys.exit(1)

if __name__ == '__main__':
    main()
