# Category 9: SVG Missing viewBox / Non-Responsive

**Difficulty estimate**: 1 (Trivial)

## Detection Signals

- SVG element renders at a fixed size regardless of viewport width
- Board is correct on desktop but too large on mobile (overflows container)
- Zooming the browser changes text size but SVG board remains the same absolute pixel size
- DevTools shows SVG has explicit `width` and `height` attributes but no `viewBox`

## Root Causes

An SVG with `width={boardWidth} height={boardHeight}` but no `viewBox` attribute renders at exactly those pixel dimensions. It does not scale down when its container is narrower than `boardWidth`. This is the most common cause of mobile board overflow.

## Known Fix Patterns

### Pattern A: Add viewBox + responsive style (canonical fix — applied to hexes, fives on 2026-03-28)
```jsx
// Before
<svg width={W} height={H} style={{ display: 'block' }}>

// After
<svg
  viewBox={`0 0 ${W} ${H}`}
  style={{ maxWidth: '100%', height: 'auto', display: 'block' }}
>
```

**How it works**:
- `viewBox="0 0 W H"` defines the SVG's internal coordinate system. The SVG can now scale.
- `maxWidth: '100%'` prevents it from exceeding its container.
- `height: 'auto'` maintains aspect ratio as width shrinks.
- The `width` and `height` attributes should be **removed** or can remain as a fallback for browsers that don't support CSS sizing of SVGs (very rare).

### Pattern B: Keep fixed width but make container scrollable
```jsx
<div style={{ overflowX: 'auto', maxWidth: '100%' }}>
  <svg width={W} height={H}>...</svg>
</div>
```
Use when proportional scaling is undesirable (e.g., the board needs to stay at a minimum playable size and should be scrolled, not shrunk).

## Known Failure Cases

- Applying `maxWidth: '100%'` to the SVG alone is insufficient if the SVG is inside a flex container that doesn't constrain width. The flex parent needs `min-width: 0` or `overflow: hidden`.
- After adding `viewBox`, verify that internal coordinate calculations (click positions, piece placement) still use the SVG's logical coordinate space, not CSS pixel coordinates. Most React SVG click handlers use `e.currentTarget.getBoundingClientRect()` + `viewBox` scale — these automatically adjust.

## Verification

After fix: screenshot at 375px width. The board should be fully visible and correctly proportioned (not stretched). Click interactions should still land on the correct cells.
