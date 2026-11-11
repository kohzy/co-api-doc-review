# co-api-doc-review

A Claude Code skill that judges written technical documentation against a rubric, and a loop for making that rubric trustworthy.

The rubric is the product. It covers three things: page structure, usability by reading, and sentence-level clarity. Every criterion is a yes/no question, and every verdict must quote the passage that justifies it or say what was looked for and not found.

The skill never edits the documentation it evaluates, and it does not check whether docs are technically accurate.

## Use it

Open this repository in Claude Code. The skill is `/doc-quality`, with two modes.

### `refine-rubric`: make the rubric better

```
/doc-quality refine-rubric path/to/cloned-docs
/doc-quality refine-rubric urls.txt
```

Point it at a public doc set: a folder, or a text file with one URL per line. Each run:

1. Samples up to 12 pages.
2. Has three independent evaluators judge them against the rubric.
3. Measures where the evaluators disagree.
4. Gives you about 12 verdicts to judge yourself, blind. You answer first; the evaluators' verdicts are shown after.
5. Proposes rubric changes, each with its evidence. Nothing changes unless you accept it.

Accepted changes produce a new rubric version and an entry in the change log.

### `refine-rubric ... held-out`: test the rubric

```
/doc-quality refine-rubric path/to/other-docs held-out
```

Runs the same evaluation on a doc set the rubric has never been run on, and changes nothing. The rubric passes when:

- the evaluators agree with each other,
- you agree with the verdicts you spot-check, and
- each criterion fails on at least one page, in a way you confirm matters.

The last condition stops the rubric from passing by becoming easy to agree on.

A doc set can be a held-out test only once, and never after it has been used for refinement. Keep some doc sets in reserve.

Held-out tests are unavailable until you have confirmed the pass thresholds, which the skill asks you to do at the end of your second `refine-rubric` run, once there are real numbers to look at.

### `review`: apply the rubric

```
/doc-quality review path/to/any/repository
/doc-quality review manual.pdf
```

One pass over new documentation, producing a report in `runs/`. In a repository it reads READMEs, Markdown, MDX, reStructuredText and AsciiDoc files, and the docstrings and comments in a sample of source files. A PDF is split into sections first.

Every report opens by saying how far the rubric has been tested: the last version that passed a held-out test, how many changes have been accepted since, and whether that test covered the kind of input being reviewed. Until a version has passed, reports say the rubric is untested.

Review never changes the rubric. If a verdict looks wrong, run `refine-rubric`.

## Where things live

| Path | What it is |
|---|---|
| `rubric/RUBRIC.md` | The rubric, for reading. Rendered; do not edit. |
| `rubric/rubric.json` | The rubric, as the scripts use it. Changed only through accepted proposals. |
| `rubric/changelog.jsonl` | Every accepted change, with its reason and evidence. |
| `rubric/seen.json` | Doc sets already used, and how. |
| `rubric/held-out.json` | Held-out test results per rubric version. |
| `rubric/config.json` | Sample sizes and pass thresholds. |
| `runs/` | One directory per run: pages, verdicts, agreement, reports. |
| `.claude/skills/doc-quality/` | The skill: instructions, evaluator prompt, and scripts. |
| `docs/plans/` | The requirements and implementation plan this was built from. |

## Requirements

Claude Code and Python 3. No Python packages are needed. For PDFs, `pdftotext` (from Poppler) is used when installed; without it the skill transcribes PDFs of up to 60 pages itself and says so in the report.

## Tests

```bash
python3 -m unittest discover -s tests -v
```
