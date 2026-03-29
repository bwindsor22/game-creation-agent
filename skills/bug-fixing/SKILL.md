---
name: bug-fixing
description: Three-stage workflow for fixing portal bugs (reproduce, fix, update skill + Supabase) and a separate workflow for feature requests. Includes Supabase tracking to prevent re-fixing.
---

# Bug-Fixing Workflow

Every bug follows three stages: reproduce, fix, update. No exceptions. Skipping Stage 3 means the fix is invisible to future sessions and the same bug pattern will be re-investigated.

Feature requests follow a different workflow (see below).

The portal lives at `/Users/brad/projects/code/abstracts/portal`.

---

## Supabase Credentials

Credentials are stored in `/Users/brad/projects/code/game-creation-agent/.env` (gitignored). Load them before any Supabase operation:

```bash
source /Users/brad/projects/code/game-creation-agent/.env
```

Then use `$SUPABASE_URL` and `$SUPABASE_ANON_KEY` in curl commands. Never hard-code credentials in skill files, markdown, or any git-tracked file.

---

## Step 0: Understand the Report

Read the report and identify the domain. Everything is a bug or an improvement to fix. "Works but could be better" still follows the same three-stage workflow. The only difference is scope: a rule-breaking logic error is a quick fix, while "the end-turn button should be more obvious" may involve design judgment. Both go through reproduce, fix, update.

---

## Before You Start: Check Supabase

Before touching any code, check whether the bug is already resolved:

```bash
source /Users/brad/projects/code/game-creation-agent/.env
curl -s \
  -H "apikey: $SUPABASE_ANON_KEY" \
  -H "Authorization: Bearer $SUPABASE_ANON_KEY" \
  "$SUPABASE_URL/rest/v1/bug_reports?id=eq.BUG_ID&select=id,description,resolved_at,resolved_notes"
```

If `resolved_at` is non-null, the bug was already fixed. Do not re-fix it. Move on.

---

## Stage 1: Reproduce Using the Relevant Skill

Before writing any code, identify which verification skill covers the bug's domain and use that skill's approach to reproduce it.

### Skill Mapping Table

| Bug Category | Verification Skill | Programmatic Check |
|---|---|---|
| Tutorial text/content | tutorial-verification | verify-tactics.mjs, grep for em dashes/double hyphens |
| Tutorial rendering | tutorial-verification | Build + screenshot at mobile/desktop |
| Tactics puzzle logic | tactics-verification | verify-tactics.mjs |
| AI too easy/hard | ai-verification | Run naive strategies, check win rates |
| AI rule violation | ai-verification + game-visual-analysis | Replay AI game, check move legality |
| Visual/layout/mobile | game-visual-analysis | Screenshot at 390x844 + 1280x800 |
| Game rule/logic | game-visual-analysis | Read Game.js, trace the rule, write test case |
| Writing style | writing-style guide | grep for em dashes, double hyphens in .jsx/.json |

### Reproduction Steps

1. **Identify the domain.** Read the bug report. Determine which row in the table above it falls into.

2. **Run the programmatic check first, if one exists.**
   - Tutorial/tactics bugs: `cd /Users/brad/projects/code/abstracts/portal && node scripts/verify-tactics.mjs`
   - Writing style: grep for em dashes and double hyphens in the relevant files.

3. **If the bug is visual, take screenshots at the reported viewport.**
   ```python
   python3 -c "
   import sys; sys.path.insert(0, '/Users/brad/projects/code/game-creation-agent')
   from tools.screenshot_tool import take_screenshot
   path = take_screenshot('http://localhost:PORT/ROUTE', output_path='/tmp/bug-repro.png', viewport={'width': 390, 'height': 844})
   print(path)
   "
   ```

4. **If the bug is a game rule/logic issue, trace the rule through Game.js.** Read the relevant game engine at `portal/src/games/<game-id>/Game.js`. Find the function that implements the reported behavior. Identify the exact code path that produces the wrong result.

