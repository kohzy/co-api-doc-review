# Documentation review: https://docs.mangrovesystems.com/api-reference/cookbooks/batch-generation

2026-11-11 · rubric version 1

> **Untested rubric.** No version of this rubric has passed a held-out test. Treat every verdict below as provisional.

## What was reviewed

| Kind | Found | Reviewed |
|---|---|---|
| Prose pages | 1 | 1 |
| PDF sections | 0 | 0 |
| Source files with comments | 0 | 0 |

## Summary

5 of 18 judged criteria failed across 1 items.

| Criterion | Question | Failed on |
|---|---|---|
| C9 | Is every term the page relies on defined, linked, or safely assumed for its stated audience? | 1 of 1 items |
| C14 | Does the page say what to do when something it describes commonly goes wrong? | 1 of 1 items |
| C17 | Can every sentence be understood on first reading? | 1 of 1 items |
| C18 | Is each thing called by the same name throughout? | 1 of 1 items |
| C20 | Is the page free of sentences that could be deleted without losing information? | 1 of 1 items |

## Findings by item

### https://docs.mangrovesystems.com/api-reference/cookbooks/batch-generation (how-to)

**Failed**

- **C9. Is every term the page relies on defined, linked, or safely assumed for its stated audience?**
  > Batch generation is the process of running a model against collected data to produce batches on a ledger.

- **C14. Does the page say what to do when something it describes commonly goes wrong?**
  > failedTask encountered an error: check error_message

- **C17. Can every sentence be understood on first reading?**
  > The full amount is drawn either way, so running fewer partitions gives each a larger share rather than drawing less from the source batch.

- **C18. Is each thing called by the same name throughout?**
  > Use the Mangrove API to check required inputs, preview batch generation, and trigger batch creation for a ledger.

- **C20. Is the page free of sentences that could be deleted without losing information?**
  > This cookbook walks through the full workflow: checking what inputs are needed, previewing the results, and triggering generation.

**Passed:** C1, C2, C3, C4, C5, C7, C10, C11, C12, C13, C19, C21, C22

## Changing a criterion

This report applies the rubric as it stands and does not change it. If a verdict here looks wrong, the criterion may need rewording: run `refine-rubric` on a public doc set to test and revise it.
