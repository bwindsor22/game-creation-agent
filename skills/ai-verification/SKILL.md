---
name: ai-verification
description: Verifies game AI competence at each difficulty level by running naive strategies against them. Use this skill after implementing or modifying a game's AI, or when auditing existing AIs. The simplest possible strategy (e.g. a straight line) should not beat the medium AI. Also trigger when the user says "test AI", "verify AI", "AI too easy", "AI difficulty", or "check the AI".
---

## Why This Exists

AI difficulty levels are promises to the player. "Medium" should feel like a fair challenge. If a naive strategy (play in a straight line, always pick the first available move, etc.) can beat the medium AI, the difficulty label is misleading and the game feels broken.

## Naive Strategy Definitions

Define naive strategies per game type:

### Connection games (Hex, TwixT)
- **Straight line**: Play cells in a straight line from your starting edge toward your target edge. For Hex, this means playing (0, col), (1, col), (2, col), etc. down a single column. For TwixT, place pegs in a straight line top to bottom.
- **Random valid**: Pick a random empty cell each turn.

### Alignment games (Pente, Fives, Go)
- **Straight five**: In Pente/Fives, play 5 stones in a row without defending.
- **Center cluster**: Play all stones near the center, ignoring opponent threats.
- **Random valid**: Pick a random empty cell each turn.

### Movement games (Santorini/Towers, Chess/Knights, YINSH/Circles)
- **Greedy build**: In Santorini, always build next to yourself, alternating workers. Try to build two towers higher and higher to reach level 3.
- **First valid move**: Pick the first legal move in iteration order.
- **Random valid**: Pick a random legal move each turn.

### Mancala games (Sowing, Omweso)
- **Leftmost pit**: Always sow from the leftmost non-empty pit.
- **Random pit**: Pick a random non-empty pit.

### Other (Quoridor/Walls, Abalone/Marbles, Hive/Bugs, Tak/Stacks)
- **No walls**: In Quoridor, never place walls, just advance the pawn straight toward the goal.
- **First valid**: Pick the first legal move.
- **Random valid**: Pick a random legal move.

## Test Protocol

For each game and difficulty level:

1. **Load the game engine** (the Game.js pure logic module, no React).
2. **Run the naive strategy vs the AI** for N games (recommend N=5 for medium, N=3 for hard).
3. **Record results**: wins, losses, draws for the naive strategy.
4. **Pass/fail criteria**:
   - **Easy**: Naive strategy SHOULD win most games (>60%). Easy AI exists for beginners to enjoy.
   - **Medium**: Naive strategy should NOT win any games (0% win rate). If it wins even 1 out of 5, the AI is too weak.
   - **Hard**: Naive strategy should NOT win any games. Hard should be strictly stronger than medium.

## Implementation

The verification runs in Node.js, importing the game engine directly:

```javascript
// Example: Hex verification
import { initState, applyMove } from './src/games/hexes/Game.js';
import { getAIMove } from './src/games/hexes/AI/ai.js';

function naiveStraightLine(state, player) {
  // Play down column 5 (middle column)
  for (let r = 0; r < 11; r++) {
    if (state.board[r][5] === null) return [r, 5];
  }
  // Fallback: first empty cell
  for (let r = 0; r < 11; r++) {
    for (let c = 0; c < 11; c++) {
      if (state.board[r][c] === null) return [r, c];
    }
  }
  return null;
}

function runGame(difficulty, naiveStrategy) {
  let state = initState({ vsAI: true, difficulty });
  while (!state.winner) {
    if (state.currentPlayer === 'red') {
      // Naive strategy plays as red
      const [r, c] = naiveStrategy(state, 'red');
      state = applyMove(state, r, c);
    } else {
      // AI plays as blue
      const move = getAIMove(state, 'blue', difficulty);
      state = applyMove(state, move[0], move[1]);
    }
  }
  return state.winner === 'red' ? 'naive' : 'ai';
}
```

## Game-Specific Notes

### Hex (hexes)
- Straight line down center column is the primary naive test.
- AI should block the line and build its own connection.
- Board: 11x11. Red: top to bottom. Blue: left to right.

### TwixT (bridges)
- Straight line of pegs from top to bottom, linking each to the previous via knight's move.
- AI should cut the line with blocking pegs/links.

### Pente (stones)
- Build 5 in a row without defending opponent threats.
- Medium AI should create its own threats and/or capture to win.
- Game ID in portal: `pairs`. Engine at `src/games/stones/Game.js`.

### Santorini (towers)
- Greedy build: alternate workers, always build adjacent to the active worker, moving to the highest reachable cell.
- Medium AI should block level-3 climbs and build strategically.

### Chess (knights)
- First valid move (iterate pieces, pick first legal move).
- Medium AI should win comfortably against random/first-move play.

## Running the Verification

```bash
cd /path/to/abstracts/portal
node scripts/verify-ai.mjs
```

The script should:
1. Import each game's engine and AI
2. Run each naive strategy 5 times against medium
3. Print results table
4. Exit 0 if all pass, exit 1 if any naive strategy beats medium

## Extending to New Games

To add AI verification for a new game:
1. Define 2-3 naive strategies appropriate for the game type
2. Add an entry to the games array in the verification script
3. Implement the naive strategy functions
4. Run and verify

## What This Skill Does NOT Cover

- Whether the AI plays "well" in a subjective sense
- Whether hard AI is meaningfully harder than medium (that requires win-rate comparison between difficulties, not just naive tests)
- Whether the AI handles edge cases (that belongs in logic/rule testing)

This is a smoke test, not a comprehensive evaluation. It answers: "Is the medium AI at least competent enough to beat a player who isn't trying?"
