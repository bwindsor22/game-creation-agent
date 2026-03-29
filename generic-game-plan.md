# Generic Game Implementation Plan

A template for implementing turn-based board games as single-page browser applications. The pipeline has two stages: (1) gather game knowledge from YouTube videos, and (2) build the game.

## Stage 1 — YouTube Research Pipeline

Before writing any code, gather game knowledge using the YouTube pipeline.

### 1a. Run the pipeline

```bash
PYENV_VERSION=3.12.2 python3 tools/youtube_pipeline.py \
  'https://www.youtube.com/watch?v=VIDEO1' \
  'https://www.youtube.com/watch?v=VIDEO2' \
  --output /path/to/game/resources/youtube \
  --game "GameName"
```

Video URLs live in `resources/how-to-play.md`. Each video produces:
- `<video_id>/transcript.md` — full timestamped transcript
- `<video_id>/frames/` — JPEG frames at 30s intervals
- `<video_id>/frames.json` — frame timestamps + vision captions

### 1b. Write guidelines.md

Read the transcripts and key frames, then synthesize a `guidelines.md` covering:
- Setup (board size, starting positions, piece counts)
- Turn structure (actions per turn, mandatory vs. optional)
- Valid moves (movement rules, placement rules, restrictions)
- Win condition (exact criteria)
- Key rules (captures, special moves, edge cases)
- Testing checklist (scenarios to verify during development)

Write to both `<video_id>/guidelines.md` and a consolidated `resources/youtube/guidelines.md`.

### 1c. Review with user

Present the guidelines and confirm accuracy before coding. The user may have the physical game or rulebook to cross-reference.

---

## Stage 2 — Game Implementation

Execute phases in order. After each phase: build, screenshot, show to the user, and wait for approval.

### Constraints

- Pure JavaScript, no server, no backend
- All state lives in the browser; nothing persists after reload
- Single-player or local multiplayer only
- React + react-dnd for interactive pieces
- Game must work at 768px-1400px wide

---

### Phase 1 — Game Pieces

**Goal:** All piece types are visually represented and distinguishable.

- Identify every piece type from guidelines.md
- Render each as styled HTML or inline SVG (no external images)
- Pieces must be distinct at a glance: shape, color, size, label
- Define the piece data model: type, owner, state
- Pieces do not need to be interactive yet

**Checkpoint:** Screenshot showing all piece types rendered side by side.

---

### Phase 2 — Game Board

**Goal:** The board is laid out correctly per the guidelines.

- Implement the board structure (grid, hex grid, track, zones)
- Board spaces are rendered and correctly positioned
- Board is responsive (768px-1400px)
- Pieces can be placed on the board statically for review

**Checkpoint:** Screenshot of the board with sample pieces placed.

---

### Phase 3 — Game Logic

**Goal:** All core rules are enforced; the game can be played to completion.

Implement in order:

1. **Initial setup** — starting positions per the rules
2. **Valid move calculation** — which moves are legal from any state
3. **Move execution** — apply a move, transition to next state
4. **Turn management** — turn order, special turn rules
5. **Win / loss / draw detection** — end of game + display result
6. **Score tracking** — live totals if the game has scoring

### Common patterns

**Setup phase** — Model as `setupComplete: bool`. During setup, `canMove` enforces setup-specific restrictions. Track with `setupPiecesPlaced` vs. `SETUP_PIECES_NEEDED`.

**Activated spaces per turn** — Track a `Set` of coordinates acted on this turn. Clear on turn advance. Check at start of every `canMove` call.

**Diminishing score piles** — Array of piles indexed by board zone. Each harvest `shift()`s the top token, falling back to next pile if empty.

**Free setup placement** — Check setup condition BEFORE resource cost check in `canMovePiece`. Gate cost deduction on `setupDone`.

Drag-and-drop is the primary interaction. Use `simulate_drag` to test key interactions.

**Checkpoint:** Screenshot mid-game with moves made. Confirm rules are enforced.

---

### Phase 4 — Instructions Panel

**Goal:** A side panel tells the player what to do at every point.

- Persistent panel alongside the board (not a modal)
- Updates dynamically based on game phase and current turn
- Concise: one or two sentences per state

**Checkpoint:** Screenshot in at least two game states.

---

### Phase 5 — Reset and Start Screen

**Goal:** Clean game start and restart.

- Start screen collects: player color, number of AI opponents, difficulty
- Pass selections as props to the game component
- Reset button returns to initial state without page reload

**Checkpoint:** Confirm reset works after several moves.

---

### Phase 6 — AI

**Goal:** Computer opponent at three difficulty levels.

- Place AI code in `src/AI/ai.js`, separate from rendering
- Minimax with alpha-beta pruning; easy/medium/hard = depths 1-2/3-4/5+
- Define a heuristic evaluation function (score delta, position weights, mobility)
- Pure functional `applyMove(state, move)` for lookahead (no mutation)
- AI takes turn after human with brief delay; show "thinking..." indicator
- Disable all interaction while AI computes

See `skills/ai-creation/SKILL.md` for detailed patterns.

**Checkpoint:** Play several moves against AI. Confirm legal moves and reasonable play.

---

### Phase 7 — Tutorial

**Goal:** Interactive tutorial teaches the game rules.

- Create tutorial JSON in `portal/public/tutorials/<game-id>.json`
- Implement `renderTutorialBoard` in the game's App.js
- Wire up TutorialMode with learn/strategy/tactics tiers as appropriate

See `skills/tutorial-creation/SKILL.md` for the full pipeline.

**Checkpoint:** Step through all tutorial lessons. Verify puzzles with `node scripts/verify-tactics.mjs`.

---

## Feedback loop protocol

After each phase:

1. Present screenshot and brief summary
2. List known gaps or deferred items
3. Ask: "Does this look correct? Any changes before Phase N?"
4. Do not proceed without explicit approval

---

## Game-specific planning step

Before Phase 1, produce a **game-specific implementation plan** by adapting this template:

- All piece types and visual representation approach
- Board type and layout strategy
- Every rule affecting valid moves
- Win condition(s) and scoring method
- Phases that don't apply or need extra sub-phases
- AI heuristic complexity estimate

Present this plan and get approval before writing code.
