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
from tools.npm_build import npm_build          # preferred for React/npm projects
from tools.dev_tools import start_dev_server, kill_dev_server
```

## Build workflow

**Always use `npm_build` from `tools/npm_build.py` to build React/npm projects — never run `npm run build` via Bash directly.** The Python tool runs without a permission prompt, which keeps the workflow uninterrupted.

```python
# Correct
result = npm_build('/path/to/project')
print(result['stderr'])  # warnings/errors from react-scripts

# Wrong — triggers permission prompt
subprocess.run(['npm', 'run', 'build'], ...)
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

## Self-verification: CSS layout for hex/grid game boards

When implementing a board game UI with a non-rectangular board (hex, diamond, etc.), verify these things after every layout change:

### 1. All cells are the same size
Take a screenshot and visually compare center cells vs. edge cells. If center cells are smaller, the root cause is usually `flex: 1 0 0` making cells fill `1/N` of their row — so rows with fewer cells have larger cells.

**Fix:** Give all cells a fixed fraction of the board container's width:
```css
flex: none;
width: calc(100% / MAX_COLS);  /* e.g. calc(100% / 7) for a hex board */
aspect-ratio: 1 / 1;
```
`100%` here resolves to the **flex container's content-box width**. Keep `box-sizing: content-box` (the default) on rows — if you add `box-sizing: border-box`, `100%` shrinks when rows have padding, making cells different sizes per row.

### 2. The board has the correct geometric shape (not a rectangle)
A hexagonal board should taper at top and bottom. If all rows end at the same right edge, the offset/indentation is being cancelled out.

**Fix:** Use spacer `<div>` elements at the start of shorter rows instead of `paddingLeft`. With content-box sizing, the spacer's `width: calc(...)` also resolves to board width, so offsets are correct:
```jsx
// type 0 row (4 of 7 cells): indent 1.5 cells
<div style={{ flex: 'none', width: 'calc(3 * 100% / 14)' }} />
```

### 3. Wrapper elements have defined width
If the board is inside a flex container alongside another element (e.g. a sidebar or action area), the board must have `flex: 1; min-width: 0` or an explicit width — otherwise its `width: 100%` rows have no concrete reference and collapse or wrap incorrectly.

### 4. Verify with a screenshot, not just code inspection
Layout bugs like unequal cell sizes or straight edges only show up visually. After any layout change:
1. Build → start dev server → take screenshot with `tools/screenshot_tool.py`
2. Read the screenshot file with the Read tool to view it
3. Check: cell sizes uniform? board outline matches expected polygon? no unexpected wrapping?
4. Iterate until correct before moving on.

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
