"""
research_all_games.py — Run game_research.py for all game projects.

Game names and PDF paths are read from each project's resources/name.txt and
resources/ directory — never hardcoded here. This file contains no game names.
"""
import glob
import os
import subprocess

PROJECTS_DIR = "/Users/brad/projects/code"
TOOLS_DIR = os.path.dirname(__file__)

# Load API key from safe location outside any git repo
_KEY_FILE = os.path.expanduser("~/projects/.anthropic_api_key")
if "ANTHROPIC_API_KEY" not in os.environ and os.path.exists(_KEY_FILE):
    os.environ["ANTHROPIC_API_KEY"] = open(_KEY_FILE).read().strip()


def discover_games(projects_dir: str) -> list[dict]:
    """Find all game projects that have a resources/name.txt file."""
    games = []
    for name_file in sorted(glob.glob(os.path.join(projects_dir, "*/resources/name.txt"))):
        game_dir = os.path.dirname(os.path.dirname(name_file))
        game_slug = os.path.basename(game_dir)
        game_name = open(name_file).read().strip()

        # Find first PDF in resources/ (if any)
        pdfs = sorted(glob.glob(os.path.join(game_dir, "resources", "*.pdf")))
        pdf_path = pdfs[0] if pdfs else None

        games.append({
            "dir": game_dir,
            "slug": game_slug,
            "name_file": name_file,
            "pdf": pdf_path,
        })
    return games


if __name__ == "__main__":
    games = discover_games(PROJECTS_DIR)
    if not games:
        print(f"No games found. Add resources/name.txt to each game project.")
        raise SystemExit(1)

    procs = []
    for game in games:
        output_path = os.path.join(game["dir"], "resources", "research.md")
        # Read name at runtime — never interpolated into this committed file
        game_name = open(game["name_file"]).read().strip()

        cmd = [
            "/usr/bin/python3",
            os.path.join(TOOLS_DIR, "game_research.py"),
            game_name,
            output_path,
        ]
        if game["pdf"]:
            cmd += ["--pdf", game["pdf"]]

        print(f"Starting: {game['slug']} -> {output_path}")
        p = subprocess.Popen(cmd, env={**os.environ})
        procs.append((game["slug"], p))

    print(f"\nAll {len(procs)} research jobs started. Waiting...\n")
    for slug, p in procs:
        p.wait()
        status = "OK" if p.returncode == 0 else f"FAILED (exit {p.returncode})"
        print(f"  {slug}: {status}")

    print("\nDone.")
