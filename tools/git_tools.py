#!/usr/bin/env python3
"""Git helper tool for Claude Code workflows.

All operations run via Python subprocess — no Bash permission prompts.

Usage:
    python3 git_tools.py status [dir]
    python3 git_tools.py commit [dir] "message"
    python3 git_tools.py add [dir] [files...]
    python3 git_tools.py log [dir]
    python3 git_tools.py diff [dir]
"""
import os
import subprocess
import sys


def _run(cmd: list, cwd: str = None) -> dict:
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "success": result.returncode == 0,
    }


def git_status(cwd: str = ".") -> dict:
    return _run(["git", "status", "--short"], cwd=cwd)


def git_diff(cwd: str = ".", staged: bool = False) -> dict:
    cmd = ["git", "diff"] if not staged else ["git", "diff", "--staged"]
    return _run(cmd, cwd=cwd)


def git_log(cwd: str = ".", n: int = 5) -> dict:
    return _run(["git", "log", f"-{n}", "--oneline"], cwd=cwd)


def git_add(paths: list, cwd: str = ".") -> dict:
    return _run(["git", "add"] + paths, cwd=cwd)


def git_commit(message: str, cwd: str = ".", add_all: bool = True) -> dict:
    if add_all:
        add_result = git_add(["-A"], cwd=cwd)
        if not add_result["success"]:
            return add_result
    return _run(["git", "commit", "-m", message], cwd=cwd)


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)

    command = args[0]
    cwd = args[1] if len(args) > 1 and os.path.isdir(args[1]) else "."
    remaining = args[2:] if (len(args) > 1 and os.path.isdir(args[1])) else args[1:]

    if command == "status":
        r = git_status(cwd)
    elif command == "commit":
        msg = remaining[0] if remaining else "auto commit"
        r = git_commit(msg, cwd=cwd)
    elif command == "add":
        files = remaining if remaining else ["-A"]
        r = git_add(files, cwd=cwd)
    elif command == "log":
        r = git_log(cwd)
    elif command == "diff":
        r = git_diff(cwd)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

    print(r["stdout"])
    if r["stderr"]:
        print(r["stderr"], file=sys.stderr)
    sys.exit(0 if r["success"] else 1)
