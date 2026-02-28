"""Claude vision analysis tool."""
from __future__ import annotations

import base64
import os


def ask_about_screenshot(image_path: str, question: str) -> str:
    """Ask Claude a question about an image.

    Args:
        image_path: Path to the PNG image file.
        question: Question to ask about the image.

    Returns:
        Claude's answer as a string.
    """
    import anthropic

    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": question,
                    },
                ],
            }
        ],
    )
    return message.content[0].text
