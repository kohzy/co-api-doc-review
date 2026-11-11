---
name: doc-quality
description: Evaluate written technical documentation against a tested rubric. Use "refine-rubric <doc-set>" to sharpen the rubric on public docs (add "held-out" to test it on unseen docs), or "review <path>" to get an evidenced quality report on a repository's docs or a PDF. Never edits the documentation it evaluates.
argument-hint: refine-rubric <folder-or-url-list> [held-out] | review <repo-path-or-pdf>
---

# Documentation quality

Judge documentation against the rubric in `rubric/rubric.json`, which covers page structure, usability by reading, and sentence-level clarity. The readable copy is `rubric/RUBRIC.md`.

There are two modes. They share the rubric and nothing else.

| Mode | Invocation | What it does | Changes the rubric? |
|---|---|---|---|
| `refine-rubric` | `refine-rubric <doc-set>` | Three independent evaluators judge a sample of a public doc set. Their disagreements and the user's blind spot-checks drive proposed rubric changes. | Only where the user accepts a proposal |
| `refine-rubric`, held-out | `refine-rubric <doc-set> held-out` | The same run on a doc set the rubric has never seen, to test the rubric. | Never |
| `review` | `review <path>` | One pass over a repository's docs or a PDF, producing a report. | Never |

## Rules that hold in every mode

- **Never edit, move or delete anything in the documentation being evaluated.** Write only under `runs/` and, in `refine-rubric`, under `rubric/`.
- **Never change `rubric/rubric.json` or `rubric/RUBRIC.md` by hand.** The rubric changes only through `rubric_store.py apply`, and only with changes the user accepted in this run.
- **Evaluators are subagents with fresh contexts.** If you cannot spawn subagents, stop and say so. Evaluators that share your context are not independent, and their agreement would mean nothing.
- **Do not judge pages yourself and do not repair an evaluator's verdicts.** Verdicts that fail validation are set aside and counted, as the scripts report.
- **Do not fetch pages with a web-fetch tool.** It returns a model's rendering of the page. `discover.py urls` saves the real text.

## Setup for every run

Run every command from the root of the repository that holds `rubric/`. The scripts are in `.claude/skills/doc-quality/scripts/` and need only Python 3.

1. Read the mode word from the arguments. If it is missing or is neither `refine-rubric` nor `review`, ask the user which they want.
2. Confirm the rubric is sound: `python3 .claude/skills/doc-quality/scripts/rubric_store.py validate`. Stop if it reports a problem.
3. Create the run directory `runs/<YYYY-MM-DD>-<doc-set-name>-<mode>/`, where the mode is `refine-rubric`, `held-out` or `review`. If it exists, add `-2`, `-3` and so on.
4. Read `rubric/config.json` for sample sizes, the batch size and the thresholds.
5. Follow the reference for the mode, in full:
   - `refine-rubric` without `held-out`: `references/refine-rubric.md`
   - `refine-rubric` with `held-out`: `references/held-out.md`
   - `review`: `references/review.md`

`references/evaluator.md` is the prompt every evaluator receives. `references/report-template.md` is the shape of a review report.
