"""
scaffold_game.py — Create a new game project from the standard template.

Usage:
    python3 tools/scaffold_game.py --name game-slug --dir /path/to/game-dir
    python3 tools/scaffold_game.py --name game-slug --dir /path/to/game-dir --plan plan.md
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys

TOOLS_DIR = os.path.dirname(__file__)
AGENT_DIR = os.path.dirname(TOOLS_DIR)

PACKAGE_JSON_TEMPLATE = {
    "version": "0.1.0",
    "private": True,
    "dependencies": {
        "@testing-library/jest-dom": "^6.6.3",
        "@testing-library/react": "^16.3.0",
        "@testing-library/user-event": "^14.6.1",
        "bootstrap": "^4.6.0",
        "react": "^19.1.0",
        "react-bootstrap": "^1.6.1",
        "react-dnd": "^10.0.2",
        "react-dnd-html5-backend": "^10.0.2",
        "react-dnd-touch-backend": "^16.0.1",
        "react-dom": "^19.1.0",
        "react-scripts": "^5.0.1",
    },
    "scripts": {
        "start": "react-scripts start",
        "build": "react-scripts build",
        "test": "react-scripts test",
        "eject": "react-scripts eject",
    },
    "eslintConfig": {"extends": "react-app"},
    "browserslist": {
        "production": [">0.2%", "not dead", "not op_mini all"],
        "development": ["last 1 chrome version", "last 1 firefox version", "last 1 safari version"],
    },
}

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title}</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
"""

INDEX_JS = """import React from 'react';
import ReactDOM from 'react-dom/client';
import 'bootstrap/dist/css/bootstrap.min.css';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<React.StrictMode><App /></React.StrictMode>);
"""

INDEX_CSS = """body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f5f5f5;
}
"""

APP_JS = """import React, {{ useState }} from 'react';
import './App.css';

// TODO: implement {title}
const App = () => {{
  return (
    <div style={{{{ padding: '20px', textAlign: 'center' }}}}>
      <h1>{title}</h1>
      <p>Implementation in progress.</p>
    </div>
  );
}};

export default App;
"""

APP_CSS = """/* {title} styles */
"""

GAME_JS = """// Game.js — core game state for {title}
// TODO: implement game logic

export function initGame() {{
  // Initialize and return game state
  return {{}};
}}

export function getValidMoves(state, player) {{
  // Return array of valid moves for player
  return [];
}}

export function applyMove(state, move) {{
  // Return new state after move (immutable)
  return {{ ...state }};
}}

export function checkWinner(state) {{
  // Return winning player id or null
  return null;
}}
"""

AI_JS = """// ai.js — AI player for {title}
// TODO: implement minimax AI

export function getAIMove(state, player, depth = 2) {{
  // Return the best move for player using minimax to given depth
  return null;
}}
"""

GITIGNORE = """node_modules/
build/
.env
.DS_Store
"""


def scaffold_game(name: str, game_dir: str, plan_path: str | None = None) -> None:
    title = name.replace("-", " ").title()
    src_dir = os.path.join(game_dir, "src")
    ai_dir = os.path.join(src_dir, "AI")
    public_dir = os.path.join(game_dir, "public")

    os.makedirs(src_dir, exist_ok=True)
    os.makedirs(ai_dir, exist_ok=True)
    os.makedirs(public_dir, exist_ok=True)

    # package.json
    pkg = dict(PACKAGE_JSON_TEMPLATE)
    pkg["name"] = name
    pkg_path = os.path.join(game_dir, "package.json")
    if not os.path.exists(pkg_path):
        with open(pkg_path, "w") as f:
            json.dump(pkg, f, indent=2)
        print(f"  Created package.json")
    else:
        print(f"  Skipped package.json (already exists)")

    # public/index.html
    html_path = os.path.join(public_dir, "index.html")
    if not os.path.exists(html_path):
        with open(html_path, "w") as f:
            f.write(INDEX_HTML.format(title=title))
        print(f"  Created public/index.html")

    # .gitignore
    gi_path = os.path.join(game_dir, ".gitignore")
    if not os.path.exists(gi_path):
        with open(gi_path, "w") as f:
            f.write(GITIGNORE)

    # src files — only create if missing
    files = {
        os.path.join(src_dir, "index.js"): INDEX_JS,
        os.path.join(src_dir, "index.css"): INDEX_CSS,
        os.path.join(src_dir, "App.js"): APP_JS.format(title=title),
        os.path.join(src_dir, "App.css"): APP_CSS.format(title=title),
        os.path.join(src_dir, "Game.js"): GAME_JS.format(title=title),
        os.path.join(ai_dir, "ai.js"): AI_JS.format(title=title),
    }
    for path, content in files.items():
        if not os.path.exists(path):
            with open(path, "w") as f:
                f.write(content)
            print(f"  Created {os.path.relpath(path, game_dir)}")
        else:
            print(f"  Skipped {os.path.relpath(path, game_dir)} (already exists)")

    # Copy generic game plan
    generic_plan = os.path.join(AGENT_DIR, "generic-game-plan.md")
    dest_plan = os.path.join(game_dir, "IMPLEMENTATION_PLAN.md")
    if plan_path and os.path.exists(plan_path):
        shutil.copy(plan_path, dest_plan)
        print(f"  Copied game-specific plan to IMPLEMENTATION_PLAN.md")
    elif os.path.exists(generic_plan) and not os.path.exists(dest_plan):
        shutil.copy(generic_plan, dest_plan)
        print(f"  Copied generic plan to IMPLEMENTATION_PLAN.md")

    # npm install
    print(f"\nRunning npm install in {game_dir}...")
    env = {**os.environ, "PATH": f"/opt/homebrew/bin:/usr/local/bin:{os.environ.get('PATH', '')}"}
    result = subprocess.run(
        ["/opt/homebrew/bin/npm", "install"],
        cwd=game_dir, capture_output=True, text=True, env=env, timeout=180,
    )
    if result.returncode == 0:
        print("  npm install succeeded")
    else:
        print(f"  npm install failed:\n{result.stderr[:500]}")

    print(f"\nScaffold complete: {game_dir}")
    print(f"Next steps:")
    print(f"  1. Review IMPLEMENTATION_PLAN.md")
    print(f"  2. Implement src/Game.js (game logic)")
    print(f"  3. Build UI in src/App.js")
    print(f"  4. Run: npm start")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True, help="Game slug (e.g. 'walls-game')")
    parser.add_argument("--dir", required=True, help="Target project directory")
    parser.add_argument("--plan", default=None, help="Path to game-specific plan markdown")
    args = parser.parse_args()

    scaffold_game(args.name, args.dir, args.plan)
