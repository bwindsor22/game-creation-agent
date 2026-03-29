---
name: ai-creation
description: Guide for implementing game AI at multiple difficulty levels. Covers minimax with alpha-beta pruning, heuristic design, difficulty scaling, and integration with the game UI. Use when building a new AI or adding difficulty levels.
---

# Game AI Implementation Guide

This skill covers building AI opponents for abstract strategy board games. The goal is multiple difficulty levels that feel fair and responsive, from a beatable easy mode to a challenging hard mode.

---

## Architecture

### File organization

AI code lives in `src/AI/ai.js`, separate from rendering and game logic:

```
src/
  Game.js          # Pure game logic (state, moves, win detection)
  App.js           # React UI, turn management, AI integration
  AI/
    ai.js          # Entry point: executeAITurn(), getAIMove(), difficulty routing
    ai_minimax.js  # Minimax search + heuristic evaluation (optional separate file)
```

The game engine (`Game.js`) must be pure functional with no React dependencies. The AI imports the engine directly for lookahead simulation.

### Core principle: pure functional applyMove

The AI needs to simulate many future game states during search. This requires a pure `applyMove(state, move)` function that returns a new state without mutating the input:

```javascript
// CORRECT: returns new state, input unchanged
function applyMove(state, move) {
  const newBoard = state.board.map(row => [...row]);
  newBoard[move.row][move.col] = state.currentPlayer;
  return { ...state, board: newBoard, currentPlayer: otherPlayer(state.currentPlayer) };
}

// WRONG: mutates input state, breaks minimax tree
function applyMove(state, move) {
  state.board[move.row][move.col] = state.currentPlayer;
  state.currentPlayer = otherPlayer(state.currentPlayer);
  return state;
}
```

If the game engine uses mutation internally, write a separate `cloneState()` + `simulateMove()` for the AI.

---

## Minimax with Alpha-Beta Pruning

Use minimax with alpha-beta for most abstract strategy games. It works well for two-player, zero-sum, perfect-information games.

### Basic structure

```javascript
function minimax(state, depth, alpha, beta, maximizing) {
  if (depth === 0 || state.winner) {
    return evaluate(state);
  }

  const moves = getValidMoves(state);

  if (maximizing) {
    let maxEval = -Infinity;
    for (const move of moves) {
      const newState = applyMove(state, move);
      const eval = minimax(newState, depth - 1, alpha, beta, false);
      maxEval = Math.max(maxEval, eval);
      alpha = Math.max(alpha, eval);
      if (beta <= alpha) break; // prune
    }
    return maxEval;
  } else {
    let minEval = Infinity;
    for (const move of moves) {
      const newState = applyMove(state, move);
      const eval = minimax(newState, depth - 1, alpha, beta, true);
      minEval = Math.min(minEval, eval);
      beta = Math.min(beta, eval);
      if (beta <= alpha) break; // prune
    }
    return minEval;
  }
}
```

### Move ordering for better pruning

Alpha-beta pruning is most effective when the best moves are evaluated first. Sort moves before searching:

1. Moves near the center of the board (tend to be stronger in most games)
2. Moves that are adjacent to existing pieces (more likely to be relevant)
3. Captures or forcing moves (if detectable cheaply)

Good move ordering can reduce search time by 10-100x at depth 4+.

---

## Difficulty Levels

### Standard difficulty scaling

| Difficulty | Search depth | Heuristic | Behavior |
|---|---|---|---|
| Easy | Depth 1 or random | Basic or none | Should lose to a player who is trying. Exists for beginners to learn. |
| Medium | Depth 2-3 | Standard heuristic | Should beat naive strategies (straight line, random, greedy). Should feel like a fair opponent. |
| Hard | Depth 3-4+ | Full heuristic | Should challenge experienced players. May use move ordering, iterative deepening. |

### Easy AI implementation

Two approaches for easy:
1. **Random**: Pick a random valid move. Simplest, but can feel arbitrary.
2. **Depth 1 with noise**: Evaluate each move but add random noise to scores. Plays somewhat sensibly but makes mistakes.

