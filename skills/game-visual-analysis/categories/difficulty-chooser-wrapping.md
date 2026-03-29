# Category 5: Difficulty Chooser Layout Wrapping

**Difficulty estimate**: 1-2 (Trivial to Easy)

## Detection Signals

- On mobile, the difficulty selection buttons (Easy / Medium / Hard) wrap to multiple lines unevenly
- "Medium" and "Hard" are on one line, "Easy" is alone on a second line (or vice versa)
- Large gap between buttons causes them to push apart and wrap when the container is narrow
- The difficulty section takes up excessive vertical space on mobile

## Root Causes

1. `gap` or `margin` between buttons is too large for narrow viewports
2. Buttons have fixed widths that don't shrink
3. Flex container with `flex-wrap: wrap` wraps at an intermediate breakpoint

## Known Fix Patterns

### Pattern A: Reduce gap between buttons (applied to bugs/Hive on 2026-03-28)
```jsx
// Before
<div style={{ display: 'flex', gap: 40 }}>

// After
<div style={{ display: 'flex', gap: 16 }}>
```

### Pattern B: Allow buttons to shrink
```css
.difficulty-button {
  flex: 1 1 auto; /* grow and shrink */
  min-width: 60px;
}
```

### Pattern C: Reduce font size or padding on mobile
```css
@media (max-width: 480px) {
  .difficulty-button {
    padding: 6px 12px;
    font-size: 14px;
  }
}
```

## Known Failure Cases

- Reducing gap too much (< 8px) makes the buttons feel cramped on large phones. 12-16px is the sweet spot.
- Pattern B with `flex: 1` makes all buttons equal width, which looks good. But if the labels have very different lengths ("Easy" vs "Very Hard"), equal-width can look strange.

## Verification

Take screenshot at 375px width. All three difficulty buttons should be on a single row with consistent spacing.
