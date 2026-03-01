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
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__)) + "/tools"
sys.path.insert(0, LOCAL_CODER_DIR)

import local_coder  # noqa: E402  (must come after sys.path insert)


# ── Game-specific tool implementations ───────────────────────────────────────

def tool_read_pdf(args: dict) -> str:
    """Extract text from a PDF rulebook. pages: '1-5' or '3' (optional)."""
    path = args.get("path")
    pages = args.get("pages")
    if not path:
        return "ERROR: path required"
    script = (
        f"import sys; sys.path.insert(0, {repr(TOOLS_DIR)}); "
        f"from pdf_tool import pdf_to_text; "
        f"print(pdf_to_text({repr(path)}, pages={repr(pages)})[:8000])"
    )
    result = subprocess.run(["/usr/bin/python3", "-c", script],
                            capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        return f"read_pdf error: {result.stderr[:400]}"
    return result.stdout.strip()


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
                            capture_output=True, text=True, timeout=30)
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
                            capture_output=True, text=True, timeout=60)
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
                            capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        return f"ask_vision error: {result.stderr[:400]}"
    return result.stdout.strip()


# ── Register game tools into local_coder's TOOLS dict ────────────────────────
GAME_TOOLS = {
    "read_pdf":   tool_read_pdf,
    "dev_server": tool_dev_server,
    "screenshot": tool_screenshot,
    "ask_vision": tool_ask_vision,
}
local_coder.TOOLS.update(GAME_TOOLS)

# Extend the tool schema with game-specific entries
local_coder.TOOL_SCHEMA = local_coder.TOOL_SCHEMA.replace(
    "- git(subcommand, cwd?, args?)              — run git status/diff/log/add/commit",
    "- git(subcommand, cwd?, args?)              — run git status/diff/log/add/commit\n"
    "- read_pdf(path, pages?)                    — extract text from a PDF rulebook\n"
    "- dev_server(action, path?, port?)          — start or stop a React dev server\n"
    "- screenshot(url?, output_path?, selector?) — screenshot a running web app; returns path\n"
    "- ask_vision(image_path, question)          — analyze screenshot with Claude vision",
)

# Add game-specific rules
local_coder.TOOL_SCHEMA = local_coder.TOOL_SCHEMA.replace(
    "10. Use remember() to save important discoveries",
    "10. Use remember() to save important discoveries\n"
    "11. To verify React UI changes: dev_server(start) → screenshot(url) → ask_vision(image, question). Stop dev_server when done.\n"
    "12. Read game rulebook PDFs with read_pdf before implementing rules.",
)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    local_coder.main()
