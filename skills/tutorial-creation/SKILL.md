---
name: tutorial-creation
description: Pipeline for converting a strategy book (PDF or text) into structured interactive tutorial content for an abstract strategy game. Use this skill when given a strategy book and asked to create tutorial lessons, strategy guides, or interactive puzzles for a game. Also trigger when the user says "strategy guide", "make a tutorial from this book", "convert PDF to tutorial", "strategy section", or "teach strategy" for a game.
---

# Strategy Book → Interactive Tutorial Pipeline

This skill converts a strategy or tactics book into structured, interactive tutorial content for a board game implementation. The output is a JSON tutorial tier ("strategy") that can be loaded by TutorialMode.

**The central principle:** A tutorial based on a book is NOT a transcription. It is a distillation. The book's job is to explain; the tutorial's job is to create *insight through play*. Every section should answer: "What does the player need to *do* to feel this concept click?"

**Meta-learning:** After running this pipeline for a game, update `meta-learning.md` in this directory with: what OCR/extraction approach worked, which concept-map structure fit the game, which puzzle types worked best, and any game-specific gotchas. These notes improve future runs.

---

## Phase 0: Extract Raw Text

Before any analysis, the book's text must be in a readable form.

**Step 1: Identify PDF type.**
Run `pdfinfo <file.pdf>` and check the Producer field:
- If Producer = `LaTeX`, `Adobe`, `LibreOffice` → digital PDF; use `pdftotext`
- If Producer = `CamScanner`, `iOS`, `Android` → scanned image PDF; must use OCR

**Step 2a: Digital PDF.**
```bash
pdftotext <file.pdf> <output.txt>
```
Check output for blank lines — if empty, the PDF is actually scanned (some lie). Fall back to OCR.

**Step 2b: Scanned PDF (OCR required).**
```bash
# Convert pages to images at 300 DPI (high enough for tesseract)
pdftoppm -r 300 <file.pdf> /tmp/<game>_page

# Convert to PNG if tesseract won't read PPM
PYENV_VERSION=3.12.2 python3 -c "
from PIL import Image
import glob
for f in sorted(glob.glob('/tmp/<game>_page-*.ppm')):
    Image.open(f).save(f.replace('.ppm', '.png'))
"

# OCR each page, write to single text file
for f in $(ls ~/Desktop/ocr_tmp/*.png | sort); do
  tesseract "$f" stdout 2>/dev/null
  echo '---PAGE_BREAK---'
done > /tmp/<game>-ocr.txt
```

Note: tesseract may fail on `/tmp/` on macOS due to sandboxing. Copy images to `~/Desktop/ocr_tmp/` first.

**Step 3: Assess OCR quality.** Read the first 500 characters of the output. Expect:
- Printed prose → very clean (≥95% accuracy)
- Board diagram images → garbled or empty (not recoverable via OCR; use prose descriptions instead)
- Move notation tables → largely preserved, but digit/letter substitutions common (`l` for `1`, `0` for `O`)

Write raw OCR output to: `resources/<game>/strategy/raw-ocr.txt`

---

## Phase 1: Concept Map — REQUIRED BEFORE ALL OTHER PHASES

**This phase is mandatory and must be completed before designing any lessons, puzzles, or JSON.**

A concept map is the structural foundation of the tutorial. Without it, you risk teaching concepts out of order, missing prerequisite knowledge, or building puzzles that assume understanding the player doesn't yet have.

### What to extract from the book

Read through the full OCR text and identify:

1. **Document structure:** What is the table of contents? How are chapters and sections organized? Which sections are worth teaching vs. skip?

2. **Notation system:** How does the book describe moves and positions? What coordinate system? How are captures, threats, and key positions annotated? Document this — you will need it to translate book positions into tutorial puzzle coordinates.

3. **Concept inventory:** List every named concept in the book. For each one, write a one-sentence definition. Do not assume you know what terms mean — some game-specific terms have unintuitive meanings.

4. **Dependency graph:** For each concept, identify which other concepts must be understood first. This is the prerequisite chain. Some concepts are foundational (can be taught with no prior knowledge); some are intermediate (require 2-3 foundational concepts); some are advanced (require the full intermediate layer).

### Concept map format

Write the concept map to: `resources/<game>/strategy/concept-map.md`

The file must contain:
- **Formation/piece hierarchy** (if applicable): visual tree from weakest to strongest configuration
- **Complex structure taxonomy** (if applicable): how simple elements combine
- **Tactical concept layer**: concepts that depend on structural knowledge
- **Dependency graph**: explicit prerequisite arrows between concepts
- **Tutorial design recommendations**: which concepts belong in which tier, and which to skip
- **Notation translation guide**: how to convert book coordinates/notation to the game's actual board representation

### Red flags that require revising the concept map before continuing

- A lesson whose core concept has an unmet prerequisite in an earlier lesson
- A puzzle that requires understanding three concepts simultaneously (split into two puzzles)
- A concept with no clear "aha moment" that can be embodied in a board position (candidate for skipping or merging)

---

## Phase 2: Tier Design

With the concept map complete, design the tutorial tiers. A "tier" is a named learning track that a player selects. Each tier has 4–8 lessons. Each lesson has 3–6 steps (mix of explanation + interactive puzzle).

### Standard tier structure

| Tier | Target player | Focus |
|------|--------------|-------|
| Foundations | Complete beginner | Core vocabulary: what's good vs. bad, and why. The #1 most important insight about this game. |
| Structure | Intermediate | Multi-dimensional patterns, formation taxonomy, how things combine and escalate |
| Tactics | Advanced | Initiative, forcing moves, attack patterns, endgame techniques |

### Rules for tier design

