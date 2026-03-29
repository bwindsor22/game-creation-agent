# Category 13: Piece Promotion Auto-Selects Without Player Choice

**Difficulty estimate**: 3 (Medium)

## Detection Signals

- In chess-variant games, a pawn reaching the last rank is automatically promoted to queen (or another piece) without showing the player a choice
- Code generates promotion move variants but selects `moves[0]` instead of prompting
- No promotion picker modal or menu appears when a pawn promotes
- Players who want a knight or rook promotion have no way to get it

## Root Causes

1. The game engine generates all promotion variants (QQ, QR, QB, QN) as separate moves, but the UI just picks the first one
2. The promotion move type is detected by checking piece type or move notation, but the result is applied immediately instead of triggering a UI state

## Known Fix Patterns

### Pattern A: Add PromotionPicker modal (applied to knights/App.js on 2026-03-28)
```jsx
function PromotionPicker({ color, onPick }) {
  const pieces = ['Q', 'R', 'B', 'N'];
  const chars = {
    Q: color === 'w' ? '\u2655' : '\u265b',
    R: color === 'w' ? '\u2656' : '\u265c',
    B: color === 'w' ? '\u2657' : '\u265d',
    N: color === 'w' ? '\u2658' : '\u265e',
  };
  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.75)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 300 }}>
      <div style={{ background: '#1e0f32', borderRadius: 12, padding: 24 }}>
        <div>Promote pawn to:</div>
        <div style={{ display: 'flex', gap: 10 }}>
          {pieces.map(p => (
            <button key={p} onClick={() => onPick(p)} style={{ fontSize: 36 }}>
              {chars[p]}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
```

In `handleSquareClick`: detect promotion moves and set `pendingPromo` state instead of applying immediately:
```jsx
const promoMoves = moves.filter(m => m.flags && m.flags.includes('p'));
if (promoMoves.length > 0) {
  setPendingPromo({ from: selected, to: sq, color: currentTurn });
  return;
}
```

Then `handlePromotion(piece)` filters `promoMoves` for the chosen piece type and applies it.

## Known Failure Cases

- If the engine represents promotion as a flag on the move object rather than separate move entries, the filter logic needs to match that API. Read the engine's move format before implementing.
- The PromotionPicker must render ABOVE the board (z-index > board elements). Test that clicking piece buttons doesn't accidentally also trigger board click handlers.

## Verification

1. Set up a position with a pawn on the 7th rank (for white)
2. Move the pawn to the 8th rank
3. Verify: a picker appears with 4 piece options
4. Select Rook — verify the pawn becomes a rook, not a queen
