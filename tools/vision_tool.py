"""Ollama vision analysis tool (no Anthropic API key required)."""
from __future__ import annotations

import base64
import json
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/generate"
VISION_MODEL = "llava-phi3"


def ask_about_screenshot(image_path: str, question: str) -> str:
    """Ask a vision model a question about an image via Ollama.

    Args:
        image_path: Path to the PNG image file.
        question: Question to ask about the image.

    Returns:
        The model's answer as a string.
    """
    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    payload = json.dumps({
        "model": VISION_MODEL,
        "prompt": question,
        "images": [image_data],
        "stream": False,
    }).encode()

    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read())
    return result.get("response", "").strip()
