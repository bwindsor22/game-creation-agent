---
name: pre-deploy-qa
description: Automated pre-deploy QA pipeline that catches UI, layout, and logic bugs before shipping. Also covers visual testing, screenshot verification, drag-and-drop interaction testing, and comparing renders to reference images. Use this skill whenever the user wants to test a website or web app before deploying, check for mobile responsiveness issues, find visual bugs, audit game logic or business rules, run screenshot-based regression testing, or do any kind of pre-push quality check on a web project. Also trigger when the user mentions "QA", "pre-deploy check", "visual regression", "mobile testing", "responsive testing", "bug audit", "screenshot testing", "visual testing", "drag-and-drop testing", or asks Claude to "find bugs" in a web app or site. This skill works for any HTML/JS/React project served locally or from static files.
---

# Pre-Deploy QA Pipeline

This skill runs a multi-layered QA audit on a web project before deployment. It catches three categories of bugs that are commonly missed in code review alone:

1. **Visual/Layout bugs** — elements offscreen, overlapping, clipped, or wrapping incorrectly at various viewport sizes (especially mobile)
2. **Logic/Rule bugs** — game rules, business logic, or constraint violations that don't match the spec
3. **Content/UX bugs** — mismatched labels, missing navigation paths, inconsistent theming

The key insight: most visual bugs are invisible in code review but obvious in screenshots. This skill combines Playwright screenshot capture with vision-based analysis and targeted code review.

**Sub-skills**: Each bug category below has a dedicated reference file in `categories/`. Read the relevant file before attempting a fix — it contains known fix patterns, failure cases, and difficulty estimates.

**Meta-learning**: After fixing a bug, update the relevant category file with the success pattern. After a regression, add a failure case note. See `meta-learning.md` for the full update protocol.

**Feature requests vs bugs**: Before reporting any finding, run it through `feature-request-detection.md`. Do not report feature requests as bugs.

---

## Prerequisites

Before running the pipeline, install Playwright and its browser dependencies. The skill handles this automatically, but if you need to do it manually:

```bash
npm install playwright
npx playwright install chromium
```

If the project uses a dev server (Vite, Next.js, etc.), start it before running the pipeline. For static HTML files, the skill will serve them with a local HTTP server.

---

## Pipeline Overview

The pipeline runs in three sequential phases. Each phase produces findings that feed into a final consolidated report.

### Phase 1: Screenshot Capture & Visual Audit

This is the highest-leverage phase. Most mobile UI bugs are immediately visible in screenshots but nearly impossible to catch from code alone.

**Step 1: Identify all distinct views/routes.**
Read the project source to enumerate every page, screen, modal, and state that a user can reach. For single-page apps, this means every route. For games, this means every screen (menu, tutorial, gameplay, settings, game over). List them explicitly before proceeding.

**Step 2: Serve the project locally.**
- If the project has a dev server command (check `package.json` scripts for `dev`, `start`, `serve`), use it
- For static HTML, run: `npx http-server . -p 8080 -c-1 --silent &`
- Wait for the server to be ready before continuing

**Step 3: Capture screenshots at multiple viewports.**
Use the Playwright script at `scripts/capture_screenshots.js` (read it before running). For each view identified in Step 1, capture at these breakpoints:

| Device class | Width × Height |
|---|---|
| Small phone | 375 × 667 |
| Large phone | 390 × 844 |
| Tablet portrait | 768 × 1024 |
| Desktop | 1440 × 900 |

Customize the script's `PAGES` array to match the views you identified. The script will output screenshots to `qa-output/screenshots/`.

**Step 4: Run the 14 Visual Bug Category Checks.**
For every screenshot, check all 14 categories below. Read the corresponding `categories/*.md` file for each check — it contains specific detection signals, known fix patterns, and difficulty estimates.

