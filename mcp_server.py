"""MCP server exposing game-creation tools to Claude Desktop and MCP-compatible agents."""
from __future__ import annotations

import asyncio
import json

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from tools.pdf_tool import pdf_to_text
from tools.screenshot_tool import take_screenshot, simulate_drag
from tools.vision_tool import ask_about_screenshot
from tools.npm_build import npm_build
from tools.dev_tools import start_dev_server, kill_dev_server

app = Server("game-creation")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="pdf_to_text",
            description="Extract text from a PDF file. Useful for reading board game rulebooks.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the PDF file.",
                    },
                    "pages": {
                        "type": "string",
                        "description": "Optional page range, e.g. '1-5' or '3'. Defaults to all pages.",
                    },
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="take_screenshot",
            description="Take a screenshot of a URL using headless Chromium.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to screenshot.",
                    },
                    "selector": {
                        "type": "string",
                        "description": "Optional CSS selector to screenshot just one element.",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Where to save the PNG. Defaults to a temp file.",
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="simulate_drag",
            description=(
                "Simulate an HTML5 drag-and-drop action on a live web page using Playwright. "
                "Works with react-dnd HTML5Backend. Returns before/after screenshot paths and "
                "any console errors. Use this to verify that drag-and-drop interactions work correctly."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL of the page to test."},
                    "source_selector": {
                        "type": "string",
                        "description": "CSS selector for the drag source element.",
                    },
                    "target_selector": {
                        "type": "string",
                        "description": "CSS selector for the drop target element.",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Base path for output screenshots (optional).",
                    },
                    "wait_after_ms": {
                        "type": "integer",
                        "description": "Milliseconds to wait after drop before screenshotting. Default 500.",
                    },
                },
                "required": ["url", "source_selector", "target_selector"],
            },
        ),
        Tool(
            name="npm_build",
            description="Run `npm run build` in any npm project directory. Returns stdout, stderr, and success flag.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_dir": {
                        "type": "string",
                        "description": "Absolute path to the npm project root.",
                    },
                },
                "required": ["project_dir"],
            },
        ),
        Tool(
            name="start_dev_server",
            description="Start the trees-game dev server in the background. Waits for it to be ready and returns the URL.",
            inputSchema={
                "type": "object",
                "properties": {
                    "port": {"type": "integer", "description": "Port number (default 3000)."},
                },
            },
        ),
        Tool(
            name="kill_dev_server",
            description="Kill the trees-game dev server by freeing the port it's listening on.",
            inputSchema={
                "type": "object",
                "properties": {
                    "port": {"type": "integer", "description": "Port number to free (default 3000)."},
                },
            },
        ),
        Tool(
            name="ask_about_screenshot",
            description="Ask Claude a question about an image (screenshot or any PNG).",
            inputSchema={
                "type": "object",
                "properties": {
                    "image_path": {
                        "type": "string",
                        "description": "Path to the PNG image file.",
                    },
                    "question": {
                        "type": "string",
                        "description": "Question to ask about the image.",
                    },
                },
                "required": ["image_path", "question"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "pdf_to_text":
        result = pdf_to_text(arguments["path"], arguments.get("pages"))
        return [TextContent(type="text", text=result)]

    if name == "take_screenshot":
        path = take_screenshot(
            arguments["url"],
            selector=arguments.get("selector"),
            output_path=arguments.get("output_path"),
        )
        return [TextContent(type="text", text=path)]

    if name == "simulate_drag":
        import json as _json
        result = simulate_drag(
            arguments["url"],
            arguments["source_selector"],
            arguments["target_selector"],
            output_path=arguments.get("output_path"),
            wait_after_ms=arguments.get("wait_after_ms", 500),
        )
        return [TextContent(type="text", text=_json.dumps(result, indent=2))]

    if name == "npm_build":
        import json as _json
        result = npm_build(arguments["project_dir"])
        return [TextContent(type="text", text=_json.dumps(result, indent=2))]

    if name == "start_dev_server":
        import json as _json
        result = start_dev_server(port=arguments.get("port", 3000))
        return [TextContent(type="text", text=_json.dumps(result, indent=2))]

    if name == "kill_dev_server":
        import json as _json
        result = kill_dev_server(port=arguments.get("port", 3000))
        return [TextContent(type="text", text=_json.dumps(result, indent=2))]

    if name == "ask_about_screenshot":
        answer = ask_about_screenshot(arguments["image_path"], arguments["question"])
        return [TextContent(type="text", text=answer)]

    raise ValueError(f"Unknown tool: {name}")


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
