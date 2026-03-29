# game-creation-agent

A Claude Code plugin providing tools to convert board game rulebooks into playable web implementations.

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
# No API key needed — pipeline uses local Ollama for vision; guidelines are written by Claude Code directly
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

## YouTube pipeline workflow

The YouTube pipeline (`tools/youtube_pipeline.py`) gathers raw materials for game understanding.
**No Anthropic API key required** — Ollama handles local vision; Claude Code writes the guidelines.

### Step 1: Run the pipeline

```bash
# Process all videos for a game (pass multiple URLs at once)
# IMPORTANT: always single-quote URLs — zsh treats '?' as a glob wildcard
PYENV_VERSION=3.12.2 python3 tools/youtube_pipeline.py \
  'https://www.youtube.com/watch?v=VIDEO1' \
  'https://www.youtube.com/watch?v=VIDEO2' \
  'https://www.youtube.com/watch?v=VIDEO3' \
  --output /path/to/game/resources/youtube \
  --game "GameName"
```

Each video gets its own subdirectory: `<output>/<video_id>/`
- `transcript.md` — full timestamped transcript (from Whisper or youtube-transcript-api)
- `frames/` — JPEG frames at 30s intervals (if video downloaded)
- `frames.json` — frame timestamps + Ollama vision captions

Video URLs to process are in `resources/how-to-play.md`.

### Step 2: Generate guidelines (done by Claude Code, not the pipeline)

After the pipeline runs, read the transcripts and frames directly and write `guidelines.md`:
1. Read `<video_id>/transcript.md` for the full rules explanation
2. Use the Read tool on key frames in `frames/` to see the board/pieces visually
3. Synthesize a `guidelines.md` with sections: Setup, Turn Structure, Valid Moves, Win Condition, Key Rules, Testing Checklist
4. Write it to `<output>/<video_id>/guidelines.md` and a consolidated `<output>/guidelines.md`

### Step 3: Refine the game implementation

With guidelines in hand:
1. Read the existing game's `src/Game.js` and `src/App.js`
2. Compare against guidelines — find discrepancies (wrong costs, missing rules, incorrect win conditions)
3. Fix each discrepancy, build, screenshot to verify

### Fully local pipeline (no cloud APIs)

| Step | Tool | Notes |
|---|---|---|
| Download | yt-dlp (pyenv 3.12) | Android client strategy first |
| Frames | ffmpeg | Every 30s |
| Transcription | **mlx-whisper** (Apple Silicon) | `mlx-community/whisper-small-mlx`; auto-downloads weights on first run |
| Frame captions | Ollama `llava-phi3` | Local vision model |
| Guidelines | Claude Code directly | Read transcripts + frames, write guidelines.md |

### Troubleshooting

- **yt-dlp 403**: Android client is strategy #1 — already set. Update yt-dlp if still failing.
- **No video download**: Pipeline falls back to `youtube-transcript-api` (transcript-only, no frames). Still sufficient for guidelines.
- **Ollama not running**: `ollama serve` then retry, or frames.json will have `caption failed` entries — that's OK.
- **mlx-whisper slow on first run**: Downloads ~150MB model weights from HuggingFace. Subsequent runs use cache.

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

## Portal architecture reference

The portal at `/Users/brad/projects/code/abstracts/portal` serves all 18 games. Key paths:

| Content | Path |
|---|---|
| Tutorial JSONs | `portal/public/tutorials/<game-id>.json` |
| Game engines | `portal/src/games/<game-id>/Game.js` |
| Game apps | `portal/src/games/<game-id>/App.js` |
| Blog articles | `portal/src/views/blog/<Name>Article.jsx` |
| Blog index | `portal/src/views/Blog.jsx` |
| Tactics verifier | `portal/scripts/verify-tactics.mjs` |
| Sitemap | `portal/public/sitemap.xml` |

### Game ID mapping (common confusion)

| Game | URL path | Game ID | Loads from |
|---|---|---|---|
| Pente | `/game/pairs` | pairs | `games/stones/App` |
| Go | `/game/stones` | stones | `games/go/App` |
| Chess | `/game/knights` | knights | `games/knights/App` |
| Othello | `/game/flips` | flips | `games/flips/App` |

**Pente is `pairs`, not `stones`.** This is the most common ID confusion.

### Vercel deployment