| # | Category | Category File | Viewport Focus |
|---|---|---|---|
| 1 | Mobile board overflow (left/right edge clipping) | `categories/mobile-board-overflow.md` | Mobile |
| 2 | FAB / fixed-button overlap with tutorial nav | `categories/fab-button-overlap.md` | Mobile |
| 3 | Touch target size < 44px | `categories/touch-target-size.md` | Mobile |
| 4 | Unwanted horizontal page scroll | `categories/horizontal-scroll.md` | Mobile |
| 5 | Difficulty chooser layout wrapping | `categories/difficulty-chooser-wrapping.md` | Mobile |
| 6 | Start screen scrolled to bottom on navigation | `categories/start-screen-scroll.md` | Mobile |
| 7 | Tutorial images / diagrams mismatch actual UI | `categories/tutorial-ui-mismatch.md` | All |
| 8 | Menu navigation gaps (feature only in one path) | `categories/menu-navigation-gaps.md` | All |
| 9 | SVG missing viewBox / non-responsive | `categories/svg-responsive.md` | Mobile |
| 10 | Tutorial puzzle has no valid solution | `categories/tutorial-puzzle-validity.md` | N/A (code) |
| 11 | Color/player legend not wrapping on narrow screens | `categories/legend-wrapping.md` | Mobile |
| 12 | Board too zoomed in or out on mobile initial view | `categories/mobile-zoom-level.md` | Mobile |
| 13 | Piece promotion auto-selects without player choice | `categories/promotion-ui.md` | All |
| 14 | Win overlay missing Elo or showing wrong values | `categories/win-overlay-display.md` | All |

Report each finding with: category number, view name, viewport size, what's wrong, and which element is affected.

### Phase 2: Logic & Rule Audit

This phase catches bugs where the code doesn't match the intended behavior. It requires the user to provide a specification — game rules, business requirements, or a description of expected behavior.

**Step 1: Get the spec.**
Ask the user for the rules, requirements, or intended behavior. If they have a rules document, tutorial text, or requirements doc, ask them to provide it. If the project has inline documentation or tutorial content, extract it from the source code.

**Step 2: Enumerate testable rules.**
From the spec, create an explicit checklist of verifiable rules. For example:
- "Pawns reaching the last rank must offer a promotion choice (queen, rook, bishop, knight)"
- "After every wall placement, a valid path must exist from each player to their goal"
- "Pieces rotated by 90 degrees must still snap to valid board positions"

**Step 3: Trace each rule through the code.**
For every rule in the checklist, find the code that implements it and verify:
- Does the implementation handle all cases described in the spec?
- Are there edge cases the code misses?
- Are there unreachable code paths or dead conditions?
- Does the code fail open (allowing invalid states) or fail closed?

**Step 4: Generate targeted tests.**
For rules involving constraints or invariants (like pathfinding, valid placements, or score calculations), generate property-based test suggestions. These are assertions that should hold true after every action:

```javascript
// Example: after every wall placement, both players must have a valid path
afterEach(() => {
  expect(hasValidPath(player1.position, player1.goal, board)).toBe(true);
  expect(hasValidPath(player2.position, player2.goal, board)).toBe(true);
});
```

Write these to `qa-output/suggested-tests/`.

### Phase 3: Content & UX Consistency

This phase catches mismatches between what the user sees and what the app actually does.

**Step 1: Audit navigation paths.**
From the screenshots and source, map every way a user can reach help content, tutorials, settings, and key features. Flag any content that's accessible from one path but not another where users would expect it (e.g., a strategy guide available from the start screen but not from the in-game menu).

**Step 2: Check visual consistency.**
Compare tutorial/help content against actual game/app visuals. Flag cases where screenshots, diagrams, or descriptions in tutorials don't match the current UI.

**Step 3: Check interactive element accessibility on mobile.**
From the mobile screenshots, verify that all primary actions are reachable without scrolling to unexpected places, and that the most important action on each screen is visually prominent.

---

## Visual Testing Workflows

### Screenshot workflow

Always follow this sequence to avoid orphaned server processes:

