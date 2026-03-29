# Category 11: Color / Player Legend Not Wrapping on Narrow Screens

**Difficulty estimate**: 1 (Trivial)

## Detection Signals

- At 375px viewport, the player color legend (e.g., "Red • Blue" or "Black • White") overflows its container
- Legend items are truncated or pushed offscreen
- On desktop the legend is on one line; on mobile it should wrap to two lines but doesn't
- The legend container has no `flex-wrap` and the items have enough width to overflow

## Root Causes

A flex legend container without `flex-wrap: wrap` forces all items onto one line, even when the viewport is too narrow. At mobile widths the container overflows rather than wrapping.

## Known Fix Patterns

### Pattern A: Add flexWrap to legend div (applied to hexes on 2026-03-28)
```jsx
// Before
<div style={{ display: 'flex', gap: 16 }}>
  <span>Red</span>
  <span>Blue</span>
</div>

// After
<div style={{ display: 'flex', flexWrap: 'wrap', gap: 16, justifyContent: 'center' }}>
  <span>Red</span>
  <span>Blue</span>
</div>
```

### Pattern B: CSS class with media query
```css
.player-legend {
  display: flex;
  gap: 16px;
}

@media (max-width: 480px) {
  .player-legend {
    flex-direction: column;
    align-items: center;
    gap: 8px;
  }
}
```

## Known Failure Cases

- `flexWrap: wrap` with large gaps can cause each legend item to appear on its own line even when there's room for two per row. Use `gap: 8px` or less on mobile.

## Verification

Screenshot at 375px. All player color labels should be fully readable, either side-by-side or wrapped to separate lines — neither truncated nor overflowing.
