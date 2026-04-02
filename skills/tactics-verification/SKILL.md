---
name: tactics-verification
description: Validates tutorial tactics puzzles against real game engines. Loads each puzzle board state, applies each correctMove through the game logic, and verifies the described outcome (win, capture, fork, threat) actually occurs. Use this skill after writing or modifying tactics puzzles, before pushing changes.
---

# Tactics Puzzle Verification

This skill validates that tutorial tactics puzzles are mechanically correct by running each puzzle through the actual game engine. It catches bugs where:

- A "win in one" puzzle doesn't actually produce a winner when the correct move is played
- A "capture" puzzle doesn't trigger the game's capture mechanic
- A "fork" puzzle doesn't create the described multi-threat position
- A correctMove points to an occupied cell
- Board state doesn't match what the puzzle text describes

## Why This Exists

Tutorial puzzles are authored as JSON with hand-crafted board states. The board coordinates and piece positions are easy to get wrong, especially for:

- **Pente captures**: Requires exactly `YOUR-OPP-OPP-YOUR` in a line with no gaps. Missing one stone in the sandwich means no capture.
- **Hex connections**: A path must be contiguous through hex neighbors. One wrong coordinate breaks the chain.
- **Prior state**: Capture-win puzzles need the correct number of prior captures set.

These bugs are invisible in code review but immediately obvious when a player completes a puzzle and sees the wrong outcome.

## Quick Start

Run the verification script from the portal directory:

```bash
cd /path/to/abstracts/portal
node scripts/verify-tactics.mjs
```

Exit code 0 = all pass, exit code 1 = failures found.

## How It Works

### 1. Board Reconstruction

Tutorial JSON stores boards as objects like `{"9,7": "black", "9,8": "white"}`. The script converts these to the game engine's native 2D array format:

```javascript
// JSON → Pente board (19x19 array)
state.board[9][7] = 'black';
state.board[9][8] = 'white';

// JSON → Hex board (11x11 array)
state.board[5][5] = 'red';
```

### 2. Puzzle Classification

Each puzzle is classified by its text and lesson title to determine what outcome to verify:

| Classification | Trigger Keywords | Expected Outcome |
|---|---|---|
| `setup` | lesson "Forced Win in Three" | Cell is adjacent to player's stones |
| `immediate-win` | "five in a row", "complete the five", lesson "Forced Win in One" | `applyMove()` returns `winner !== null` |
| `capture-win` | "fifth capture", "win by capture", "4 captures" | Capture count reaches 5, `winner !== null` |
| `capture` | "capture" (without win context) | Capture count increases |
| `fork` | "two threats", "double tria", "fork", lesson "Forced Win in Two" | At least one three-in-a-row created |
| `threat` | "extend", "tria", lesson "Win in Two" | At least three-in-a-row or four-in-a-row created |

### 3. Engine Verification

For each correctMove, the script:
1. Builds the game state from the JSON board
2. Sets prior captures if needed (capture-win puzzles assume 4 prior captures)
3. Calls the game engine's `applyMove(state, row, col)`
4. Checks the returned state against the expected outcome
5. Reports failures with specific details
6. **Alternate solution scan**: For each empty cell NOT in `correctMoves`, applies the move and checks if it produces the same outcome. If so, reports `ALT-SOLUTION`. For Pente, compares formations before/after to avoid false positives from pre-existing patterns. For Hex, only checks `immediate-win` (other types need opponent modeling).

### 4. Specific Checks Per Game

**Pente (stones)**:
- Custodian capture: `player-opp-opp-player` in any of 8 directions from placed stone
- Five-in-a-row: 5+ consecutive same-color stones in any of 4 directions
- Win by capture: `captures[player] >= 5`

**Hex (hexes)**:
- Win: BFS from starting edge to ending edge through contiguous same-color cells
- Red: row 0 to row 10. Blue: col 0 to col 10
- Hex neighbors: `[-1,0], [-1,1], [0,-1], [0,1], [1,-1], [1,0]`

## Issue Log (Known Failure Cases)

Historical bugs encountered during tactics verification. Check for these on every run:

