Start a new board game implementation. Combines the game's rulebook with the generic implementation plan to produce a game-specific plan, reviews it with the user, then builds the game phase by phase with a visual review after each phase.

Usage: /game-creation-agent:new-game [path-to-rulebook-pdf] [project-dir]

## Step 1 — Gather inputs

Parse $ARGUMENTS for:
- `rulebook_path`: path to the PDF rulebook
- `project_dir`: directory where the game will be built (create it if it doesn't exist)

If either is missing, ask the user before proceeding.

## Step 2 — Read the rulebook

Call `pdf_to_text(rulebook_path)` to extract the rules. If the PDF is long (>20 pages), read it in chunks using the `pages` argument. Focus on:
- All piece types and their properties
- Board structure and setup
- Valid moves and turn order
- Win/loss/draw conditions
- Scoring rules

## Step 3 — Read the generic plan

Read `generic-game-plan.md` from this plugin's directory. This is the template all games follow.

## Step 4 — Produce a game-specific implementation plan

Combine the rulebook content with the generic plan to write a game-specific plan. For each phase in the generic plan, specify:

- **Phase 1 (Pieces)**: List every piece type, its visual design approach (color, shape, label), and its data model fields
- **Phase 2 (Board)**: Board type (grid/hex/track/etc.), dimensions, space labels or colors, starting piece positions
- **Phase 3 (Logic)**: Every rule that governs valid moves; turn order; win conditions; scoring formula
- **Phase 4 (Instructions)**: What the panel should say in each distinct game state
- **Phase 5 (Reset)**: What "initial state" means for this game
- **Phase 6 (Sandbox)**: Any constraints on sandbox mode (e.g. some pieces can't be picked up at all)
- **Phase 7 (AI)**: Heuristic evaluation approach; what constitutes a "good" board position for this game

Note any generic phases that don't apply and any game-specific phases that need to be added.

## Step 5 — Review plan with user

Present the game-specific plan clearly. Ask: "Does this plan look correct before I start building?" Do not write any code until the user approves. Incorporate any requested changes.

## Step 6 — Implement phase by phase

For each phase (1 through 7):

1. Implement the phase in `project_dir`
2. Call `build_project(project_dir)` — fix any build errors before continuing
3. Call `start_dev_server(project_dir)`
4. Call `take_screenshot('http://localhost:3000', output_path='/tmp/phase-N.png')`
5. Call `ask_about_screenshot('/tmp/phase-N.png', <phase-specific question>)` to verify the implementation looks correct
6. Call `kill_dev_server(3000)`
7. Show the screenshot and your visual assessment to the user
8. Ask: "Does Phase N look correct? Any changes before I continue to Phase N+1?"
9. Do not proceed until the user explicitly approves

Phase-specific vision questions to ask:
- Phase 1: "Are all piece types visually distinct and clearly rendered? Do any look like unstyled default HTML?"
- Phase 2: "Does the board layout match a [grid/hex/track] structure? Are all spaces visible and correctly positioned?"
- Phase 3: "Are pieces positioned on the board? Does the layout suggest a mid-game state with valid piece placement?"
- Phase 4: "Is there a visible instruction panel alongside the board? Is the text readable?"
- Phase 5: "Is there a visible reset button? Is it clearly labeled?"
- Phase 6: "Is there a visible sandbox mode toggle? Is it clearly labeled?"
- Phase 7: "Does the UI indicate whose turn it is and that an AI opponent is present?"

## Constraints (remind yourself throughout)

- Pure JavaScript — no server, no backend, no persistent state after reload
- Single-page application loadable in a browser
- All interactivity via drag-and-drop using react-dnd HTML5Backend
- No external image dependencies unless the user provides assets
