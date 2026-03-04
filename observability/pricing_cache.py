#!/usr/bin/env python3
"""
pricing-cache.py — Fetch and cache live model pricing from OpenRouter API.

Queries OpenRouter's /api/v1/models endpoint, parses pricing data, and caches
it locally with 24h TTL. Falls back to hardcoded pricing if API unavailable.

Usage:
    from pricing_cache import get_pricing
    pricing = get_pricing()  # Returns dict: model_id -> {input, output}
"""

import json
import time
from pathlib import Path
from datetime import datetime, timezone
import requests

CACHE_FILE = Path.home() / '.openclaw/workspace/memory/pricing-cache.json'
CACHE_TTL = 86400  # 24 hours in seconds
OPENROUTER_API = 'https://openrouter.ai/api/v1/models'
SECRETS_FILE = Path.home() / '.openclaw/secrets.json'

# Fallback hardcoded pricing (per million tokens, in USD)
FALLBACK_PRICING = {
    'openrouter/anthropic/claude-sonnet-4.5': {'input': 3.0, 'output': 15.0},
    'openrouter/anthropic/claude-haiku-4.5': {'input': 0.8, 'output': 4.0},
    'openrouter/deepseek/deepseek-chat': {'input': 0.14, 'output': 0.28},
}

def load_api_key():
    """Load OpenRouter API key from secrets.json."""
    if not SECRETS_FILE.exists():
        return None
    try:
        with open(SECRETS_FILE) as f:
            secrets = json.load(f)
            return secrets.get('openrouter', {}).get('apiKey')
    except Exception:
        return None

def load_cache():
    """Load pricing cache from disk."""
    if not CACHE_FILE.exists():
        return None
    try:
        with open(CACHE_FILE) as f:
            cache = json.load(f)
            # Check if cache is still valid (TTL)
            cached_at = cache.get('cached_at', 0)
            if time.time() - cached_at < CACHE_TTL:
                return cache.get('pricing', {})
            else:
                return None  # Cache expired
    except Exception:
        return None

def save_cache(pricing):
    """Save pricing data to cache."""
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    cache = {
        'cached_at': time.time(),
        'cached_at_human': datetime.now(timezone.utc).isoformat(),
        'pricing': pricing
    }
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)

def fetch_live_pricing():
    """Fetch pricing from OpenRouter API."""
    api_key = load_api_key()
    if not api_key:
        print("⚠️  No OpenRouter API key found in secrets.json")
        return None
    
    try:
        headers = {
            'Authorization': f'Bearer {api_key}',
            'HTTP-Referer': 'https://github.com/openclaw/openclaw',
            'X-Title': 'OpenClaw Observability'
        }
        
        response = requests.get(OPENROUTER_API, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        models = data.get('data', [])
        
        # Build pricing dict
        pricing = {}
        for model in models:
            model_id = model.get('id')
            pricing_info = model.get('pricing', {})
            
            # OpenRouter returns prices as strings (per-token cost)
            # We need per-million-token cost
            input_cost = float(pricing_info.get('prompt', 0)) * 1_000_000
            output_cost = float(pricing_info.get('completion', 0)) * 1_000_000
            
            if model_id and (input_cost > 0 or output_cost > 0):
                pricing[model_id] = {
                    'input': round(input_cost, 4),
                    'output': round(output_cost, 4)
                }
        
        print(f"✅ Fetched pricing for {len(pricing)} models from OpenRouter")
        return pricing
    
    except requests.RequestException as e:
        print(f"⚠️  OpenRouter API error: {e}")
        return None
    except Exception as e:
        print(f"⚠️  Unexpected error fetching pricing: {e}")
        return None

def get_pricing():
    """
    Get model pricing (cached or live).
    Returns dict: model_id -> {input: float, output: float}
    """
    # Try cache first
    cached = load_cache()
    if cached:
        print(f"📦 Using cached pricing ({len(cached)} models)")
        return cached
    
    # Cache miss or expired - fetch live
    print("🔄 Cache miss/expired - fetching live pricing from OpenRouter...")
    live = fetch_live_pricing()
    
    if live:
        save_cache(live)
        return live
    else:
        # API failed - fall back to hardcoded pricing
        print("⚠️  Falling back to hardcoded pricing")
        return FALLBACK_PRICING

if __name__ == '__main__':
    # CLI test
    pricing = get_pricing()
    print(f"\n📊 Pricing data available for {len(pricing)} models")
    print("\nSample (models we use):")
    for model in ['openrouter/anthropic/claude-sonnet-4.5', 
                  'openrouter/anthropic/claude-haiku-4.5',
                  'openrouter/deepseek/deepseek-chat']:
        if model in pricing:
            p = pricing[model]
            print(f"  {model}")
            print(f"    Input:  ${p['input']:.4f}/M tokens")
            print(f"    Output: ${p['output']:.4f}/M tokens")
