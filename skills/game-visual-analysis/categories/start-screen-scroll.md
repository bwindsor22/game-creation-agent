# Category 6: Start Screen Scrolled to Bottom on Navigation

**Difficulty estimate**: 2-3 (Easy to Medium)

## Detection Signals

- User scrolls down a list of games on the portal home screen to find a game
- After selecting and loading a game, the start screen appears but is scrolled down to show the bottom portion
- User sees buttons at the bottom before scrolling up to see the game title and description
- First visual impression is of buttons and secondary content, not the game name

## Root Causes

1. Scroll position is not reset when navigating from a scrolled list to a new screen
2. The start screen shares a scroll container with the game list; scroll position carries over
3. React Router or a similar SPA router does not reset scroll on route change
4. The new screen mounts into a container that has retained scroll offset from a previous render

## Known Fix Patterns

### Pattern A: Scroll to top on route change (React Router)
```jsx
import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}

// Add <ScrollToTop /> inside <Router>
```

### Pattern B: Scroll to top on component mount
```jsx
useEffect(() => {
  window.scrollTo({ top: 0, behavior: 'instant' });
}, []); // empty dep array = runs on mount only
```
Add this to the StartScreen component.

### Pattern C: Reset scroll on the container element (not window)
```jsx
const containerRef = useRef(null);
useEffect(() => {
  if (containerRef.current) containerRef.current.scrollTop = 0;
}, [selectedGame]);
```

## Known Failure Cases

- `behavior: 'smooth'` causes a visible scroll animation — use `'instant'` for immediate reset.
- Pattern A requires `react-router-dom` and won't work for apps that manage navigation via state instead of URLs.

## Verification

1. Scroll down on the game selection list
2. Select a game
3. Verify the start screen appears at the top (title visible, not scrolled down)