```
build_project(project_dir)
  → start_dev_server(project_dir, port)
    → take_screenshot(url)
      → ask_about_screenshot(path, specific_question)
        → kill_dev_server(port)
```

Kill the server even if an earlier step fails.

### Asking useful vision questions

The vision tool (`ask_about_screenshot`) returns much better results with **specific, answerable questions** than open-ended prompts:

- Good: "Are the price badges overlapping the piece tokens, or are they visually separated?"
- Good: "Are the piece tokens circular, or do they have square corners?"
- Good: "Do the store rows form clean horizontal lines, or are items wrapping to the next line?"
- Weak: "Does this look correct?" / "Describe the UI."

When reference images are available (e.g. in `project_dir/resources/`), pass each to `ask_about_screenshot` and ask explicitly how the current render differs.

### Drag-and-drop testing

**Critical**: Standard Playwright mouse events (`mouse.down`, `mouse.move`, `mouse.up`) do **not** trigger HTML5 drag-and-drop events. Libraries like react-dnd (HTML5Backend) listen for native `DragEvent` objects (`dragstart`, `dragenter`, `dragover`, `drop`, `dragend`).

Use `simulate_drag(url, source_selector, target_selector)` which dispatches these events correctly via `page.evaluate`.

`simulate_drag` returns:
- `before_path` / `after_path`: screenshot paths to compare visually
- `console_errors`: JS errors logged during the drag — always report these; they explain failed drops

### Layout debugging

Hex board geometry is sensitive to column widths. If a hex board loses its shape after a layout change:
- The board squares are likely fixed-pixel (intrinsic image size), not responsive
- Percentage-based row offsets are a function of column width — changing column width breaks the geometry
- Restore the original column width rather than adjusting the offset percentages

Store/inventory layout: prefer plain CSS flexbox (`justify-content: space-evenly; align-items: flex-end`) over Bootstrap Row/Col for game piece grids. Bootstrap columns add padding that causes wrapping when pieces have fixed widths.

### Price badge / token overlap

When a price badge overlaps a piece token in the store:
- Use `position: absolute; top: 0; left: 0` on the badge with `padding-top/left` on the container to create a corner badge that never overlaps
- Avoid `flexDirection: column` with badge below — this can still cause overlap when pieces are taller than expected

### Circular piece tokens

If piece images have square/rectangular transparent corners that obscure other elements, add `border-radius: 50%` to the `<img>` style. This clips the corners without requiring image editing.

### Turn-rule interaction testing

