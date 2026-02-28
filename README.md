# game-creation-agent

An agentic system for converting board game rule PDFs into playable web implementations.

## Purpose

This agent takes a board game rulebook PDF and produces a working browser-based game. It operates in a loop:

1. **Extract rules** — read and parse the PDF rulebook into structured text
2. **Screenshot & inspect** — render the current game implementation in a browser and capture screenshots
3. **Vision analysis** — ask Claude to evaluate whether the rendered UI matches the rules
4. **Generate / iterate** — produce or refine code until the implementation matches the rules

## Tools

All tools are exposed as an MCP server (`mcp_server.py`) so they work with Claude Desktop or any MCP-compatible agent runner.

### `pdf_to_text(path, pages=None)`
Extracts text from a PDF. Uses `pypdf` by default; falls back to `pdfminer.six` if the output is empty or garbled. `pages` accepts ranges like `"1-5"` or a single page like `"3"`.

### `take_screenshot(url, selector=None, output_path=None)`
Opens a URL in headless Chromium via Playwright, waits for network idle, and saves a full-page PNG (or just the matched `selector` element). Returns the path to the saved image.

### `ask_about_screenshot(image_path, question)`
Base64-encodes an image and sends it to Claude (claude-sonnet-4-6) with a question. Returns Claude's answer as a string.

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
```

Set `ANTHROPIC_API_KEY` in your environment before running vision queries.

## Running the MCP server

```bash
python mcp_server.py
```

To register with Claude Desktop, add the following to `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "game-creation": {
      "command": "python",
      "args": ["/path/to/game-creation-agent/mcp_server.py"]
    }
  }
}
```
