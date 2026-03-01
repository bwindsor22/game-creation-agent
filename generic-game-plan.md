# Generic Game Implementation Plan

A template for implementing turn-based board games as single-page browser applications. When starting a new game, combine this plan with the specific game's rulebook to produce a game-specific implementation plan, review it with the user, then execute it phase by phase.

## Constraints (apply to all games)

- Pure JavaScript — no server, no backend, no WebSockets
- All state lives in the browser; nothing persists after a page reload
- Single-player or local multiplayer only (no networked multiplayer)
- Loadable by opening an HTML file or a local dev server; no build step required to play
- Use React + react-dnd for interactive pieces unless the game rules make a simpler approach clearly better

---

## Phases

Execute phases in order. After each phase: build the project, take a screenshot, show it to the user, and wait for explicit approval before continuing to the next phase.

---

### Phase 1 — Game Pieces

**Goal:** All piece types are visually represented and distinguishable.

- Identify every piece type from the rulebook (tokens, tiles, cards, dice, markers, etc.)
- Render each piece as a styled HTML element or inline SVG — avoid external image dependencies where possible
- Pieces must be clearly distinct at a glance: use shape, color, size, and/or label
- Define the piece data model: type, owner, state (face-up/down, value, etc.)
- Pieces do not need to be interactive yet

**Review checkpoint:** Screenshot showing all piece types rendered side by side. Confirm visual design before proceeding.

---

### Phase 2 — Game Board

**Goal:** The board is laid out correctly and matches the rulebook diagram.

- Implement the board structure (grid, hex grid, track, irregular zones, etc.)
- Board spaces are rendered and correctly positioned
- Spaces are labeled or colored according to the rules
- Board is responsive within a reasonable range (768px–1400px wide)
- Pieces can be placed on the board statically (hard-coded for review)

**Review checkpoint:** Screenshot of the board with sample pieces placed. Confirm layout matches the rulebook before proceeding.

---

### Phase 3 — Game Logic

**Goal:** All core rules are enforced; the game can be played to completion.

Implement in this sub-order, confirming each works before the next:

1. **Initial setup** — board and piece starting positions per the rules
2. **Valid move calculation** — which moves are legal from any given state
3. **Move execution** — apply a move and transition to the next state
4. **Turn management** — whose turn it is, turn order, any special turn rules
5. **Win / loss / draw conditions** — detect end of game and display result
6. **Score tracking** — if the game has scoring, show live totals

### Common patterns (apply when the rulebook requires them)

**Setup phase** — Many Euro games have distinct setup rules before normal play begins (e.g. "place 2 starting pieces on the outer ring only"). Model this as a separate flag (`setupComplete: bool`). During setup, `canMove` enforces setup-specific restrictions; once setup is done, normal rules apply. Track progress with a counter (`setupPiecesPlaced`) compared to a constant (`SETUP_PIECES_NEEDED`).

**Activated spaces per turn** — When the rulebook says "you may not act on the same space twice in one turn" (common in Euro games for planting/growing/harvesting), track a `Set` of activated coordinates. Add to it on every board action; clear it when the turn advances. Check it at the start of every `canMove` call for board targets.

**Newly placed pieces are inert** — Pieces placed this turn should not count as sources for further actions in the same turn. Since newly placed pieces are already in `activatedSquares`, excluding activated squares from any "find a nearby source" check implements this rule automatically.

**Diminishing score piles** — Many Euro games award more points for early harvests from central locations. Model as an array of piles indexed by board zone (e.g. ring 0 = center = most valuable). Each harvest `shift()`s the top token from the matching pile, falling back to the next (less valuable) pile if that pile is empty. Initialize piles from a constant and keep them in module-level state alongside the board.

**"N rounds" end condition with bonus scoring** — When the game ends after a fixed number of rounds, compute the final score as `scoringTokens + floor(resources / divisor)`. Track revolutions/rounds as a counter incremented when the sun/phase marker wraps. Set `isGameOver = true` when the counter reaches the limit; disable the advance-turn button; display the score breakdown prominently.

**Free setup placement** — Many games have free initial placement (no resource cost). In `canMovePiece`, check the setup condition BEFORE the resource/LP cost check so that 0-LP players can still place their starting pieces. In `movePiece`, gate any cost deduction on `setupDone`: `const cost = setupDone ? movementCosts[type] : 0`. Same pattern in `getDropHint` — skip the "need N LP" error during setup so players see valid drop targets.