5. **Document what you find.** Write down: (a) whether the bug reproduces, (b) the root cause if found, (c) which files are involved.

6. **If the bug cannot be reproduced**, check if it was already fixed in a prior session. If so, mark it resolved in Supabase and move on. If not previously fixed and still cannot be reproduced, note this in the Supabase record and move on.

---

## Stage 2: Fix the Bug

Fix the bug in the portal codebase. Then verify the fix.

### By Bug Type

**Rule/logic bugs:**
- Fix the logic in `Game.js` or the relevant engine file.
- Write a test case or trace the fix through the engine manually. If verify-tactics.mjs covers it, run the script.
- Build the project to confirm no compilation errors.

**Visual/layout bugs:**
- Fix the CSS or component code.
- Build the project: `python3 /Users/brad/projects/code/game-creation-agent/tools/npm_build.py /Users/brad/projects/code/abstracts/portal`
- Take before/after screenshots at the reported viewport size.

**Tutorial bugs:**
- Fix the tutorial JSON or rendering component.
- Run `node scripts/verify-tactics.mjs` if the bug involves puzzle logic.
- Take a screenshot to verify text rendering and layout.

**AI bugs:**
- Fix the AI logic in `AI/ai.js` or the heuristic.
- Run the naive strategy tests from ai-verification to confirm the fix does not break difficulty balance.

**Writing style bugs:**
- Fix the text in the relevant .jsx or .json file.
- Grep the file to confirm no remaining em dashes or double hyphens.

### Build Verification

Always build after fixing:

```bash
python3 /Users/brad/projects/code/game-creation-agent/tools/npm_build.py /Users/brad/projects/code/abstracts/portal
```

A broken build is worse than the original bug. Do not proceed to Stage 3 until the build succeeds.

---

## Stage 3: Update the Relevant Skill + Supabase

This is the most important stage. Never skip it. An untracked fix will be re-investigated in the next bug pull.

### 3a. Update the Verification Skill's Issue Log

Open the relevant skill's SKILL.md (based on the mapping table) and add a new entry to its **Issue Log (Known Failure Cases)** section.

The entry must be **general enough to catch similar bugs in the future**, not specific to this one instance.

**Good example:** "Tutorial text referencing board coordinates not visible on the board UI (e.g., 'row 0' on a board with no row labels)."

**Bad example:** "Flips tutorial lesson 3 references row 0 but the board has no row labels."

The good version catches the same bug in any game's tutorial. The bad version only catches the exact instance.

Skill files to update:

| Skill | File |
|---|---|
| tutorial-verification | `skills/tutorial-verification/SKILL.md` |
| tactics-verification | `skills/tactics-verification/SKILL.md` |
| ai-verification | `skills/ai-verification/SKILL.md` |
| game-visual-analysis | `skills/game-visual-analysis/SKILL.md` |

### 3b. Update Supabase

Mark the bug as resolved:

```bash
source /Users/brad/projects/code/game-creation-agent/.env
curl -s -X PATCH \
  -H "apikey: $SUPABASE_ANON_KEY" \
  -H "Authorization: Bearer $SUPABASE_ANON_KEY" \
  -H "Content-Type: application/json" \
  -H "Prefer: return=minimal" \
  -d '{"resolved_at": "ISO_DATE", "resolution_notes": "Brief description of the fix", "status": "resolved"}' \
  "$SUPABASE_URL/rest/v1/bug_reports?id=eq.BUG_ID"
```

Replace `BUG_ID` with the actual bug ID, `ISO_DATE` with the current timestamp.

### 3c. Consider Programmatic Test Additions

Ask: could this bug have been caught automatically? If yes, note what test should be added to the relevant verification skill's Programmatic Tests section.

Examples:
- A tutorial referencing invisible coordinates could be caught by grepping tutorial JSON for coordinate patterns and cross-referencing with the game's board rendering.
- An AI difficulty regression could be caught by adding the specific naive strategy to the AI verification script.
- A missing sandwich stone in a Pente puzzle is already caught by verify-tactics.mjs.

