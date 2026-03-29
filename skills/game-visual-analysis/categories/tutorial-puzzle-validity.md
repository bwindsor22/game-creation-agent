# Category 10: Tutorial Puzzle Has No Valid Solution

**Difficulty estimate**: 2-3 (Easy to Medium)

## Detection Signals

- A tutorial step with `type: "puzzle"` has `correctMoves` that point to cells that are:
  - Already occupied in the `board` state
  - Not strategically meaningful (don't actually achieve the stated goal)
  - Impossible to reach (wrong row/col indexing)
- User cannot advance past a tutorial puzzle because no move is accepted
- Tutorial description says "block your opponent" but no move in `correctMoves` actually achieves that on the given board

## Root Causes

1. Board state and correctMoves were defined independently and fell out of sync
2. Puzzle was copied from a previous step and correctMoves wasn't updated for the new board
3. correctMoves uses 0-indexed rows while the renderer uses 1-indexed rows (or vice versa)
4. The board state encodes a position where multiple moves could win, but only a subset are in correctMoves -- user found the right move but it wasn't in the list

## Known Fix Patterns

### Pattern A: Manually verify each correctMove against the board state
For each `[row, col]` in `correctMoves`:
1. Check the `board` object: the cell `"row,col"` must not have a piece already
2. Visually place that move mentally and verify it achieves the tutorial step's stated goal

### Pattern B: Replace complex puzzle with a clear single-solution puzzle (applied to hexes on 2026-03-28)
The hexes tutorial had a puzzle "block Red while helping Blue connect" with no valid solution. It was replaced with a direct blocking puzzle where correctMoves are clearly optimal and unambiguous.

```json
{
  "type": "puzzle",
  "text": "Block Red's winning path by playing in one of these cells.",
  "board": { ... },
  "correctMoves": [[4,3],[4,4],[5,3],[5,4]],
  "highlights": [[4,3],[4,4],[5,3],[5,4]]
}
```

### Pattern C: Expand correctMoves to include all equivalent winning moves
If the puzzle has multiple solutions (e.g., "any of these 4 cells blocks Red"), include all of them in `correctMoves` so users who find any valid solution are accepted.

## Known Failure Cases

- Puzzles that require "block AND connect simultaneously" tend to have very few valid moves and are hard to verify. Split them into two separate steps: one blocking puzzle, one connection puzzle.
- Highlights that show correctMoves can spoil the puzzle if shown before the user tries. Verify that highlights only appear after solving or via a hint button.

## Known Failure Cases (added 2026-03-28)

- **Flips (Othello) tutorial bugs** (9a60bf55, 3f443ffb, 659ed556): Tutorial text described board positions (e.g., "Row 0 has white discs at columns C-E") that didn't match the actual JSON board state. The board state was correct for the puzzle, but the explanatory text was auto-generated and referenced wrong coordinates. Fix: audit every `explain` step's text against its `board` object.
- **Text-board drift**: When tutorial text uses coordinate labels (row/column) to describe the board, verify every coordinate mention against the JSON. Common issue: text says "column B" but piece is at index 1 (which might be column A depending on 0/1 indexing).

## Verification

For each tutorial JSON file:
1. Read every puzzle step
2. For each correctMove `[r, c]`: verify `board["r,c"]` is undefined (cell is empty)
3. Mentally or visually confirm the move achieves the tutorial step's stated goal
4. For each explain step: verify every coordinate/position mentioned in `text` matches the `board` object
5. For each puzzle step: verify `wrongFeedback` and `hint` text reference correct coordinates
