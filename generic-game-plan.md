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

- Implement minimax with alpha-beta pruning
- Define a heuristic evaluation function for non-terminal states (derived from the rulebook's scoring/advantage criteria)
- AI difficulty: start with depth 3; make depth configurable if performance allows
- AI takes its turn automatically after the human player's move
- Show a brief "thinking…" indicator while AI computes
- AI plays one side only; human always goes first unless the rules specify otherwise

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