When the game has per-turn activation restrictions (no acting on the same space twice; newly placed pieces can't be used as sources), verify them explicitly — they are easy to miss in a static screenshot.

Test sequence for "place then immediately use" bug:
1. `simulate_drag` a piece onto an empty board square (e.g. plant a tree)
2. `simulate_drag` a seed from available to a square that would only be in range via the just-planted tree
3. Check `console_errors` and take an after screenshot — the drop should be **rejected** (piece returns to origin, board state unchanged)

If the second drop is accepted, the rule is not being enforced. Fix: ensure the seed-range check excludes squares in `activatedSquaresThisTurn`.

### Reference image comparison

Store reference images in `project_dir/resources/`. When verifying layout changes, always compare against them. Ask: "How does this screenshot compare to [reference]? List specific differences in layout, shapes, colors, and positioning."

---

## Issue Log (Known Failure Cases)

Historical visual bugs to check for on every QA pass:

- **Board clips off left/right edge on mobile (most common visual bug)**: The game board extends beyond the viewport on narrow screens. Usually caused by fixed-width containers, negative margins, or missing `overflow: hidden`. Check at 375px and 390px widths.
- **SVG without viewBox doesn't scale on mobile**: SVG elements without a `viewBox` attribute render at their intrinsic size and don't scale down on narrow viewports. Always verify SVG game boards have `viewBox` set.
- **FAB button overlaps tutorial navigation at bottom**: The floating action button (menu, settings) covers the Next/Previous step buttons in tutorial mode. Check at mobile viewports with tutorial active.
- **Touch targets under 44px on mobile**: Buttons, cells, and interactive elements smaller than 44x44px are hard to tap on mobile. Common in hex game cells and difficulty chooser buttons.
- **Difficulty chooser buttons wrap to second line on narrow screens**: When 4-5 difficulty buttons are in a row, they wrap on screens under 390px wide. Use smaller font, abbreviations, or a different layout for mobile.
- **Start screen scrolled to wrong position after navigation**: After navigating back to the start screen from a game, the page may be scrolled to the bottom instead of the top. Add `window.scrollTo(0, 0)` on screen transitions.
- **Win overlay Elo display shows NaN or wrong values**: The Elo calculation uses values that may be undefined on first game or after a draw. Check that the overlay handles missing/null Elo gracefully.
- **Board too zoomed in on mobile (3D games especially)**: 3D games using react-three-fiber may render too close on mobile, clipping the board edges. Adjust camera position or FOV based on viewport width.
- **Stacked-piece connectivity check ignores stack depth**: When a piece sits on top of a stack (e.g., beetle in Hive), the one-hive/connectivity check must only virtually remove the top piece, not the entire cell. Otherwise, pieces on stacks become permanently immovable if the cell beneath is a connectivity bottleneck. Fix: skip the connectivity check for pieces on stacks with height > 1.
- **Unicode chess piece size asymmetry**: Filled black Unicode chess glyphs (U+265x) render visually larger than outlined white glyphs (U+2659-265F) at the same font size. Apply a ~10% font-size reduction to black pieces across all rendering contexts (board, tutorial, captured list, replay viewer, promotion picker).
- **TouchBackend swallows tap events on mobile**: When react-dnd-touch-backend is active, it intercepts touch events on drag sources even when `canDrag` returns false. This prevents onClick handlers from firing. Fix: disable drag ref on mobile for pieces that use tap-to-select interaction.
- **Action buttons not visually prominent enough**: Critical game actions (End Turn, Submit Move) rendered with subtle styling are easy to miss. Use solid background color with contrast and consider a pulse/glow animation to draw attention.

---

## Feature Request Filtering

Before reporting any finding, check `feature-request-detection.md`. A finding is a **bug** only if:
- The app does something incorrectly relative to its stated behavior
- A UI element is visually broken, inaccessible, or misleading
- A game rule is implemented wrong

A finding is a **feature request** if:
- The app works correctly but the user wants additional functionality
- The issue is about adding new data, new views, or new interactions
- The app is just missing something the user thinks would be nice

**Do not report feature requests in the QA output.** Log them separately in `qa-output/FEATURE-REQUESTS.md` if they come up.

---

## Bug Difficulty Estimation

For each bug found, estimate fix difficulty using the rubric in `difficulty-rubric.md`:

| Level | Label | Typical fix time | Description |
|---|---|---|---|
| 1 | Trivial | < 5 min | Single CSS property change, one-liner fix |
| 2 | Easy | 5-30 min | Small, localized change to one file |
| 3 | Medium | 30 min - 2 hrs | Multiple files or requires understanding component state |
| 4 | Hard | 2-8 hrs | Architectural change, complex state, or requires new component |
| 5 | Very Hard | 8+ hrs | Requires new system, deep game logic rewrite, or infrastructure |

Include the difficulty level in every finding report.

---

## Output Format

Produce a final report saved to `qa-output/REPORT.md` with findings organized by severity:

```markdown
# Pre-Deploy QA Report

## Critical -- Rule/Logic Bugs
Issues where the app behaves incorrectly relative to its spec.

### [BUG-ID]: [Short title]
- **Category**: [category name + number]
- **Difficulty**: [1-5 + label]
- **Location**: [file:line or component name]
- **Expected**: [what should happen]
- **Actual**: [what happens instead]
- **Evidence**: [screenshot filename or code snippet]
- **Fix pattern**: [reference to category file section, if known]

## High -- Mobile/Visual Layout Bugs
Issues where the UI is broken or unusable at specific viewport sizes.

### [BUG-ID]: [Short title]
- **Category**: [category name + number]
- **Difficulty**: [1-5 + label]
- **Viewport**: [device class and dimensions]
- **Screenshot**: [filename]
- **Description**: [what's wrong]
- **Affected element**: [CSS selector or component]
- **Fix pattern**: [reference to category file section, if known]

## Medium -- Content/UX Issues
Issues with navigation, consistency, or clarity.

### [BUG-ID]: [Short title]
- **Category**: [category name + number]
- **Difficulty**: [1-5 + label]
- **Description**: [what's wrong]
- **Suggestion**: [how to fix it]
```

Also save the suggested tests to `qa-output/suggested-tests/` and all screenshots to `qa-output/screenshots/`.
Feature requests go to `qa-output/FEATURE-REQUESTS.md`.

---

## Meta-Learning Protocol

After each QA run and subsequent fixes, update the skill library:

1. **When a bug is fixed successfully**: Open the relevant `categories/*.md` file. Add the fix to the "Known Fix Patterns" section with the exact code change that worked.

2. **When a previously-fixed bug regresses**: Add a "Known Failure Cases" entry in that category file describing what the regression looked like and why the first fix wasn't sufficient.

3. **When a new bug type is discovered that doesn't fit an existing category**: Create a new `categories/*.md` file following the template, then add it to the category table in this SKILL.md.

4. **When fix difficulty estimates are wrong**: Update `difficulty-rubric.md` with the actual time taken and why it differed.

See `meta-learning.md` for the full update protocol and category file template.

---

## Bug Review Pipeline

When reviewing new bug reports (from Supabase or user feedback), use this skill's category system:

1. **Classify each bug** against the 14 categories in `categories/`. If a bug doesn't fit any existing category, create a new category file following the template in `meta-learning.md`.
2. **Update category files** with new fix patterns discovered while fixing bugs. Each successful fix should be added to the relevant category's "Known Fix Patterns" section.
3. **Add failure cases** when a fix doesn't hold or a bug regresses. This trains future sessions to avoid the same mistakes.
4. **Calibrate difficulty estimates** by comparing the rubric prediction against actual fix time.

This ensures the skill library improves with every bug review cycle, not just during scheduled QA runs.

---

## Adapting the Pipeline

The pipeline above is a general-purpose starting point. Adapt it based on the project:

- **For game projects**: Focus heavily on Phase 2 (rules audit) and Phase 1 at mobile viewports. Games have the most complex logic bugs and the most layout variation.
- **For marketing/content sites**: Phase 1 (visual audit) is primary. Add extra viewports for landscape mobile (667 x 375) and check that images and text are legible.
- **For SaaS/dashboards**: Emphasize Phase 1 at tablet and desktop breakpoints. Add checks for data-heavy tables, overflow behavior, and interactive elements like dropdowns and modals.
- **For projects with existing tests**: Start by running the existing test suite first. Then focus the QA pipeline on what tests don't cover -- typically visual layout and edge-case logic.

---

## Important Reminders

- Always capture screenshots BEFORE analyzing. Do not try to predict visual bugs from code alone -- actually render and look at the result.
- If the screenshot capture script fails, debug it. Common issues: server not ready yet (add a wait), wrong port, or SPA routes needing navigation actions rather than direct URL hits.
- When reporting bugs, be specific. "Layout looks off on mobile" is not useful. "The game board's left 40px is clipped offscreen at 375px viewport width because the container has a fixed left margin of -20px" is useful.
- Don't invent bugs that aren't there. If a screenshot looks fine, say so and move on. False positives erode trust in the pipeline.
- The suggested tests in Phase 2 are suggestions for the user to implement. Generate them as clearly as possible with comments explaining what invariant they verify.
- Run this pipeline before every submission/push when changes touch layout, mobile styles, or game logic.
