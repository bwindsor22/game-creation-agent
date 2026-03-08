"""
generate_game_plan.py — Combine a game's rulebook PDF + generic-game-plan.md into a
concrete, game-specific implementation plan using Claude.

Usage:
    python3 tools/generate_game_plan.py --pdf path/to/rules.pdf --game "Game Name" --output plan.md
    python3 tools/generate_game_plan.py --research path/to/research.md --game "Game Name" --output plan.md
"""
from __future__ import annotations

import argparse
import os
import sys

import anthropic

_KEY_FILE = os.path.expanduser("~/projects/.anthropic_api_key")
if "ANTHROPIC_API_KEY" not in os.environ and os.path.exists(_KEY_FILE):
    os.environ["ANTHROPIC_API_KEY"] = open(_KEY_FILE).read().strip()

GENERIC_PLAN_PATH = os.path.join(os.path.dirname(__file__), "..", "generic-game-plan.md")

PROMPT = """You are a senior game developer planning the implementation of a browser-based board game.

Below is a generic 7-phase implementation template, followed by the rules and research for a specific game.
Your job: produce a CONCRETE, game-specific implementation plan by adapting the template to this game.

For each phase, be specific:
- Name every piece type and describe its visual representation
- Describe the exact board layout (grid size, shape, coordinate system)
- List every rule that affects valid moves, with precise conditions
- Define win conditions and scoring with exact formulas
- Identify the trickiest rules to implement and flag them
- Describe the AI heuristic: what to maximize, what board features to score

Output a markdown document structured exactly like the generic plan (Phase 1 through Phase 7),
but with all details filled in for this specific game. Do NOT copy generic placeholders — every
sentence should be specific to {game_name}.

---
GENERIC TEMPLATE:
{generic_plan}

---
GAME RULES / RESEARCH:
{rules_text}
"""


def load_text(path: str, max_chars: int = 20000) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()[:max_chars]


def load_pdf_text(pdf_path: str, max_chars: int = 15000) -> str:
    sys.path.insert(0, os.path.dirname(__file__))
    try:
        from pdf_tool import pdf_to_text  # type: ignore
        return pdf_to_text(pdf_path)[:max_chars]
    except Exception as e:
        return f"(PDF extraction failed: {e})"


def generate_game_plan(game_name: str, rules_text: str, output_path: str) -> str:
    generic_plan = load_text(GENERIC_PLAN_PATH)

    client = anthropic.Anthropic()

    prompt = PROMPT.format(
        game_name=game_name,
        generic_plan=generic_plan,
        rules_text=rules_text,
    )

    print(f"Generating game plan for '{game_name}'...")

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=6000,
        messages=[{"role": "user", "content": prompt}],
    )

    result = response.content[0].text.strip()
    header = f"# {game_name} — Implementation Plan\n\n_Generated from generic-game-plan.md + rulebook_\n\n"
    full = header + result

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full)

    print(f"Saved to {output_path} ({len(full)} chars)")
    return full


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--game", required=True, help="Human-readable game name")
    parser.add_argument("--pdf", default=None, help="Path to PDF rulebook")
    parser.add_argument("--research", default=None, help="Path to research markdown (from game_research.py)")
    parser.add_argument("--output", required=True, help="Output path for the plan markdown")
    args = parser.parse_args()

    rules_text = ""
    if args.pdf:
        print(f"Extracting PDF: {args.pdf}")
        rules_text += load_pdf_text(args.pdf)
    if args.research:
        print(f"Loading research: {args.research}")
        rules_text += "\n\n" + load_text(args.research)

    if not rules_text.strip():
        print("ERROR: provide --pdf and/or --research", file=sys.stderr)
        sys.exit(1)

    generate_game_plan(args.game, rules_text, args.output)
