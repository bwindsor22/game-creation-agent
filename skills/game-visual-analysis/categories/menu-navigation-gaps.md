# Category 8: Menu Navigation Gaps (Feature Only Reachable via One Path)

**Difficulty estimate**: 1-2 (Trivial to Easy)

## Detection Signals

- "Learn to Play" tutorial is accessible from the start screen but not from the in-game menu
- "Strategy Guide" appears in one menu but is absent from another where users would expect it
- A settings option exists at game start but disappears once gameplay begins
- Users can't find rules help after starting a game without quitting

## Root Causes

1. Feature was added to one entry point (start screen) but the in-game menu wasn't updated
2. Menu item was removed from one view due to space constraints and never added back
3. The in-game menu uses a different component than the start screen, leading to feature drift

## Known Fix Patterns

### Pattern A: Add missing menu items to in-game menu overlay (applied to hexes on 2026-03-28)
```jsx
// In App.js menu overlay section
{menuOpen && (
  <div className="menu-overlay">
    <button onClick={() => { setMenuOpen(false); setTutorialMode('learn'); }}>
      Learn to Play
    </button>
    <button onClick={() => { setMenuOpen(false); setTutorialMode('strategy'); }}>
      Strategy Guide
    </button>
    {/* ... other menu items */}
  </div>
)}
```

### Pattern B: Extract menu items into a shared component
Create a `<GameMenu items={[...]} />` component used in both the start screen and in-game overlay, so they always stay in sync.

## Known Failure Cases

- Adding "Learn to Play" to the in-game menu but not wiring it to `setTutorialMode` causes a click with no effect. Always test that the button actually opens the tutorial.

## Verification

1. Screenshot the start screen and list all navigation options
2. Start a game, open the menu, list all options
3. Compare: every tutorial/help option available before game start should also be available in-game
