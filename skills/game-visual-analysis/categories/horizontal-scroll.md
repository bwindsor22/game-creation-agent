# Category 4: Unwanted Horizontal Page Scroll

**Difficulty estimate**: 1-2 (Trivial to Easy)

## Detection Signals

- At mobile viewports, the page can be scrolled sideways (the viewport is wider than the screen)
- A horizontal scrollbar appears on `body` or `html`
- Content is accessible but only via horizontal scroll (bad UX — users don't expect this)
- The board or some other element creates a wider layout than the viewport

## Root Causes

1. A child element has a fixed pixel width exceeding the viewport
2. A flex container's items overflow without wrapping
3. An absolutely-positioned element extends beyond the right edge
4. Negative margins pushing content outside viewport bounds

## Distinction: Board-level vs Page-level scroll

- **Board should scroll** (acceptable): The game board itself is wider than the screen and has `overflow-x: auto` — this is intentional for complex boards like Hive.
- **Page should not scroll** (bug): The overall page scrolls horizontally, meaning the nav, footer, and layout chrome are also shifted.

## Known Fix Patterns

### Pattern A: Prevent `body` from horizontal scrolling
```css
body {
  overflow-x: hidden;
}
```
**Warning**: This hides the symptom, not the cause. Use only as a last resort after fixing the root element.

### Pattern B: Find and fix the overflowing element
```css
/* Debug: temporarily add this to find what overflows */
* { outline: 1px solid red; }
```
Look for elements whose right edge exceeds `window.innerWidth`.

### Pattern C: Allow board-level horizontal scroll intentionally
```css
.board-wrapper {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch; /* smooth iOS momentum scrolling */
  max-width: 100%;
}
```
Applied to Hive (bugs game) board on 2026-03-28.

## Known Failure Cases

- Adding `overflow-x: hidden` to `body` breaks sticky/fixed position elements in Safari. Test after applying.

## Verification

On mobile screenshots, check that no horizontal scrollbar is visible on the main page. The board may have its own scrollbar — that's acceptable.
