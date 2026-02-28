---
name: game-visual-testing
description: Use when testing, verifying, or debugging the visual appearance or interactions of a game implementation. Covers screenshot-based visual testing, drag-and-drop interaction testing, and comparing renders to reference images.
---

# Game Visual Testing

## Screenshot workflow

Always follow this sequence to avoid orphaned server processes:

```
build_project(project_dir)
  → start_dev_server(project_dir, port)
    → take_screenshot(url)
      → ask_about_screenshot(path, specific_question)
        → kill_dev_server(port)
```

Kill the server even if an earlier step fails.

## Asking useful vision questions

The vision tool (`ask_about_screenshot`) returns much better results with **specific, answerable questions** than open-ended prompts:

- Good: "Are the price badges overlapping the piece tokens, or are they visually separated?"
- Good: "Are the piece tokens circular, or do they have square corners?"
- Good: "Do the store rows form clean horizontal lines, or are items wrapping to the next line?"
- Weak: "Does this look correct?" / "Describe the UI."

When reference images are available (e.g. in `project_dir/resources/`), pass each to `ask_about_screenshot` and ask explicitly how the current render differs.

## Drag-and-drop testing

**Critical**: Standard Playwright mouse events (`mouse.down`, `mouse.move`, `mouse.up`) do **not** trigger HTML5 drag-and-drop events. Libraries like react-dnd (HTML5Backend) listen for native `DragEvent` objects (`dragstart`, `dragenter`, `dragover`, `drop`, `dragend`).

Use `simulate_drag(url, source_selector, target_selector)` which dispatches these events correctly via `page.evaluate`.

`simulate_drag` returns:
- `before_path` / `after_path`: screenshot paths to compare visually
- `console_errors`: JS errors logged during the drag — always report these; they explain failed drops

## Layout debugging

Hex board geometry is sensitive to column widths. If a hex board loses its shape after a layout change:
- The board squares are likely fixed-pixel (intrinsic image size), not responsive
- Percentage-based row offsets are a function of column width — changing column width breaks the geometry
- Restore the original column width rather than adjusting the offset percentages

Store/inventory layout: prefer plain CSS flexbox (`justify-content: space-evenly; align-items: flex-end`) over Bootstrap Row/Col for game piece grids. Bootstrap columns add padding that causes wrapping when pieces have fixed widths.

## Price badge / token overlap

When a price badge overlaps a piece token in the store:
- Use `position: absolute; top: 0; left: 0` on the badge with `padding-top/left` on the container to create a corner badge that never overlaps
- Avoid `flexDirection: column` with badge below — this can still cause overlap when pieces are taller than expected

## Circular piece tokens

If piece images have square/rectangular transparent corners that obscure other elements, add `border-radius: 50%` to the `<img>` style. This clips the corners without requiring image editing.

## Reference image comparison

Store reference images in `project_dir/resources/`. When verifying layout changes, always compare against them. Ask: "How does this screenshot compare to [reference]? List specific differences in layout, shapes, colors, and positioning."
