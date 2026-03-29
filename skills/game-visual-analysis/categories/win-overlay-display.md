# Category 14: Win Overlay Missing Elo or Showing Wrong Values

**Difficulty estimate**: 2-3 (Easy to Medium)

## Detection Signals

- Game ends but the win overlay shows no rating change
- Elo rating shown is 1200 (default) regardless of game history
- Rating change is always +0 or always the same value
- Win overlay shows correct winner but Elo section is absent entirely
- Rating decreases after a win (sign error)

## Root Causes

1. `eloInfo` prop not passed to `WinOverlay` — it's defined but not wired
2. `computeEloChange` called before `gameState.winner` is set (race condition in useEffect)
3. `gameId` passed to `computeEloChange` doesn't match the key used in `getHistory()` storage
4. `difficulty` not available at win time — game uses `'medium'` hardcoded or undefined
5. Custom win overlay (mills, omweso, sowing, towers, walls, trees) has Elo display but `eloInfo` is not computed

## Known Fix Patterns

### Pattern A: Wire computeEloChange in winner useEffect
```jsx
import { computeEloChange } from '../../utils/storage';

// In App.js, inside the effect that fires when winner is determined:
useEffect(() => {
  if (!gameState.winner) return;
  const won = gameState.winner === 'player'; // adjust to match game's winner value
  setEloInfo(computeEloChange('gameid', won, gameState.difficulty || 'medium'));
}, [gameState.winner]);

// Pass to WinOverlay:
<WinOverlay winner={gameState.winner} eloInfo={eloInfo} onRestart={handleRestart} />
```

### Pattern B: Check that gameId matches storage key
`computeEloChange(gameId, ...)` uses `gameId` to filter `getHistory()`. The gameId must exactly match the string used when saving game results. Check `saveResult('gameid', ...)` calls in the same file.

### Pattern C: Custom overlay -- add eloInfo display manually
For games with custom overlays that don't use the shared `WinOverlay`:
```jsx
{eloInfo && (
  <div style={{ textAlign: 'center', marginTop: 12 }}>
    <div>Rating: {eloInfo.rating}</div>
    <div style={{ color: eloInfo.change >= 0 ? '#4caf50' : '#f44336' }}>
      {eloInfo.change >= 0 ? '+' : ''}{eloInfo.change}
    </div>
  </div>
)}
```

## Known Failure Cases

- `computeEloChange` returns `{ rating: 1200, change: 0 }` when there's no history. This is correct behavior (first game). Do not flag as a bug.
- If `won` is computed wrong (e.g., `gameState.winner === 'red'` when the player is red but difficulty check shows the AI is red), the rating change sign will be reversed. Verify that "won" means the human player won, not just that some color won.

## Verification

1. Play a game against Easy AI and win
2. Check the win overlay: rating change should be positive (won against lower-rated AI)
3. Play against Hard AI and lose: change should be negative
4. Play again: accumulated rating should reflect previous games
