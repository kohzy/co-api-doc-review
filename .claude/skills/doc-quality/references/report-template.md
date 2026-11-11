# Review report template

Write `report.md` in this shape. Text in angle brackets is filled in; everything else is literal. Omit a section only where the template says so.

## How to fill the status block

Use the JSON from `registry.py header`.

- `last_passed_version` is null: write the **Untested** line.
- Otherwise, write the **Tested** line with `last_passed_version` and `changes_since_pass`.
- For each input kind present in this review, look it up in `coverage`. If it is false, add a **Not covered** line for it. Name the kinds for a reader: prose pages, PDF sections, docstrings and code comments.
- If `not_tested` lists criteria that appear in this report, add the **Not exercised** line.

## Template

```markdown
# Documentation review: <what was reviewed>

<date> · rubric version <current_version>

> **Untested rubric.** No version of this rubric has passed a held-out test. Treat every verdict below as provisional.

> **Tested at version <last_passed_version>.** <changes_since_pass> rubric changes have been accepted since that test. <If zero: "This is the tested version.">

> **Not covered by that test:** <kind>. The rubric has not been checked on this kind of input, so verdicts on it are provisional.

> **Not exercised by that test:** <criterion ids>. The test's sample had too few applicable pages to check these criteria.

> **Transcribed PDF.** `pdftotext` was not available, so the text was transcribed and quotes were checked against the transcription, not the original file.

## What was reviewed

| Kind | Found | Reviewed |
|---|---|---|
| Prose pages | <n> | <n> |
| PDF sections | <n> | <n> |
| Source files with comments | <n> | <n> |

<One sentence if source files were sampled: "Source files were sampled; <n> of <n> were reviewed.">
<One sentence if any verdicts were invalid: "<n> verdicts were set aside because their evidence could not be found in the page.">

## Summary

<n> of <n> judged criteria failed across <n> items.

| Criterion | Question | Failed on |
|---|---|---|
| <id> | <question> | <n> of <n> items |

List only criteria with at least one failure, most failures first.

## Findings by item

### <source> (<page type>)

**Failed**

- **<criterion id>. <question>**
  > <the quoted evidence, exactly as in the verdict>

- **<criterion id>. <question>**
  Looked for <looked_for> in <searched>; not found.

**Passed:** <criterion ids, comma-separated>

Repeat for every item, in item order. Use the quote form or the looked-for form according to the verdict's evidence. If an item has no failures, write "**Failed:** none".

## Changing a criterion

This report applies the rubric as it stands and does not change it. If a verdict here looks wrong, the criterion may need rewording: run `refine-rubric` on a public doc set to test and revise it.
```

Keep the quoted evidence verbatim. Do not summarise it, merge findings, rank items by overall quality, or add recommendations for fixing the documentation.