Build command in `vercel.json`: `cd portal && npm install --legacy-peer-deps && CI=false GENERATE_SOURCEMAP=false npm run build`

- `CI=false` is required because Vercel sets `CI=true`, which makes Create React App treat warnings as errors (CSS order conflicts, missing source maps).
- After every push, check Vercel build status. Fix any failures before continuing.

### Tactics verification

After writing or modifying any tutorial puzzle:
```bash
cd /Users/brad/projects/code/abstracts/portal
node scripts/verify-tactics.mjs
```

The script loads each puzzle board into the game engine, applies correctMoves, checks outcomes, and scans for alternate solutions. Exit 0 = pass, exit 1 = failures.

## Writing style

All user-facing text (tutorials, blog articles, puzzle feedback, UI labels) must follow the style guide at `skills/writing-style/writing-style.md`. The single most important rule: **no em dashes**. Replace with commas, periods, or parentheses.

## Task and skill reference

| Task | Relevant skills / files |
|---|---|
| **Creating a new game** | |
| | `generic-game-plan.md` — phase-by-phase implementation template |
| | `skills/game-visual-analysis/` — pre-deploy QA pipeline (14 bug categories, includes visual testing) |
| | `skills/writing-style/` — voice guide for all user-facing text |
| **Creating a strategy tutorial** | |
| | `skills/tutorial-creation/` — full pipeline from PDF extraction to interactive JSON |
| | `skills/tutorial-verification/` — verify puzzles, text, mobile layout, learning progression |
| | `skills/strategy-pipeline/` — concept maps for specific games (Pente, Hex) |
| | `skills/writing-style/` — tutorial text conventions |
| | `skills/tactics-verification/` — engine verification of puzzle correctness |
| **Creating tactics puzzles** | |
| | `skills/tactics-creation/` — puzzle design patterns (Hex two-bridges, Pente captures, etc.) |
| | `skills/tactics-verification/` — automated verification against game engines |
| | `skills/writing-style/` — feedback and hint text conventions |
| **Creating or tuning game AI** | |
| | `skills/ai-creation/` — minimax, heuristic design, difficulty scaling, UI integration |
| | `generic-game-plan.md` (Phase 7) — AI architecture patterns |
| | `skills/ai-verification/` — naive strategy smoke tests per difficulty level |
| | `skills/game-visual-analysis/` — screenshot verification of AI behavior (includes visual testing) |
| **Verifying game AI** | |
| | `skills/ai-verification/` — run naive strategies against each difficulty |
| | Game engine files: `portal/src/games/<id>/Game.js` + `AI/ai.js` |
| **Writing or editing blog articles** | |
| | `skills/blog-articles/` — article conventions, components, game ID mapping |
| | `skills/writing-style/` — Brad Windsor voice guide, no em dashes rule |
| **Fixing bugs from user reports** | |
| | `skills/bug-fixing/` — three-stage workflow: reproduce, fix, update skill + Supabase |
| | `skills/game-visual-analysis/` — visual/layout/rule bug reproduction |
| | `skills/tutorial-verification/` — tutorial bug reproduction |
| | `skills/ai-verification/` — AI bug reproduction |
| **Pre-deploy quality assurance** | |
| | `skills/game-visual-analysis/` — 14-category visual bug audit |
| | `skills/tactics-verification/` — tutorial puzzle engine verification |
| | `skills/ai-verification/` — AI difficulty smoke tests |

## Self-improvement

While implementing games, you will encounter patterns, gotchas, and reusable techniques. Apply the following rule when deciding where improvements belong:

**Add to game-creation-agent** when the capability is game-agnostic — useful for any future game:
- A new tool in `tools/` + registered in `mcp_server.py` (e.g. a tool to diff two screenshots, or to validate HTML accessibility)
- A new or updated command in `commands/` (e.g. a new workflow step)
- A new pattern or gotcha in `skills/game-visual-analysis/SKILL.md`
- An update to `generic-game-plan.md` if a phase needs refinement based on experience

**Add to the target game's repo** when the code is game-specific:
- React components, game logic, CSS, assets
- Anything that references piece types, board layout, or rules of a particular game

**Never add game-specific code to game-creation-agent.** All code here must work regardless of which game is being built.

When you identify a self-improvement opportunity, propose it explicitly: "I noticed X pattern across this implementation. Should I add Y to game-creation-agent?" Get user approval before modifying this repo's files mid-implementation.
