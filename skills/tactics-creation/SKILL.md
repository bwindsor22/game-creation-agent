---
name: tactics-creation
description: Design interactive tactics puzzles for abstract strategy games. Use this skill when creating "win in one", "win in two", "win in three", capture, fork, or threat puzzles for any game's tutorial. Also trigger when the user says "make puzzles", "add tactics", "forced win", "create lessons", or "write puzzles" for a game tutorial.
---

# Tactics Puzzle Creation

This skill covers designing and constructing interactive tactics puzzles for board game tutorials. The output is a set of puzzle steps in the tutorial JSON format, verified against the game engine.

**The central principle:** Every puzzle must have exactly one correct answer (or a small, explicitly listed set of equivalent answers). If a puzzle has an unlisted alternate solution, it's broken.

---

## Step 1: Choose Puzzle Type

Each puzzle teaches a specific tactical pattern. Pick the type before constructing the board.

### Universal Types

| Type | What the player learns | Difficulty |
|---|---|---|
| Immediate win | Spot the winning move | Easiest |
| Capture | Execute a capture mechanic | Easy |
| Fork / double threat | Create two threats the opponent can't both answer | Medium |
| Forced win in two | Set up a position where the next move wins by force | Medium |
| Forced win in three | Fill the forced gap first, leaving two-bridges | Hard |
| Setup | Place a stone that enables a future forced sequence | Hard |

### Game-Specific Patterns

**Hex (hexes):**
- **Two-bridge**: Two empty cells both connect two groups across a 2-row gap. Opponent blocks one, you take the other. This is the foundational Hex tactic.
- **Forced win in one**: A contiguous path from edge to edge with exactly one gap. BFS confirms the win after placement.
- **Forced win in two**: Two gaps in a chain, each a two-bridge. Player fills one; opponent blocks the other bridge cell; player takes the remaining cell.
- **Forced win in three**: Three gaps in a chain. One gap has only one bridge cell (forced). The other two are two-bridges. Player must fill the forced gap first.
- **Hex neighbors**: `[[-1,0], [-1,1], [0,-1], [0,1], [1,-1], [1,0]]`. Red wins row 0 to row 10. Blue wins col 0 to col 10.

**Pente (stones):**
- **Custodian capture**: Place a stone to complete `YOUR-OPP-OPP-YOUR` in a straight line (8 directions).
- **Five in a row**: Place the 5th consecutive stone in any direction.
- **Capture win**: Make a 5th capture (requires 4 prior captures set in game state).
- **Fork / double tria**: Place a stone at the intersection of two lines that each already have 2 of your stones, creating two three-in-a-rows simultaneously.
- **Keystone / threat**: Extend an existing line to create a four-in-a-row (unstoppable next turn).

---

## Step 2: Construct the Board Position

### Design principles

1. **Minimal pieces**: Use the fewest pieces needed to demonstrate the concept. Extra pieces are distracting and increase the chance of unintended alternate solutions.

2. **Block alternate solutions**: After placing your intended correct move(s), mentally scan every other empty cell. Ask: "Does placing here also win / capture / create a fork?" If yes, either:
   - Add opponent stones to block the alternate
   - Rearrange the position to eliminate the alternate
   - Add the alternate to `correctMoves` (only if it teaches the same concept)

3. **Look like a real game**: Positions should feel plausible. Avoid symmetric or obviously artificial layouts. Place some opponent stones that look like they could have been played during a real game.

4. **One concept per puzzle**: Don't combine capture + fork in the same puzzle. Teach them separately.

### Hex-specific construction

- Board is 11x11 (rows 0-10, columns 0-10).
- Red's edges: row 0 (top) and row 10 (bottom). Blue's edges: col 0 (left) and col 10 (right).
- A "chain" is a connected path of same-color cells through hex neighbors.
- A "gap" is a break in the chain where one or two empty cells could reconnect it.
- A "two-bridge" gap has exactly two empty cells that are both hex-neighbors of the cells on either side of the gap. The opponent can block one; the player takes the other.
- A "forced" gap has only one empty cell that bridges it. If the opponent doesn't block it, the player completes it for free. This is why forced gaps must be filled first.
- For "Forced Win in Three" puzzles: build a chain with 3 gaps. Make 1 gap forced (single bridge cell) and 2 gaps two-bridges. The correct first move is always the forced gap.
- Always verify the chain by running BFS from one edge to the other with all gaps filled.

### Pente-specific construction

