# game-creation-agent

A Claude Code plugin providing tools to convert board game rulebooks into playable web implementations.

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
export ANTHROPIC_API_KEY=sk-...
```

## Tool reference

All tools live in `tools/`. Their names, signatures, and descriptions are the single source of truth in `mcp_server.py` — read `list_tools()` there to see what's available.

Import directly in Python one-liners:

```python
import sys; sys.path.insert(0, '/path/to/game-creation-agent')
from tools.pdf_tool import pdf_to_text
from tools.screenshot_tool import take_screenshot, simulate_drag
from tools.vision_tool import ask_about_screenshot
from tools.dev_tools import build_project, start_dev_server, kill_dev_server
```

## Slash commands (this plugin)

- `/game-creation-agent:visual-verify [project_dir]` — build → screenshot → compare to reference images → report
- `/game-creation-agent:test-drag [url] [source] [target]` — simulate drag-and-drop → before/after screenshots → report errors

## MCP server

`mcp_server.py` exposes all tools over stdio for Claude Desktop or other MCP clients. The plugin manifest (`.claude-plugin/plugin.json`) wires this up automatically when the plugin is installed.

To register manually with Claude Desktop, add to `~/.claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "game-creation": {
      "command": "python3",
      "args": ["/absolute/path/to/game-creation-agent/mcp_server.py"]
    }
  }
}
```

## Adding a new tool

1. Add a function to an existing file in `tools/` (or create a new one)
2. Register it in `mcp_server.py`: add a `Tool(...)` entry in `list_tools()` and a handler branch in `call_tool()`

## Self-improvement

While implementing games, you will encounter patterns, gotchas, and reusable techniques. Apply the following rule when deciding where improvements belong:

**Add to game-creation-agent** when the capability is game-agnostic — useful for any future game:
- A new tool in `tools/` + registered in `mcp_server.py` (e.g. a tool to diff two screenshots, or to validate HTML accessibility)
- A new or updated command in `commands/` (e.g. a new workflow step)
- A new pattern or gotcha in `skills/game-visual-testing/SKILL.md`
- An update to `generic-game-plan.md` if a phase needs refinement based on experience

**Add to the target game's repo** when the code is game-specific:
- React components, game logic, CSS, assets
- Anything that references piece types, board layout, or rules of a particular game

**Never add game-specific code to game-creation-agent.** All code here must work regardless of which game is being built.

When you identify a self-improvement opportunity, propose it explicitly: "I noticed X pattern across this implementation. Should I add Y to game-creation-agent?" Get user approval before modifying this repo's files mid-implementation.