```javascript
function getEasyMove(state) {
  const moves = getValidMoves(state);
  // Option 1: pure random
  return moves[Math.floor(Math.random() * moves.length)];

  // Option 2: depth-1 with noise
  const scored = moves.map(m => ({
    move: m,
    score: evaluate(applyMove(state, m)) + (Math.random() - 0.5) * 50
  }));
  scored.sort((a, b) => b.score - a.score);
  return scored[0].move;
}
```

### Depth guidelines by game

- **Small boards (5x5 Santorini, 4x4 Tak)**: Depth 4-6 is feasible for hard
- **Medium boards (11x11 Hex, 6x6 YINSH)**: Depth 3-4 for hard
- **Large boards (19x19 Pente/Go)**: Depth 2-3 for hard; consider narrowing the move set

If hard AI takes more than 3 seconds per move, reduce depth or add move pruning (only consider the top N moves by quick evaluation).

---

## Heuristic Design

The heuristic function is the most important part of the AI. It assigns a numeric score to a game state from one player's perspective. Higher = better for the maximizing player.

### Score components

1. **Material/piece advantage**: Count of pieces, captures, or controlled territory
2. **Positional value**: Bonus for center control, edge proximity (connection games), or strategic squares
3. **Mobility**: Number of available moves (more options = better position)
4. **Threat detection**: Bonus for creating threats (near-wins), penalty for opponent threats
5. **Win/loss detection**: Return +/- Infinity for terminal states

### Score delta pattern

The heuristic should return the score difference between the two players:

```javascript
function evaluate(state) {
  const myScore = scoreFor(state, 'maximizing');
  const oppScore = scoreFor(state, 'minimizing');
  return myScore - oppScore;
}
```

This naturally handles both offensive and defensive play: the AI gains points for improving its own position and loses points when the opponent improves theirs.

### Common heuristic mistakes

- **Not weighting opponent threats**: The AI builds its own position but ignores the opponent's near-win. Fix: give opponent threats a high negative weight.
- **Over-weighting material in positional games**: In connection games (Hex, TwixT), raw stone count is meaningless. Score connectivity instead.
- **Linear heuristic for exponential threats**: A four-in-a-row in Pente is not 4x as dangerous as a one-in-a-row; it is a near-win. Use exponential or threshold-based scoring for alignment lengths.

---

## UI Integration

### AI turn trigger

After the human player completes their turn, trigger the AI with a `setTimeout` delay:

```javascript
useEffect(() => {
  if (gameState.currentPlayer === aiPlayer && !gameState.winner) {
    setIsAIThinking(true);
    setTimeout(() => {
      const move = getAIMove(gameState, aiPlayer, difficulty);
      const newState = applyMove(gameState, move);
      setGameState(newState);
      setIsAIThinking(false);
    }, 300); // small delay so the human's move renders first
  }
}, [gameState.currentPlayer]);
```

The 300ms delay ensures the human player sees their own move on the board before the AI responds. Without it, both moves appear to happen simultaneously.

### "Thinking..." indicator

Show a visual indicator while the AI is computing:

```jsx
{isAIThinking && <div className="ai-thinking">Thinking...</div>}
```

Disable all drag targets and click handlers during the AI's turn to prevent the human from playing out of turn.

### useRef for scores in async callbacks

If the AI callback reads score or state values, use `useRef` to avoid stale closures:

```javascript
const scoresRef = useRef(scores);
scoresRef.current = scores;

// Inside the AI setTimeout callback:
const currentScores = scoresRef.current; // always fresh
```

This is especially important when the AI turn involves multiple async steps (e.g., setup phase).

### Setup phase AI

For games with a setup phase (placing initial pieces before the main game), the AI setup trigger depends on the human completing setup first:

```javascript
useEffect(() => {
  if (p1SetupDone && !p2SetupDone && isAIGame) {
    // Trigger AI setup
    const positions = getAISetupPositions(gameState, difficulty);
    applySetup(positions);
  }
}, [p1SetupDone]);
```

Use `p1SetupDone` as the trigger, not `isSetupComplete` (which fires after both players are done).

---

## Testing the AI

After implementing, verify with the `ai-verification` skill:

1. Run naive strategies against each difficulty level
2. Easy should lose to a trying player
3. Medium should beat all naive strategies (straight line, random, greedy)
4. Hard should be strictly stronger than medium

See `skills/ai-verification/SKILL.md` for the full test protocol and game-specific naive strategies.
