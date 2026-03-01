#!/usr/bin/env python3
"""
game_coder.py — Game-creation coding agent.

Extends local_coder (generic coding agent) with game-specific tools:
  - read_pdf    : extract text from rulebook PDFs
  - dev_server  : start/stop React dev server for live testing
  - screenshot  : take screenshot of running game for visual verification
  - ask_vision  : analyze screenshot with Claude vision

Usage (same as local_coder):
    python3 game_coder.py --project /path/to/game --task "Implement Phase 1"
    python3 game_coder.py --project /path/to/game   # interactive mode
"""
import os
import sys
import subprocess

# ── Import local_coder as the base ───────────────────────────────────────────
LOCAL_CODER_DIR = "/Users/brad/projects/code/local-coder"

# Build subprocess env: inherit everything, add ANTHROPIC_API_KEY if not already set.
# Claude Code stores the key internally; if the user has it in their shell, use it.
_SUBPROCESS_ENV = {**os.environ}
if "ANTHROPIC_API_KEY" not in _SUBPROCESS_ENV:
    # Try reading from ~/.anthropic/api_key (common location)
    _key_file = os.path.expanduser("~/.anthropic/api_key")
    if os.path.exists(_key_file):
        with open(_key_file) as _f:
            _SUBPROCESS_ENV["ANTHROPIC_API_KEY"] = _f.read().strip()
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__)) + "/tools"
sys.path.insert(0, LOCAL_CODER_DIR)

import local_coder  # noqa: E402  (must come after sys.path insert)


# ── Game-specific tool implementations ───────────────────────────────────────

def tool_dev_server(args: dict) -> str:
    """Start or stop a React dev server. action: 'start'|'stop', path, port."""
    import time
    action = args.get("action", "start")
    port = int(args.get("port", 3000))
    script_parts = [
        f"import sys, time; sys.path.insert(0, {repr(TOOLS_DIR)}); "
        f"from dev_tools import start_dev_server, kill_dev_server; "
        f"kill_dev_server({port}); "
    ]
    if action == "stop":
        script_parts.append(f"print('Dev server on port {port} stopped.')")
    else:
        path = args.get("path", ".")
        script_parts.append(
            f"r = start_dev_server({repr(path)}, {port}); "
            f"time.sleep(4); "
            f"print('Dev server started at http://localhost:{port} pid=' + str(r.get('pid','?')))"
        )
    result = subprocess.run(["/usr/bin/python3", "-c", "".join(script_parts)],
                            capture_output=True, text=True, timeout=30, env=_SUBPROCESS_ENV)
    if result.returncode != 0:
        return f"dev_server error: {result.stderr[:400]}"
    return result.stdout.strip()


def tool_screenshot(args: dict) -> str:
    """Take a screenshot of a running web app URL. Returns path to PNG."""
    url = args.get("url", "http://localhost:3000")
    output_path = args.get("output_path", "/tmp/screenshot.png")
    selector = args.get("selector")
    script = (
        f"import sys; sys.path.insert(0, {repr(TOOLS_DIR)}); "
        f"from screenshot_tool import take_screenshot; "
        f"p = take_screenshot({repr(url)}, selector={repr(selector)}, "
        f"output_path={repr(output_path)}); print(p)"
    )
    result = subprocess.run(["/usr/bin/python3", "-c", script],
                            capture_output=True, text=True, timeout=60, env=_SUBPROCESS_ENV)
    if result.returncode != 0:
        return f"screenshot error: {result.stderr[:400]}"
    return f"Screenshot saved to {result.stdout.strip()}"


def tool_ask_vision(args: dict) -> str:
    """Ask Claude vision to analyze a screenshot. Returns text answer."""
    image_path = args.get("image_path")
    question = args.get("question", "Describe what you see.")
    if not image_path:
        return "ERROR: image_path required"
    script = (
        f"import sys; sys.path.insert(0, {repr(TOOLS_DIR)}); "
        f"from vision_tool import ask_about_screenshot; "
        f"print(ask_about_screenshot({repr(image_path)}, {repr(question)}))"
    )
    result = subprocess.run(["/usr/bin/python3", "-c", script],
                            capture_output=True, text=True, timeout=120, env=_SUBPROCESS_ENV)
    if result.returncode != 0:
        return f"ask_vision error: {result.stderr[:400]}"
    return result.stdout.strip()


# ── Register game tools into local_coder's TOOLS dict ────────────────────────
GAME_TOOLS = {
    "dev_server": tool_dev_server,
    "screenshot": tool_screenshot,
    "ask_vision": tool_ask_vision,
}
local_coder.TOOLS.update(GAME_TOOLS)

# Extend the tool schema with game-specific entries (git and read_pdf already in local_coder)
local_coder.TOOL_SCHEMA = local_coder.TOOL_SCHEMA.replace(
    "- read_pdf(path, pages?)                    — extract text from a PDF rulebook",
    "- read_pdf(path, pages?)                    — extract text from a PDF rulebook\n"
    "- dev_server(action, path?, port?)          — start or stop a React dev server\n"
    "- screenshot(url?, output_path?, selector?) — screenshot a running web app; returns path\n"
    "- ask_vision(image_path, question)          — analyze screenshot with Ollama vision model",
)

# Add game-specific rules
local_coder.TOOL_SCHEMA = local_coder.TOOL_SCHEMA.replace(
    "14. Tackle one concrete deliverable at a time.",
    "14. Tackle one concrete deliverable at a time.\n"
    "15. Every React component prop in the function signature MUST be used in JSX. After writing, re-read to confirm.\n"
    "16. When building a game: create the game state module FIRST (pure JS, no React), get build passing, then update components to consume it.\n"
    "17. After npm_build passes with React changes, start dev_server → screenshot → ask_vision to confirm the UI renders correctly. Stop dev_server after.\n"
    "18. Read game rulebook PDFs with read_pdf before implementing rules.",
)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    local_coder.main()
