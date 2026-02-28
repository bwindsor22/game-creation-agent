Visually verify a game implementation by building it, screenshotting it, and comparing it against any reference images.

Usage: /game-creation-agent:visual-verify [project_dir]

Steps:
1. Use $ARGUMENTS as the project directory. If not provided, ask the user.
2. Call `build_project(project_dir)` — report build output and stop if it fails.
3. Call `start_dev_server(project_dir, port=3000)` and wait for it to be ready.
4. Call `take_screenshot('http://localhost:3000', output_path='/tmp/verify.png')`.
5. Check for reference images in `{project_dir}/resources/` (e.g. store-1.png, store-2.png). For each one found, call `ask_about_screenshot` comparing the current render to it: "How does this screenshot compare to the reference image at {path}? List specific differences in layout, shapes, colors, and positioning."
6. Ask targeted questions about the current screenshot:
   - "Are any labels, prices, or badges overlapping interactive elements?"
   - "Are all piece tokens circular, or do any have square/rectangular corners?"
   - "Are the store rows orderly horizontal rows, or are items wrapping unexpectedly?"
7. Call `kill_dev_server(3000)`.
8. Summarize all findings as a pass/fail list. Flag any visual regressions clearly.

Import pattern:
```python
import sys; sys.path.insert(0, '/path/to/game-creation-agent')
from tools.dev_tools import build_project, start_dev_server, kill_dev_server
from tools.screenshot_tool import take_screenshot
from tools.vision_tool import ask_about_screenshot
```