If the test is straightforward to add, add it. If it requires significant work, note it as a TODO in the skill file.

---

## Supabase Operations Reference

Credentials are in `/Users/brad/projects/code/game-creation-agent/.env`. Always `source` this file before running commands.

### Fetch all open bugs

```bash
curl -s \
  -H "apikey: $SUPABASE_ANON_KEY" \
  -H "Authorization: Bearer $SUPABASE_ANON_KEY" \
  "$SUPABASE_URL/rest/v1/bug_reports?resolved_at=is.null&order=created_at.desc"
```

### Fetch open bugs for a specific game

```bash
curl -s \
  -H "apikey: $SUPABASE_ANON_KEY" \
  -H "Authorization: Bearer $SUPABASE_ANON_KEY" \
  "$SUPABASE_URL/rest/v1/bug_reports?game_id=eq.GAME_ID&resolved_at=is.null"
```

### Mark a bug as resolved

```bash
curl -s -X PATCH \
  -H "apikey: $SUPABASE_ANON_KEY" \
  -H "Authorization: Bearer $SUPABASE_ANON_KEY" \
  -H "Content-Type: application/json" \
  -H "Prefer: return=minimal" \
  -d '{"resolved_at": "ISO_DATE", "resolution_notes": "Description of fix", "status": "resolved"}' \
  "$SUPABASE_URL/rest/v1/bug_reports?id=eq.BUG_ID"
```

### Fetch a single bug by ID

```bash
curl -s \
  -H "apikey: $SUPABASE_ANON_KEY" \
  -H "Authorization: Bearer $SUPABASE_ANON_KEY" \
  "$SUPABASE_URL/rest/v1/bug_reports?id=eq.BUG_ID&select=*"
```

---

## Larger Improvements

Some reports describe improvements that require more design judgment (e.g., "end-turn button should be more obvious," "add push-off animation"). These still follow the three stages, with one addition:

**Before Stage 2**, read the game-creation-agent `CLAUDE.md` to check if an existing skill covers the domain (tutorial-creation for tutorial content, ai-creation for AI improvements, etc.). Use that skill's approach. For larger changes, check with the user before implementing.

---

## Anti-Patterns

- **Never fix a bug without checking Supabase first.** It may already be resolved. Duplicate work wastes time and can introduce regressions.
- **Never skip Stage 3.** An untracked fix will be re-investigated in the next bug pull. The Supabase update is what prevents re-work.
- **Never add an Issue Log entry that is too specific to one instance.** Generalize the pattern so it catches the entire class of bug, not just the one occurrence.
- **Never forget to build and verify after fixing.** A broken build is worse than the original bug.
- **Never hard-code Supabase credentials in git-tracked files.** Always source from `.env`.
- **Never fix multiple bugs in a single commit without building between each.** One bad fix can mask another, and reverting becomes harder.
- **Never dismiss a report as "just a feature request."** If a user reported it, it's worth fixing.

---

## Writing Style

All user-facing text written or modified during bug fixes must follow the writing style guide at `skills/writing-style/writing-style.md`. The most common violation: em dashes. Replace with commas, periods, or parentheses.

---

## Integration with Other Skills

This skill orchestrates the other verification skills. It does not replace them.

| Skill | Role in Bug-Fixing |
|---|---|
| `tutorial-verification/` | Stage 1 reproduction for tutorial bugs. Stage 3 Issue Log updates. |
| `tactics-verification/` | Stage 1 reproduction for puzzle logic bugs. verify-tactics.mjs. |
| `ai-verification/` | Stage 1 reproduction for AI bugs. Naive strategy tests. |
| `game-visual-analysis/` | Stage 1 reproduction for visual/layout/rule bugs. Screenshot pipeline. |
| `writing-style/` | Stage 2 text fixes. Grep checks for prohibited punctuation. |
| `tutorial-creation/` | Reference when tutorial structure or content needs changes. |
| `ai-creation/` | Reference when AI logic or difficulty needs changes. |
