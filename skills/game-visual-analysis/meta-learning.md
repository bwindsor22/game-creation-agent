# Meta-Learning Protocol

This document describes how to update the skill library as bugs are found, fixed, and (sometimes) reintroduced.

The goal: the skill library grows smarter over time. Each fix adds a known pattern. Each regression adds a failure case note. Over time, the agent can estimate fix difficulty accurately and reference prior art instead of starting from scratch.

---

## When to Update

| Trigger | Action |
|---|---|
| Bug successfully fixed and verified | Add fix to "Known Fix Patterns" in relevant category file |
| Bug fixed, but fix later regresses | Add entry to "Known Failure Cases" with why it regressed |
| New bug type found with no matching category | Create new category file + add row to SKILL.md category table |
| Fix difficulty was significantly wrong | Update "Difficulty estimate" in category file + update `difficulty-rubric.md` |
| Feature request misclassified as bug | Add example to `feature-request-detection.md` common false positives table |

---

## How to Add a Fix Pattern

Open the relevant `categories/*.md` file and add a new entry under "Known Fix Patterns":

```markdown
### Pattern X: [Short description] (applied to [game] on [date])
[Code snippet showing the fix]

**Why it works**: [Brief explanation of the root cause and why this fix addresses it]

**When to use**: [Conditions where this pattern applies]
```

Keep each pattern focused on one concrete change. Multiple related changes in a single PR can each be separate patterns if they address different root causes.

---

## How to Add a Failure Case

Under "Known Failure Cases" in the category file:

```markdown
- **[Date] regression in [game]**: [What broke]. Root cause: [why it broke]. The original fix [description] was insufficient because [reason]. Fixed again by [description of updated fix].
```

---

## New Category File Template

When a new bug type appears that doesn't match any existing category, create `categories/[slug].md`:

```markdown
# Category N: [Name]

**Difficulty estimate**: N (Label)

## Detection Signals

- [Specific visual or behavioral signal]
- [Another signal]

## Root Causes

1. [Root cause 1]
2. [Root cause 2]

## Known Fix Patterns

(Empty on first creation -- will be filled after the bug is fixed)

## Known Failure Cases

(Empty on first creation)

## Verification

[How to verify the fix worked]
```

Then add a row to the category table in SKILL.md:

```markdown
| N | [Category name] | `categories/[slug].md` | [Viewport Focus] |
```

---

## Difficulty Calibration

After each bug fix session, compare the estimated difficulty (in the category file) against actual time spent:

- If actual was < half the estimate: lower the estimate by 1 level
- If actual was > 2x the estimate: raise the estimate by 1 level
- If actual matched: no change needed

Update the category file's "Difficulty estimate" line accordingly, and add a note to `difficulty-rubric.md` if a new pattern was discovered (e.g., "SVG viewBox fixes are always Level 1 regardless of game").

---

## Bug Report Classification Over Time

As more user-submitted bug reports are processed, track patterns in how reports are classified:

- Reports that were feature requests: note the phrasing pattern in `feature-request-detection.md`
- Reports that described multiple bugs in one: note how they were split
- Reports that were duplicates: note which canonical bug they were duplicates of

Over time, the feature-request-detection.md table of "Common False Positives" will grow and the agent will misclassify fewer reports.
