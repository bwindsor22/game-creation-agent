# Category 1: Mobile Board Overflow (Left/Right Edge Clipping)

**Difficulty estimate**: 1-2 (Trivial to Easy)

## Detection Signals

- At 375px or 390px viewport, the left or right edge of the game board is cut off
- Player cannot see corner cells, edge pieces, or border lines
- No horizontal scrollbar appears where one should (or page scrolls instead of board)
- Board appears to start at x=0 but visually clips the first column

## Root Causes

1. **SVG missing `viewBox`**: An SVG element with fixed `width`/`height` attributes but no `viewBox` renders at fixed pixel size. On small screens the right side (or both sides if centered with negative margins) overflows.
2. **Fixed pixel width on container**: A `div` wrapper has `width: 800px` or similar; mobile viewport is narrower.
3. **Negative margin or padding offset**: Container uses `margin-left: -20px` or similar to center; on small screens this shifts content offscreen.
4. **`overflow: hidden` on a parent**: The board renders correctly but a parent clips it.

## Known Fix Patterns

### Pattern A: Add viewBox to SVG (most common — fixes hexes, fives, go, stones)
```jsx
// Before
<svg width={boardWidth} height={boardHeight}>

// After
<svg
  viewBox={`0 0 ${boardWidth} ${boardHeight}`}
  style={{ maxWidth: '100%', height: 'auto' }}
>
```
This makes the SVG scale down proportionally on narrow viewports while maintaining aspect ratio.

### Pattern B: Responsive wrapper div
```css
.board-container {
  max-width: 100%;
  overflow-x: auto;
}
```
Use when the board must remain a fixed pixel size (e.g., 3D canvas) but should be scrollable on mobile.

### Pattern C: Remove fixed width, use percentage
```css
/* Before */
.board { width: 600px; }

/* After */
.board { width: min(600px, 100%); }
```

## Known Failure Cases

- **Pattern A alone insufficient when board is inside a flex row**: If the SVG's parent is `display: flex` with other siblings, the SVG may still shrink below usable size. Fix: add `flex: 1; min-width: 0` to the SVG's flex parent.
- **Pattern B causes entire page to scroll horizontally**: If applied too high in the DOM. Apply `overflow-x: auto` only on the immediate board container, not on `body` or `main`.

## Verification

After applying fix: take screenshot at 375px width. Left edge of first column should be fully visible with no clipping.