Drag-and-drop is the primary interaction for placing/moving pieces. Use `simulate_drag` to test key interactions after implementation.

**Review checkpoint:** Screenshot mid-game with a few moves made. Confirm pieces move correctly and illegal moves are blocked.

---

### Phase 4 — Instructions Panel

**Goal:** A side panel tells the player what to do at every point in the game.

- Persistent panel visible alongside the board (not a modal)
- Content updates dynamically based on game phase and whose turn it is
- Covers: setup instructions, each player's turn options, what happens on special events, end-game summary
- Keep text concise — one or two sentences per state

**Review checkpoint:** Screenshot showing the panel in at least two different game states (e.g. setup vs. mid-game). Confirm the text is accurate and readable.

---

### Phase 5 — Reset Button

**Goal:** One click returns the game to its initial state.

- Button is always visible and clearly labeled
- Resets all game state: board, pieces, scores, turn counter, instructions panel
- Does not require a page reload

**Review checkpoint:** Confirm reset works correctly after a few moves have been made.

---

### Phase 6 — Sandbox Mode

**Goal:** A toggle that lets the player move any piece anywhere, bypassing all rules.

- Clearly labeled toggle (e.g. "Sandbox Mode" switch)
- When active: all pieces are draggable to any valid space; no move validation; no turn enforcement
- When inactive: normal rules apply and game state is unchanged from before sandbox was entered
- Useful for exploring positions and testing piece layouts

**Review checkpoint:** Screenshot with sandbox mode active, pieces rearranged freely.

---

### Phase 7 — Adversarial AI

**Goal:** The player can choose to play against a computer opponent.

- Place AI code in `src/AI/ai.js` (NOT inside `src/view/`) — keeps AI separate from rendering
- Use greedy search with lookahead depth (depth 1 = greedy, depth 2–3 = lookahead) rather than full minimax; this is faster and sufficient for most Euro games
- Expose `easy` / `medium` / `hard` difficulty levels; map to depths 1/2/3 or top-N random vs. best
- Define a heuristic evaluation function using: score delta, resource delta, board position weights (central squares > edge)
- Use a pure functional `applyMove(state, move)` that snapshots state without mutating module state — essential for lookahead
- AI takes its turn automatically after the human player ends their turn, with a brief `setTimeout` delay for visual feedback
- Show a "thinking…" indicator in the UI; disable all drag targets while AI is computing
- AI plays one side only; human always goes first unless the rules specify otherwise
- Track LP / scores via `useRef` to avoid stale closures in async AI callbacks
- The setup useEffect (AI places starting pieces) must depend on `p1SetupDone` state, not `isSetupComplete` — `isSetupComplete` is only true when BOTH players have placed, so it never fires the AI trigger in time

**Startup screen pattern:**
- Show a startup screen (separate component) before the game mounts the `GameProvider`
- Startup screen collects: player color, number of AI opponents, difficulty
- Pass selections as props to `GameProvider` (e.g. `initialColor`, `initialDifficulty`)
- Player color: apply a CSS `filter` (hue-rotate) to piece images; export a `COLOR_FILTERS` map from GameContext for consistency across components
- Lock difficulty selector after setup completes (can't change mid-game)

**Initial photosynthesis:**
- Run photosynthesis at sun position 0 AFTER setup completes (not before)
- This gives players their first LP from their starting trees, per the rulebook
- Trigger it inside the AI setup useEffect, after AI places its trees

**Review checkpoint:** Play several moves against the AI. Confirm it makes legal moves and provides reasonable (not obviously losing) play.

---

## Feedback loop protocol

After each phase is built and the screenshot is reviewed:

1. Present the screenshot and a brief summary of what was implemented
2. List any known gaps or deferred items
3. Ask the user: "Does this look correct? Any changes before I continue to Phase N?"
4. Do not proceed until the user gives explicit approval or requests changes
5. If changes are requested, implement them and re-verify before moving on

---

## Game-specific planning step

Before beginning Phase 1, produce a **game-specific implementation plan** by adapting this template to the target game:

- Identify all piece types and their visual representation approach
- Describe the board type and layout strategy
- List every rule that affects valid moves
- Define the win condition(s) and scoring method
- Note any phases that don't apply (e.g. some games have no scoring) or need extra sub-phases
- Estimate complexity of the AI heuristic

Present this adapted plan to the user and get approval before writing any code.
