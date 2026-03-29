# Bug Fix Difficulty Rubric

Use this rubric to estimate fix difficulty for every bug found in a QA run. Include the difficulty level in every finding report.

---

## Levels

| Level | Label | Typical fix time | Description |
|---|---|---|---|
| 1 | Trivial | < 5 min | Single CSS property, one-liner, add missing attribute |
| 2 | Easy | 5-30 min | Small, localized change to one file; requires understanding of one component |
| 3 | Medium | 30 min - 2 hrs | Multiple files or requires understanding component state flow |
| 4 | Hard | 2-8 hrs | Architectural change, complex state machine, or requires a new component |
| 5 | Very Hard | 8+ hrs | Requires new system, deep game logic rewrite, or infrastructure changes |

---

## Calibrated Examples (from actual fixes)

| Bug | Level | Actual | Notes |
|---|---|---|---|
| Add `viewBox` + `maxWidth: 100%` to SVG | 1 | ~2 min | Always Level 1 regardless of game |
| Add `flexWrap: wrap` to legend div | 1 | ~1 min | Single property change |
| Reduce gap in difficulty chooser | 1 | ~1 min | Single value change |
| Add `padding-bottom: 80px` to tutorial panel | 1 | ~2 min | Single CSS rule in media query |
| Add horizontal scroll to board wrapper | 1 | ~3 min | Single CSS property |
| Replace broken tutorial puzzle in JSON | 2 | ~20 min | Requires understanding game rules and puzzle design |
| Add "Learn to Play" to in-game menu | 2 | ~10 min | Add button + wire to existing state |
| Add PromotionPicker modal (knights) | 3 | ~45 min | New component, state management, event flow |
| Fix pawn promotion move detection | 3 | ~30 min | Requires understanding engine move format |
| Walls AI pathfinding edge case | 4 | ~3 hrs | Complex game logic, requires proof of correctness |
| Asymmetric wall placement (left vs right edge) | 4 | ~2 hrs | Coordinate system bug, hard to reproduce |

---

## How to Use During QA

1. Identify the root cause (not just the symptom)
2. Look up similar bugs in the calibrated examples above
3. If no calibrated example, use the level descriptions and err on the side of higher difficulty
4. Mention the difficulty in the report so the user can prioritize

---

## Updating This Rubric

After completing a fix session, check if any bugs took significantly more or less time than estimated. Update the calibrated examples table with the actual time and a note explaining why.

If a class of bug is consistently under- or over-estimated, add a note in the relevant category file as well.