1. **Foundations must be self-contained.** A player who only does Foundations should leave with one clear, actionable insight they can apply immediately.
2. **Each tier must build on the previous one.** Do not introduce a concept in Tactics that was not touched in Structure.
3. **Order lessons by dependency, not by book chapter order.** Books are written linearly; tutorial dependency graphs often are not.
4. **Merge thin concepts.** If two related concepts each only merit one puzzle, combine them into one lesson.
5. **Skip rare or edge-case content.** Only include concepts that appear in most games at intermediate+ level.

Write tier outlines to: `resources/<game>/strategy/tier-design.md`

---

## Phase 3: Puzzle Design

Each lesson needs 1–3 interactive puzzles. A puzzle is a board position where the player must find the correct move (or sequence of moves).

### Puzzle sourcing

In order of preference:
1. **Annotated game positions from the book** — the book already argues why the move is correct; use that as the explanation
2. **Constructed minimal positions** — strip everything away except the concept being taught; minimum pieces needed to make the point
3. **Problem sets from the book** — explicitly marked exercises; often the best teaching material

### Puzzle quality checklist

- [ ] The correct answer is unambiguous (one best move, or a small set of equivalent moves)
- [ ] The position can be set up using the game's actual board (no illegal placements)
- [ ] The position looks like it could arise in a real game (not purely artificial)
- [ ] The explanation of *why* the answer is correct teaches the concept, not just the position
- [ ] The puzzle is solvable in 1–2 minutes by the target tier's audience
- [ ] For "win in N" puzzles: verify the forced line is actually forced (no opponent escape)

### Puzzle coordinate translation

Translate book positions to game board coordinates using the notation guide from the concept map. Verify each position by:
1. Constructing it mentally (or on a physical board) using book move sequences
2. Checking that piece counts match (no extra pieces from annotations or diagram artifacts)
3. Confirming the "correct move" is actually available in the constructed position

Document the translation for each puzzle in a comment block in the JSON.

---

## Phase 4: JSON Output

Write the strategy tier to the game's tutorial JSON file at: `public/tutorials/<game-id>.json`

### JSON schema

```json
{
  "gameId": "<game-id>",
  "tiers": [
    {
      "id": "foundations",
      "label": "Foundations",
      "lessons": [
        {
          "id": "lesson-id",
          "title": "Lesson Title",
          "steps": [
            {
              "type": "info",
              "text": "Explanation text. Keep to 2–4 sentences. One concept per step."
            },
            {
              "type": "puzzle",
              "text": "Instruction for what the player should do.",
              "board": { /* game-specific initial board state */ },
              "correctMoves": ["move1", "move2"],
              "explanation": "Why this move is correct. Ties back to the concept."
            }
          ]
        }
      ]
    }
  ]
}
```

### Writing standards for tutorial text

- **Info steps:** 2–4 sentences. One concept per step. State the principle, then give one concrete example of what it looks like. No jargon without definition.
- **Puzzle instructions:** Tell the player *what to look for*, not *what to do*. "Find the move that creates two threats at once" is better than "Play C5."
- **Explanations:** Explain *why*, not *what*. "This works because the opponent cannot block both threats on the next move" is better than "C5 creates a Tessera."

---

## Phase 5: Verification

Before shipping the tutorial tier:

1. **Run the tactics verification script** (for games that have one):
   ```bash
   cd /path/to/abstracts/portal
   node scripts/verify-tactics.mjs
   ```
   This checks that every correctMove produces the expected outcome when run through the game engine, and scans for alternate solutions. Fix all failures before proceeding.

2. **Step through every lesson manually** in the game's TutorialMode UI.
3. **Verify every puzzle is solvable**: the `correctMoves` point to empty cells on the constructed board, and the move results in the position the explanation describes.
4. **Check for alternate solutions**: For each puzzle, mentally scan empty cells near the correctMove. If another cell also produces a win/capture/fork, either add it to correctMoves or add an opponent stone to block it. The verification script automates this for Pente and Hex.
5. **Read the tier end-to-end as a learner**: does each lesson assume only what came before it? Is the pacing right?
6. **Check mobile**: open the tutorial on a 390px-wide viewport and verify no text overflow, no button overlap with FAB.
7. **Search for em dashes**: grep for — (—) and -- in all user-visible strings. Replace with commas, periods, or parentheses per the writing style guide.

See also: `tactics-creation/SKILL.md` for puzzle design patterns, and `tactics-verification/SKILL.md` for details on the verification script.

---

## Phase 6: Meta-Learning Update

After completing the strategy tutorial for a game, update `meta-learning.md` in this directory with:

- **What OCR approach worked** (digital PDF vs. scanned, resolution, tools)
- **How the concept map was structured** for this game (was the Formation → Structure → Tactics pattern right, or did the game need a different shape?)
- **Which puzzle types were most effective** (constructed positions vs. book positions vs. endgame puzzles)
- **What was skipped and why** (so future agents know what sections of similar books to skip)
- **Any game-specific gotchas** in coordinate translation or board representation

---

## Quick Reference: Phase Order

```
Phase 0: Extract raw text (OCR if scanned)
    ↓
Phase 1: CONCEPT MAP — mandatory before anything else
    ↓
Phase 2: Tier design (map concepts to lessons, order by dependency)
    ↓
Phase 3: Puzzle design (source, construct, translate, verify)
    ↓
Phase 4: JSON output (write to public/tutorials/<game>.json)
    ↓
Phase 5: Verification (step through UI, check mobile)
    ↓
Phase 6: Meta-learning update
```

**Never skip Phase 1.** The concept map is the single artifact that prevents all downstream errors. If you are tempted to skip it because the book seems straightforward, that is exactly when it matters most — simple-seeming books often have implicit prerequisite chains that are invisible until you make them explicit.
