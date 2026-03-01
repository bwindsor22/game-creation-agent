#!/usr/bin/env python3
"""CLI wrapper: run npm build in a project directory.

Usage:
    python3 npm_build.py /path/to/project

Prints build output, exits with 0 on success or 1 on failure.
"""
import os
import subprocess
import sys


def npm_build(project_dir: str) -> dict:
    """Run `npm run build` in project_dir and return results."""
    env = {**os.environ, "PATH": f"/opt/homebrew/bin:{os.environ.get('PATH', '')}"}
    result = subprocess.run(
        ["/opt/homebrew/bin/npm", "run", "build"],
        cwd=project_dir,
        capture_output=True,
        text=True,
        env=env,
    )
    return {
        "success": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <project_dir>", file=sys.stderr)
        sys.exit(1)

    project_dir = sys.argv[1]
    result = npm_build(project_dir)

    if result["stdout"]:
        print(result["stdout"])
    if result["stderr"]:
        print(result["stderr"])

    if result["success"]:
        print(f"\nBuild succeeded (exit {result['returncode']})")
    else:
        print(f"\nBuild FAILED (exit {result['returncode']})", file=sys.stderr)

    sys.exit(0 if result["success"] else 1)
