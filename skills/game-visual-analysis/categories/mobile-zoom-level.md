# Category 12: Board Too Zoomed In or Out on Mobile Initial View

**Difficulty estimate**: 2-3 (Easy to Medium)

## Detection Signals

- On mobile, the game loads with the board so zoomed in that only a fraction of cells are visible
- Conversely, the board may be so small that pieces are unreadably tiny
- The initial camera/viewport position shows the center of the board but not the full board
- 3D games (Santorini, Tak) may load at a camera angle that hides far-side towers/pieces

## Root Causes

1. **3D games (react-three-fiber)**: Camera `position` or `fov` set for desktop; mobile needs a different position/distance
2. **SVG/CSS games**: Container `transform: scale(...)` or initial scroll offset positions the view mid-board
3. **Canvas games**: Canvas size vs CSS size mismatch causes scaling at an unintended ratio
4. **Initial camera for OrbitControls**: `target` or `distance` not adjusted for mobile

## Known Fix Patterns

### Pattern A: Responsive camera position (react-three-fiber)
```jsx
const isMobile = window.innerWidth < 768;
const cameraPosition = isMobile ? [0, 14, 10] : [0, 10, 8];

<Canvas camera={{ position: cameraPosition, fov: 45 }}>
```

### Pattern B: Adjust `minDistance` on OrbitControls for mobile
```jsx
<OrbitControls
  minDistance={isMobile ? 8 : 5}
  maxDistance={isMobile ? 20 : 15}
/>
```

### Pattern C: CSS `transform-origin` + scale for non-3D boards
```css
@media (max-width: 480px) {
  .board-container {
    transform: scale(0.8);
    transform-origin: top center;
  }
}
```
**Warning**: This scales click coordinates too — test interactions after applying.

## Known Failure Cases

- Pattern C (CSS scale) breaks click event coordinate mapping unless the game accounts for the scale factor.
- `window.innerWidth` inside React renders may be stale if the window resizes. Use a `useWindowSize` hook or media query for responsive camera control.

## Verification

Screenshot at 375px on game load. The full board should be visible with pieces/cells large enough to tap. For 3D games, all cells should be in view (no fog or off-screen edges).
