# Strategy Tutorial Pipeline — Meta-Learning Log

This file records learnings from each run of the tutorial-creation skill. Future agents should read this before starting a new game's strategy tutorial.

---

## Run 1: Pente (stones game) — 2026-03-28

**Source:** Tom Braunlich, *Pente Strategy* (1979 World Champion)
**PDFs:** `resources/pairs/pente-strategy-part-1.pdf` (25 pages), `pente-strategy-part-2.pdf` (22 pages)
**Concept map:** `resources/pairs/strategy/concept-map.md` (in game-creation-agent)
**OCR output:** `/tmp/pente-part1-ocr.txt`, `/tmp/pente-part2-ocr.txt`

### OCR approach

- Both PDFs are **scanned image PDFs** (Producer: CamScanner/iOS). `pdftotext` returned empty output.
- Used `pdftoppm -r 300` to convert to PPM images, then Pillow (pyenv 3.12) to convert to PNG.
- Tesseract refused to run on `/tmp/` (macOS sandbox). Moved images to `~/Desktop/pente_ocr_tmp/`.
- OCR quality: excellent for prose and move notation; board diagram images are completely unreadable (noise).
- 300 DPI is the right resolution — higher wastes time, lower loses legibility on small text.

### PDF coverage gap

The two PDFs cover Introduction + Chapter I (Structure) + Chapter II (Tactics), ending at book page 48. Chapter III (Multi-Player Games) and both Appendices are missing. This is fine for tutorial purposes — Chapter III is out of scope (two-player game only) and the Appendices are supplementary.

### Concept map structure

The Formation → Structure → Tactics pattern fit Pente perfectly:
- **Formations** (hierarchy from Pair/Potential up to Pente): clean linear dependency chain
- **Complex structures** (L/V/T/Cross/Wing/Dread X/Horrible H): branched taxonomy with a key insight (diagonal = strong)
- **Tactics** (Initiative → Double Threat → Attacking Weaknesses → Endgame): depends on full structural knowledge

The **Potential vs. Pair** insight is the foundational axis of the entire game. Every other concept is downstream from understanding why adjacent stones are weak and diagonal stones are strong. This should be Lesson 2 of Foundations (after win conditions).

### Concept map: what to skip

| Skipped concept | Reason |
|----------------|--------|
| Stretch Two / Knight-Jump Two | Author says nearly useless; rarely arises |
| Stretch Four / Flex Four | Very rare formations; advanced edge cases |
| Irregular Threes A–D taxonomy | Academic classification; teach as "not all threes equal" |
| Multi-Player Games (Ch. III) | Out of scope for two-player implementation |
| Exchange (trading captures) | Nuanced endgame; optional only |

### Notation translation

Pente book uses centered `(X,Y)` with `(0,0)` at board center intersection.
Our stones game likely uses 0-indexed row/col from top-left on a 19×19 board.
Conversion: `col = X + 9`, `row = 9 - Y`
Example: book `(3,2)` → col=12, row=7 → board position `[7][12]`
Captures noted with asterisks: `*-1,0*` = capture at (-1,0).

### Puzzle sourcing

The book contains 4 fully annotated tournament games with move-by-move commentary — these are the richest puzzle source. Key games:
- Braunlich-McAuliff (Qualifying Tournament 1979) — tactical endgame, Keystone attack
- Krenz-Braunlich (Qualifying Tournament 1979) — structural evaluation in practice
- Braunlich-Means (1980 off-hand game) — initiative and forcing moves
- Braunlich-Gabrel (Wichita 1980) — opening structure development

Board figures are images (not recoverable via OCR) — construct positions from the move sequences in the prose instead.

### What worked well

- Reading the full OCR text before designing any lessons revealed several non-obvious concept dependencies (e.g., Radiance must come before Danger Zone, and both must come before Keystone)
- The concept map's "dependency graph" section is the highest-value artifact — refer back to it constantly during lesson ordering

### What to do differently next time

- Run OCR on all pages first, then read the full output before beginning concept map (do not read page-by-page)
- For books with figure-heavy chapters, explicitly note in the concept map which figures are unreproducible and ensure the prose surrounding them is sufficient
- Check whether the game's tutorial JSON already has `foundations` or other tiers before writing -- avoid overwriting existing content

---

## Run 2: Hex (hexes game) -- 2026-03-29

**Source:** Cameron Browne, *Hex Strategy: Making the Right Connections* (2000)
**Concept map:** `skills/strategy-pipeline/concept-map-hex.md`
**Extracted text:** `resources/hexes/hex-strategy-extracted.txt`

### Source material

- Book is a digital PDF (clean text extraction, no OCR needed).
- 13 chapters covering adjacency through advanced ladder tactics and opening play.
- Extensive board diagrams referenced by figure numbers (not reproducible from text alone, but prose descriptions are sufficient for tutorial construction).

### Concept map structure

The hierarchy for Hex is deeper than Pente's:
- **Adjacency → Chains → Connectivity → Bridges** forms a clean linear foundation
- **Bridges → Templates (Interior + Edge) → Template Intrusions → Forcing Moves** is the structural backbone
- **Ladders → Ladder Escapes → Escape Forks → Escape Foils** is a complex tactical subtree
- The concept map has 3 tiers with 10, 14, and 17 concepts respectively

The **two-bridge** is the foundational tactical unit of Hex (equivalent to Pente's "Potential vs Pair" insight). Every other concept builds on understanding why two shared empty neighbors between two groups makes the connection safe.

### Tactics puzzle design learnings

1. **Two-bridge is the building block**: All hex tactics puzzles beyond "win in one" rely on the two-bridge pattern. Teach it first as an explain step before any puzzles.

2. **"Forced Win in Three" design**: Build a chain from one edge to the other with exactly 3 gaps. Make 1 gap forced (single bridge cell) and 2 gaps two-bridges. The correct first move is always the forced gap. This pattern is hard to construct correctly -- verify neighbor adjacency for every gap.

3. **Alternate solution scanning is critical for Hex**: Because Hex has no captures or complex mechanics, any empty cell that completes a path is a valid win. The alternate-solution scanner in `verify-tactics.mjs` catches these. Run it after every puzzle edit.

4. **Blue stones as blockers**: Place Blue stones at one of the two bridge cells in a two-bridge to reduce it to a forced (single-bridge) gap. This creates puzzle variety without changing the fundamental pattern.

5. **Hex neighbor formula**: `[[-1,0], [-1,1], [0,-1], [0,1], [1,-1], [1,0]]`. Easy to get wrong. When constructing a gap between rows R and R+2, the bridge cells are at `[R+1, col]` and `[R+1, col+1]` (or `[R+1, col-1]` depending on direction). Always verify by checking both cells are neighbors of both sides of the gap.

### What to do differently next time

- Hex concept map is very deep (ladders alone have 6+ sub-concepts). Consider splitting Tier 3 into two sub-tiers (Tactics: Ladders, Tactics: Advanced) or pruning aggressively.
- The Browne book has excellent annotated game positions. Prioritize those over constructed minimal positions for the Structure and Tactics tiers.
- Board figures in the book are essential for some concepts (especially template shapes). Without OCR-recoverable diagrams, cross-reference the prose descriptions carefully and construct positions from the textual move sequences.
