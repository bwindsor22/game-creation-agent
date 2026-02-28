"""Development workflow tools: build projects and manage dev servers."""
from __future__ import annotations

import os
import signal
import subprocess
import time


def build_project(project_dir: str) -> dict:
    """Run `npm run build` in the given project directory.

    Args:
        project_dir: Absolute path to the npm project root.

    Returns:
        Dict with keys:
          - "success": bool
          - "stdout": build output
          - "stderr": any error output
          - "returncode": process exit code
    """
    result = subprocess.run(
        ["/opt/homebrew/bin/npm", "run", "build"],
        cwd=project_dir,
        capture_output=True,
        text=True,
        env={**os.environ, "PATH": f"/opt/homebrew/bin:{os.environ.get('PATH', '')}"},
    )
    return {
        "success": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
    }


def start_dev_server(project_dir: str, port: int = 3000) -> dict:
    """Start an npm dev server in the background.

    Args:
        project_dir: Absolute path to the npm project root.
        port: Port to serve on (default 3000).

    Returns:
        Dict with keys:
          - "pid": process ID of the started server
          - "port": port number
          - "url": URL to access the server
    """
    env = {
        **os.environ,
        "PATH": f"/opt/homebrew/bin:{os.environ.get('PATH', '')}",
        "BROWSER": "none",
        "PORT": str(port),
    }
    proc = subprocess.Popen(
        ["/opt/homebrew/bin/npm", "start"],
        cwd=project_dir,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(8)
    return {"pid": proc.pid, "port": port, "url": f"http://localhost:{port}"}


def kill_dev_server(port: int = 3000) -> dict:
    """Kill any process listening on the given port.

    Args:
        port: Port number to free (default 3000).

    Returns:
        Dict with keys:
          - "killed_pids": list of PIDs that were killed
          - "port": port that was freed
    """
    result = subprocess.run(
        ["lsof", "-ti", f":{port}"],
        capture_output=True,
        text=True,
    )
    pids = [int(p) for p in result.stdout.strip().split() if p]
    killed = []
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
            killed.append(pid)
        except ProcessLookupError:
            pass
    return {"killed_pids": killed, "port": port}
