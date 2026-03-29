---
name: tutorial-verification
description: Verifies that strategy tutorials are correct, complete, and functional. Checks puzzle solvability, text accuracy, mobile layout, and learning progression. Use after creating or editing tutorial content.
---

# Tutorial Verification

This skill validates strategy tutorials end-to-end: puzzle correctness, text quality, mobile layout, and learning progression. Run it after creating or editing any tutorial content.

---

## Issue Log (Known Failure Cases)

Historical bugs to check for on every verification pass:

- **Puzzle has no valid solution**: correctMoves point to an occupied cell, or the board state makes the intended move illegal. Most common when puzzle boards are hand-crafted from book diagrams.
- **Puzzle has unlisted alternate solutions**: An empty cell not in correctMoves also produces the expected outcome (win, capture, fork). The alternate-solution scanner catches these for Pente and Hex, but other games need manual checking.
- **Em dashes in user-facing text**: The writing style guide prohibits em dashes (--) and (---). They appear frequently when text is drafted quickly. Replace with commas, periods, or parentheses.
- **Tutorial text references concepts not yet introduced (dependency violation)**: A lesson mentions a term or pattern that is taught in a later lesson. This breaks the learning progression and confuses players who follow the intended order.
- **Board state doesn't match what the text describes**: The puzzle instruction says "Black has a tria on row 8" but the board JSON places stones on row 9. Caused by coordinate translation errors from book notation.
- **Mobile layout: text overflow, FAB overlap with tutorial nav buttons**: Long explanation text overflows its container on narrow viewports. The floating action button covers the Next/Previous step buttons at the bottom of the screen.
- **Info steps that are too long (>4 sentences) or use undefined jargon**: Info steps should be 2-4 sentences max. Each term must be defined before or during its first use. Jargon from the source book that wasn't introduced in an earlier step is a failure.
- **Tutorial text references internal coordinates not visible on the board**: Text says "Row 0" or "column 6" but the board UI has no row/column labels. Tutorial text must use player-visible descriptions (spatial terms like "top row," "corner," "left side") rather than array indices or internal coordinates.
- **Explain steps worded as imperatives, confused with puzzle steps**: Non-interactive explain/info steps that say "Place a disc..." or "Move your piece to..." read as calls to action, making players try to click. Explain steps must use descriptive language ("Black goes first by placing...") not imperative language ("Place a disc to...").
- **Tutorial board state shows illegal moves**: A tutorial step illustrating "after this move" must show a legal game state. If a piece is shown as placed, it must follow the game's placement rules (e.g., Othello requires sandwiching). Flipped/captured pieces must be updated in the board JSON.

---

## Programmatic Tests

Run these checks after every tutorial edit:

### 1. Puzzle solution verification

```bash
cd /path/to/abstracts/portal
node scripts/verify-tactics.mjs
```

This script:
- Loads each puzzle board state into the game engine
- Applies each correctMove via `applyMove()`
- Verifies the expected outcome (win, capture, fork, threat)
- Scans all empty cells for alternate solutions that produce the same outcome
- Exit code 0 = all pass, exit code 1 = failures found

Fix all failures before proceeding. Common fixes: add missing sandwich stones (Pente captures), correct hex neighbor coordinates, add blocker stones to eliminate alternate solutions.

### 2. Mobile layout walkthrough

Step through each lesson in a browser at 390px viewport width:

```python
# Take screenshot at mobile width
python3 -c "
import sys; sys.path.insert(0, '/Users/brad/projects/code/game-creation-agent')
from tools.screenshot_tool import take_screenshot
path = take_screenshot('http://localhost:3000/tutorial', output_path='/tmp/tutorial-mobile.png', viewport={'width': 390, 'height': 844})
print(path)
"
```

Check each step for:
- Text overflow outside the tutorial panel
- FAB button overlapping tutorial navigation (Next/Previous)
- Touch targets smaller than 44px
- Puzzle board clipping on left/right edges

### 3. Em dash and double hyphen scan

Search all tutorial JSON files for prohibited punctuation:

```bash
# Grep for em dashes and double hyphens in tutorial strings
grep -rn '[—]' portal/public/tutorials/*.json
grep -rn '\-\-' portal/public/tutorials/*.json
```

Replace any matches with commas, periods, or parentheses per the writing style guide.

### 4. Concept dependency ordering

Verify lesson ordering matches the concept map dependency graph:

1. Read the concept map at `resources/<game>/strategy/concept-map.md`
2. For each lesson, identify which concepts it teaches and which it assumes
3. Verify that every assumed concept was taught in a prior lesson within the same tier or a prerequisite tier
4. Flag any dependency violations (concept used before it is introduced)

This check is manual but critical. The most common failure is a Tactics tier lesson that assumes Structure-tier knowledge the player may not have if they skipped Structure.

---

## Integration with Other Skills

- **`tutorial-creation/`**: The creation pipeline (Phase 5) calls this verification skill. Read creation first, verify second.
- **`tactics-verification/`**: Covers the programmatic puzzle verification in detail. This skill adds the text quality and mobile layout checks on top.
- **`tactics-creation/`**: Puzzle design patterns. Consult when fixing puzzle failures.
- **`writing-style/`**: The style rules that govern all tutorial text. Check it when fixing em dashes or jargon issues.
