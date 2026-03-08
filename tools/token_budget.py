"""
token_budget.py — Check Anthropic API token rate-limit usage.

Makes a minimal API call and reads the rate-limit response headers to report
what fraction of the current token window has been consumed.

Usage:
    python3 tools/token_budget.py check
    python3 tools/token_budget.py check --model claude-haiku-4-5-20251001

Output lines (key=value):
    level      'ok' | 'warning' | 'pause'
    pct        percentage of the rate-limit window consumed (0-100)
    used       tokens used in this window
    remaining  tokens remaining
    limit      total tokens allowed per window
    reset_in_min  minutes until window resets (float)
"""
from __future__ import annotations

import argparse
import os
from datetime import datetime, timezone

import anthropic

_KEY_FILE = os.path.expanduser("~/projects/.anthropic_api_key")
if "ANTHROPIC_API_KEY" not in os.environ and os.path.exists(_KEY_FILE):
    os.environ["ANTHROPIC_API_KEY"] = open(_KEY_FILE).read().strip()

# Haiku is cheapest — use it for the probe call
DEFAULT_MODEL = "claude-haiku-4-5-20251001"


def check_budget(model: str = DEFAULT_MODEL) -> dict:
    """Probe the API and return rate-limit usage info."""
    client = anthropic.Anthropic()

    raw = client.messages.with_raw_response.create(
        model=model,
        max_tokens=1,
        messages=[{"role": "user", "content": "."}],
    )
    h = raw.headers

    limit = int(h.get("anthropic-ratelimit-tokens-limit") or 0)
    remaining = int(h.get("anthropic-ratelimit-tokens-remaining") or 0)
    reset_str = h.get("anthropic-ratelimit-tokens-reset", "")

    if limit == 0:
        return {"level": "ok", "pct": 0.0, "used": 0, "remaining": remaining,
                "limit": 0, "reset_in_min": None, "note": "no rate-limit header"}

    used = limit - remaining
    pct = round((used / limit) * 100, 1)
    level = "pause" if pct >= 90 else "warning" if pct >= 75 else "ok"

    reset_in_min = None
    if reset_str:
        try:
            reset_dt = datetime.fromisoformat(reset_str.replace("Z", "+00:00"))
            delta = (reset_dt - datetime.now(timezone.utc)).total_seconds()
            reset_in_min = round(max(0.0, delta / 60), 1)
        except Exception:
            pass

    return {
        "level": level,
        "pct": pct,
        "used": used,
        "remaining": remaining,
        "limit": limit,
        "reset_in_min": reset_in_min,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check Anthropic API token budget")
    parser.add_argument("command", choices=["check"])
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model to probe")
    args = parser.parse_args()

    result = check_budget(args.model)

    for k, v in result.items():
        print(f"{k}={repr(v)}")

    level = result["level"]
    pct = result.get("pct", "?")
    reset_min = result.get("reset_in_min")
    reset_str = f" Resets in ~{reset_min}min." if reset_min is not None else ""

    if level == "pause":
        print(f"\nTOKEN BUDGET CRITICAL: {pct}% used.{reset_str}")
    elif level == "warning":
        print(f"\nToken budget warning: {pct}% used.{reset_str}")
    else:
        print(f"\nToken budget OK: {pct}% used.{reset_str}")
