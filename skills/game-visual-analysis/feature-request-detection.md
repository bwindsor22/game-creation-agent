# Feature Request Detection

Before reporting a finding in the QA report, classify it as a **bug** or a **feature request**. Only bugs go in `REPORT.md`. Feature requests go in `FEATURE-REQUESTS.md`.

## Decision Criteria

A finding is a **bug** if ANY of these are true:
- Something that was intended to work doesn't work (broken behavior)
- A UI element is inaccessible, invisible, or overlapping another element
- The app violates its own stated behavior (tutorial says X, game does Y)
- An action produces an error, crash, or no response when a response is expected
- Existing content is wrong (wrong rule text, broken image, incorrect score)

A finding is a **feature request** if ALL of these are true:
- The app works correctly as-is
- The user wants additional data, interactions, or views that don't currently exist
- Implementing it requires adding new code, not fixing broken code

## Common False Positives (these are features, not bugs)

| Description | Classification | Reason |
|---|---|---|
| "Show game notation / move history" | Feature | App never had notation |
| "Add undo button" | Feature (unless button exists and is broken) | New functionality |
| "You Might Also Like should use my preferences" | Feature | Static version works correctly |
| "Strategy Guide link in menu" | Bug IF tutorial link exists elsewhere | Feature if tutorial never existed |
| "Animate piece captures" | Feature | Enhancement, not broken behavior |
| "Show win probability" | Feature | New data display |
| "Board should have coordinates" | Feature | New UI element |
| "AI should explain its moves" | Feature | New functionality |

## How to Handle During QA

1. If uncertain, ask: "Does removing this finding make the app broken or just less good?"
   - **Broken** = bug
   - **Less good** = feature request

2. When user-submitted bug reports are the input: check the `bugs_fixed.md` table. Reports in the "Won't Fix / Feature Requests" section are pre-classified. Do not re-open them.

3. Log feature requests separately: they are useful product feedback even if not bugs.

## Feature Requests Log Format

```markdown
# Feature Requests

## [ID]: [Short title]
- **Game**: [game name]
- **Request**: [what the user wants]
- **Current behavior**: [what the app does now -- and it works correctly]
- **Priority assessment**: P1 / P2 / P3
```
