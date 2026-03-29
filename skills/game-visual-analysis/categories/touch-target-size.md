# Category 3: Touch Target Size < 44px

**Difficulty estimate**: 1-2 (Trivial to Easy)

## Detection Signals

- Interactive elements (buttons, links, checkboxes, small icons) appear physically small in mobile screenshots
- Users report tapping a button but triggering a nearby element instead
- Tappable icons are < 44px in either dimension (Apple HIG and WCAG 2.5.5 both require 44x44px minimum)

## Root Causes

1. The element has an explicit `width`/`height` set to a small pixel value (e.g. `width: 24px`)
2. The element inherits a small font-size that shrinks padding-based sizing
3. Icon-only buttons (no label) rely on the icon's intrinsic size, which is smaller than 44px

## Known Fix Patterns

### Pattern A: Add minimum tap area with padding
```css
.icon-button {
  padding: 10px; /* adds invisible tappable area around the icon */
  min-width: 44px;
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
}
```

### Pattern B: Use `min-width`/`min-height` directly on the element
```css
button, a, [role="button"] {
  min-height: 44px;
  min-width: 44px;
}
```

### Pattern C: Expand hit area with `::after` pseudo-element (no layout change)
```css
.small-icon-button {
  position: relative;
}
.small-icon-button::after {
  content: '';
  position: absolute;
  top: -12px; right: -12px; bottom: -12px; left: -12px;
}
```

## Known Failure Cases

- Pattern A can cause layout shifts when applied to inline elements. Wrap in a block container first.

## Verification

In browser DevTools, inspect the computed size of each interactive element on a 375px viewport. All should be >= 44x44px.
