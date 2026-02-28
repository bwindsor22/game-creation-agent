Test a drag-and-drop interaction on a running game and report what changed visually and whether any errors occurred.

Usage: /game-creation-agent:test-drag [url] [source-selector] [target-selector]

Steps:
1. Parse $ARGUMENTS for `url`, `source_selector`, and `target_selector`. If any are missing, ask the user. Default url is `http://localhost:3000`.
2. Call `simulate_drag(url, source_selector, target_selector, output_path='/tmp/drag-test')`.
3. The result contains:
   - `before_path`: screenshot before the drag
   - `after_path`: screenshot after the drag
   - `console_errors`: any JS errors logged during the interaction
4. Call `ask_about_screenshot(before_path, "Describe the state of the game board and piece positions.")`.
5. Call `ask_about_screenshot(after_path, "Describe the state of the game board and piece positions. What changed compared to before the drag?")`.
6. Report console errors verbatim if any exist — these often explain why a drag had no effect.
7. Assess: did the piece move as expected? Did game state update? Were there errors?

Important: Standard Playwright mouse events do not trigger HTML5 drag-and-drop (react-dnd HTML5Backend). The `simulate_drag` tool dispatches native `DragEvent` objects via `page.evaluate`, which is required for react-dnd to respond.

Import pattern:
```python
import sys; sys.path.insert(0, '/path/to/game-creation-agent')
from tools.screenshot_tool import simulate_drag
from tools.vision_tool import ask_about_screenshot
```
