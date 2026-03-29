# Category 2: FAB / Fixed-Button Overlap with Tutorial Navigation

**Difficulty estimate**: 1 (Trivial)

## Detection Signals

- In tutorial mode, the "Next" or "Back" navigation buttons are partially or fully hidden
- A fixed-position button (help "?", bug report icon, or other FAB) sits at the same screen position as the tutorial nav
- On desktop this is fine; on mobile (375px-480px) the FABs are large enough to cover nav buttons
- User cannot advance or go back in tutorial steps

## Root Causes

In this portal:
- `game-guide-fab` (the "?" help button): `position: fixed; bottom: 20px; right: 20px`
- `bug-report-fab`: `position: fixed; bottom: 20px; left: 20px`
- Tutorial `.tutorial-bottom` panel: contains Back/Next buttons near the bottom of the screen

On mobile, the tutorial bottom panel sits behind the FABs because the panel doesn't account for the FABs' height.

## Known Fix Patterns

### Pattern A: Add bottom padding to tutorial panel on mobile (applied 2026-03-28)
```css
/* TutorialMode.css */
@media (max-width: 480px) {
  .tutorial-bottom {
    padding: 8px 10px 80px; /* clears both fixed FABs (each ~56px + 20px gap) */
  }
}
```
This pushes the tutorial content up so Next/Back are above the FAB zone.

### Pattern B: Hide FABs while tutorial is active
```jsx
// In App.js, pass tutorialMode to the FAB components
{!tutorialMode && <GameGuideFab />}
{!tutorialMode && <BugReportFab />}
```
Cleaner, but requires tutorial state to be accessible at the layout level.

## Known Failure Cases

- **padding-bottom not enough on very small screens**: If the tutorial panel also has its own min-height constraint, the padding may be absorbed. Check that `.tutorial-bottom` has no `min-height` that prevents the padding from taking effect.
- **Pattern B hides the bug report button during tutorial**: Users can't report bugs they encounter in the tutorial itself. Pattern A is preferred for this reason.

## Verification

After applying fix: take screenshot at 375px width while tutorial is on a step with Next/Back visible. Both buttons should be fully visible above the FAB zone.