- Board is 19x19 (rows 0-18, columns 0-18). JSON uses `"row,col": "color"`.
- Capture requires exactly `YOUR-OPP-OPP-YOUR` in one of 8 directions from the placed stone. The closing stone (3 cells away in the capture direction) must already be on the board.
- For capture-win puzzles: set prior captures to 4 in the verification script. Don't leave captured pairs on the board (they've been removed in prior captures).
- For fork puzzles: the correctMove cell must be at the intersection of two lines that each have exactly 2 of your stones, forming two three-in-a-rows through the target cell. Common error: stones on the wrong row/column that don't actually pass through the target.
- For "win in two" / Keystone puzzles: extending a tria (three in a row) to a tessera (four in a row) is unstoppable. But check that extending in the OTHER direction doesn't also work. If it does, add an opponent stone to block it.

---

## Step 3: Write the JSON

### Tutorial JSON structure

```json
{
  "type": "puzzle",
  "text": "Instruction telling the player what to look for.",
  "board": {
    "row,col": "color",
    "row,col": "color"
  },
  "correctMoves": [[row, col], [row, col]],
  "rightFeedback": "Why this move is correct. Ties back to the concept.",
  "wrongFeedback": "Hint toward the right approach without giving it away.",
  "hint": "More specific hint if the player is stuck."
}
```

### Text conventions

- **Puzzle text**: Tell the player what pattern to find, not where to click. "Red has a chain with three gaps. Find the one gap that has only one bridge cell." Not "Play at (3,3)."
- **Right feedback**: Explain WHY the move works. "Correct! (3,3) is the only cell bridging the gap at row 3. The remaining two gaps are two-bridges. Blue can block one cell of each, but Red takes the other."
- **Wrong feedback**: Point toward the right analysis. "Trace Red's chain from top to bottom. One gap has only one possible bridge cell. Fill that one first."
- **Hint**: More specific than wrongFeedback. "The gap between rows 2 and 4 has only one bridge cell. The gaps at rows 5 and 8 each have two options."
- **No em dashes**. Use commas, periods, or parentheses for asides. This is a hard rule across all user-facing text.

### Lesson structure

Group 3-4 puzzles into a lesson. Each lesson:
1. Starts with 1-2 `info` or `explain` steps that introduce the concept
2. Follows with 2-3 `puzzle` steps of increasing difficulty
3. The first puzzle should be straightforward (one obvious answer)
4. Later puzzles can add distractors or require deeper analysis

---

## Step 4: Verify

**Always run the tactics verification script after writing or modifying puzzles.**

```bash
cd /path/to/abstracts/portal
node scripts/verify-tactics.mjs
```

The script:
1. Loads each puzzle's board state into the game engine
2. Applies each correctMove
3. Checks the expected outcome (win, capture, fork, etc.)
4. Scans all empty cells for alternate solutions not listed in correctMoves
5. Reports failures and alternate solutions

Fix every failure before pushing. Common fixes:
- **ALT-SOLUTION reported**: Add the alternate to correctMoves (if it teaches the same concept) or add an opponent stone to block it
- **Expected win but no winner**: The board state doesn't actually produce a win when the move is applied. Check coordinates.
- **Capture not triggered**: Missing sandwich stone. Ensure `YOUR-OPP-OPP-YOUR` pattern in at least one direction from the correctMove.

See `tactics-verification/SKILL.md` for full details on the verification script.

---

## Step 5: Playtest

After verification passes:
1. Open the tutorial in the browser
2. Step through each puzzle as a player would
3. Try wrong answers to confirm wrongFeedback appears
4. Try the correct answer to confirm rightFeedback and visual state change
5. Check mobile (390px viewport) for text overflow and board fit

---

## Common Mistakes

| Mistake | How to avoid |
|---|---|
| Puzzle has multiple valid solutions | Run alt-solution scanner. Block alternates with opponent stones. |
| Board position is impossible | Check that piece counts and positions could arise in a real game. |
| CorrectMove points to occupied cell | Double-check coordinates against the board object. |
| Feedback text has em dashes | Search for the — character. Replace with commas or periods. |
| Hex puzzle: gap has wrong neighbor count | Verify with the 6-direction hex neighbor formula. |
| Pente puzzle: capture direction wrong | Check all 8 directions from the placed stone: [0,1],[0,-1],[1,0],[-1,0],[1,1],[-1,-1],[1,-1],[-1,1]. |
| "Win in three" but forced gap isn't first | The forced (single-bridge) gap must be the correctMove. Two-bridges resolve themselves. |