- **Puzzle has unlisted alternate solution (most common failure)**: An empty cell not in `correctMoves` also produces the expected outcome. The alternate-solution scanner catches these for Pente and Hex. For other games, manually scan cells adjacent to correctMoves.
- **Pente capture puzzle missing sandwich stone**: The capture mechanic requires `YOUR-OPP-OPP-YOUR` in a line. A common error is having the opponent pair but no friendly stone at the far end to complete the sandwich.
- **Pente fork puzzle with stones on wrong row (misaligned three-in-a-row)**: Double-tria puzzles need two lines of 2 stones each intersecting at the correctMove cell. Stones placed on adjacent rows don't form a line through the target.
- **Hex puzzle gap at wrong coordinate (path doesn't connect via BFS)**: A "win in one" hex puzzle must have a contiguous path with exactly one gap. One wrong coordinate in the hex neighbor grid breaks the chain. Verify with the 6-direction neighbor formula: `[[-1,0], [-1,1], [0,-1], [0,1], [1,-1], [1,0]]`.
- **Capture-win puzzle with wrong prior capture count**: "Fifth capture" puzzles must have exactly 4 prior captures set in the game state. If the count is wrong, the capture doesn't trigger a win.
- **"Forced Win in Three" puzzle where the forced gap isn't actually forced (has two bridge cells)**: A gap that looks forced actually has two valid bridge cells, making it a two-bridge. Both cells complete the connection, so the puzzle has two solutions at the first step. Fix: add a blocker stone at one bridge cell.
- **Em dashes in feedback/hint text**: The writing style guide prohibits em dashes. They appear in puzzle explanation text, hint text, and feedback strings. Grep for them after every edit.
- **Defensive "Block the Win" puzzles classified as threats**: Blocking puzzles where the player prevents the opponent from winning were misclassified as "threat" or "capture-win" and failed verification. Fixed by adding a "block" classification that triggers when lesson title includes "block" and text includes "block"/"prevent"/"defend". Block puzzles verify: (1) opponent CAN win without the block, and (2) opponent CANNOT win after the block.
- **Open four with both ends unblocked (unsolvable block puzzle)**: A block-the-win puzzle with an open four (four in a row with both ends empty) is unsolvable because blocking one end leaves the other open. Fix: add a stone at one end so only one blocking move is needed.
- **Lesson auto-completing when it has no puzzles**: TutorialMode's `isLessonComplete` marked all-explain lessons as done because every step was "not a puzzle." Fix: return false when a lesson has no puzzle steps.
- **Chess fork puzzle where the forking piece is capturable**: A knight fork puzzle placed the knight on a square defended by an opponent pawn. The fork is technically correct (it attacks two pieces) but tactically wrong (the knight is immediately captured). Fix: remove the defending pawn. Verify-tactics.mjs does not currently check whether the forking piece survives; this requires chess-specific defense validation.
- **Chess tutorial arrows too faint to see**: Arrow overlays at `strokeWidth: 2.5` and `opacity: 0.7` were nearly invisible on mobile screens. Fix: increase to `strokeWidth: 4`, `opacity: 0.85`, and enlarge the arrowhead marker.
- **YINSH "block the score" threat not actually achievable**: A block puzzle claimed the opponent threatens five in a row, but no opponent ring was positioned to create the 5th marker. In YINSH, moving a ring leaves a marker at the ring's starting position. So an opponent ring must sit at one end of the row for the threat to be real. Fix: add an opponent ring at the end of the marker row.
- **Tutorial text references coordinates but board has no labels**: Puzzle text like "move to (-2,1)" is useless when the board shows no coordinate labels. Fix: replace all coordinate references with spatial descriptions ("the highlighted ring," "to the right," "the first empty cell past the markers").
- **Tutorial board too large for container (SVG without viewBox)**: The Board SVG used a fixed `width` attribute without a `viewBox`, so it couldn't scale down within the tutorial container. Fix: add `viewBox` and use `width: 100%` with `maxWidth`.
- **Solved tutorial state doesn't show move result (ring stays, markers don't flip)**: When `buildTutorialState` just placed a ring at the destination without running the engine, the original ring remained and jumped markers were not flipped. Fix: use `getValidMoves` to find the source ring, then `applyMove` to compute the real post-move state showing the marker left behind and flipped markers.

---

## Common Failure Patterns

### Pattern 1: Missing sandwich stone (Pente captures)

The capture mechanic requires `YOUR-OPP-OPP-YOUR` in a straight line from the placed stone. A common error is having the opponent's pair on the board but no friendly stone to complete the sandwich.

**Example**: Board has `black(9,5), white(9,8), white(9,9)`. Placing at `(9,10)` checks direction [0,-1]: finds white at (9,9), white at (9,8), then needs black at (9,7) -- but (9,7) is empty. No capture.

**Fix**: Ensure a same-color stone exists exactly 3 cells away from the placed stone in the capture direction.

### Pattern 2: Wrong capture count for capture-win

"Fifth capture" puzzles must have 4 prior captures in the game state. The verification script sets `captures.black = 4` for these puzzles. If the board also shows uncaptured pairs from "previous" captures, those pairs should NOT be on the board (they've already been removed).

### Pattern 3: Misaligned three-in-a-row (fork puzzles)

Double-tria puzzles need two separate lines of 2 stones each that intersect at the correctMove cell. A common error is placing stones on different rows/columns that don't actually form a line through the target cell.

**Correct**: `(8,7)` and `(8,9)` intersect at `(8,8)` horizontally. `(7,8)` and `(9,8)` intersect at `(8,8)` vertically.

**Wrong**: `(9,7)` and `(9,9)` don't intersect at `(8,8)` -- they're on row 9, but `(8,8)` is on row 8.

### Pattern 4: Hex path gap

A "win in one" hex puzzle must have a contiguous path from edge to edge with exactly one gap. If the gap cell is at the wrong coordinate, the path won't connect.

**Verification**: After placing the stone, BFS from row 0 must reach row 10 (for Red).

### Pattern 5: Unblocked alternate winning move (Pente)

A "win in two" puzzle where the player extends a tria (three in a row) to a tessera (four in a row) may have an alternate solution: extending the tria in the *other* direction also creates a four-in-a-row. The alt-solution scanner catches this.

**Fix**: Add an opponent stone at the alternate extension point.

**Example**: Black has stones at (8,8), (8,9), (8,10). Placing at (8,11) makes four in a row. But placing at (8,7) also makes four in a row. Fix: add `"8,7": "white"` to the board.

### Pattern 6: Hex two-bridge with both cells valid

A "win in two" hex puzzle where a two-bridge gap has two valid bridge cells. Both cells complete the connection. If only one is listed in correctMoves, the other shows as ALT-SOLUTION.

**Fix**: Add both bridge cells to correctMoves, or add a Blue stone at one to make it a forced (single-bridge) gap.

### Pattern 7: Open four in block puzzle (unsolvable)

A "Block the Win" puzzle that presents an open four (both ends empty) is inherently unsolvable. Blocking one end leaves the other, and the opponent wins regardless.

**Correct**: Place a friendly stone at one end so the four has exactly one open end to block.

**Wrong**: `white: (9,7), (9,8), (9,9), (9,10)` with both (9,6) and (9,11) empty. Player can't block both.

**Fix**: Add `"9,6": "black"` to the board, leaving only (9,11) as the correct block.

### Pattern 8: Block puzzle misclassified as capture-win

When a "Block the Win" lesson contains text about opponent captures (e.g., "White has 4 captures"), the classifier may match "capture-win" before "block." The fix: check lesson title for "block" BEFORE text-based classification.

## Extending to New Games

To add verification for a new game:

1. Implement the game's core logic (initState, applyMove, win detection) as functions in the verification script
2. Add a `jsonBoardToXxxState()` converter for the tutorial JSON format
3. Add a `verifyXxxPuzzle()` function with game-specific checks
4. Register the game in the `games` array at the bottom of the script

The game engines in `src/games/*/Game.js` are pure logic with no React dependencies, so they can be adapted for Node.js verification by inlining the core functions.

## Running After Every Puzzle Edit

Add to your workflow:

```bash
# After editing any tutorial JSON with tactics puzzles
node scripts/verify-tactics.mjs

# If failures found, fix the board state and re-run
# Common fixes:
# - Add missing sandwich stone for captures
# - Move stones to correct coordinates for three-in-a-row
# - Verify hex neighbor adjacency with the 6-direction formula
```

## Integration with Other Skills

This skill complements:
- **`tactics-creation/`**: Design patterns for constructing puzzles. Read it before writing new puzzles.
- **`pre-deploy-qa`** (in `game-visual-analysis/`): Catches visual bugs. This skill catches logic bugs. Run both before pushing.
- **`tutorial-creation/`**: Phase 5 (Verification) calls this script.

```bash
node scripts/verify-tactics.mjs    # Logic verification
# Then run pre-deploy-qa for visual checks
```

## File Locations

- Verification script: `portal/scripts/verify-tactics.mjs`
- Pente tutorial JSON: `portal/public/tutorials/stones.json`
- Hex tutorial JSON: `portal/public/tutorials/hexes.json`
- Pente game engine: `portal/src/games/stones/Game.js`
- Hex game engine: `portal/src/games/hexes/Game.js`
