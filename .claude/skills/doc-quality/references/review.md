# review

Apply the current rubric once to new documentation and write a report. The input is a path to a repository or folder, or to a PDF. This mode never changes the rubric and never proposes changes to it.

`S` below stands for `.claude/skills/doc-quality/scripts`, and `RUN` for the run directory.

## 1. Collect the input

**A repository or folder.** Review covers every prose page. Source files are sampled up to `review_source_file_cap`.

```
python3 S/discover.py folder <path> --run RUN --seed <seed> --source-cap <review_source_file_cap>
```

If it reports that no documentation was found, tell the user and stop. Write no report.

**A PDF.**

1. Extract the text: `python3 S/discover.py pdf-text <file.pdf> --out RUN/document.txt`.
2. If that exits 3, `pdftotext` is not installed. Read the PDF with your own PDF reading instead and transcribe it faithfully into `RUN/document.txt`, word for word. If the PDF is longer than `pdf_transcription_page_cap` pages, stop and tell the user to install `pdftotext` (part of Poppler) or supply a shorter document. Remember that you transcribed, for the report.
3. Read `RUN/document.txt` and choose where sections begin: at each top-level heading, and at the next heading level inside any section longer than about 2,000 words. Note the line number each section starts on. The first must be line 1.
4. Cut the snapshots: `python3 S/discover.py sections RUN/document.txt --starts 1,<n>,<n> --run RUN --source "<document title>"`.

## 2. Fix each page's type

As in step 2 of `refine-rubric.md`: read the opening of each prose page or PDF section, decide its type from the rubric's `page_types`, then:

```
python3 S/discover.py set-types RUN p001=tutorial p002=reference
python3 S/rubric_store.py annotate RUN/items.json
```

Code-comment items keep the type `other`.

## 3. Evaluate in batches

Split the items into batches of about `review_batch_size`. For each batch, spawn one evaluator subagent with the prompt in `evaluator.md`, the newcomer stance, and that batch's item ids. Name them `batch1`, `batch2` and so on, so each writes its own `RUN/verdicts-batchN.json`. Batches can run in parallel. Every item is judged exactly once.

## 4. Validate

```
python3 S/verdicts.py RUN
```

This writes `RUN/valid-verdicts.json`, `RUN/invalid-verdicts.json` and `RUN/missing-verdicts.json`, and prints each criterion left unjudged. Only valid verdicts go in the report. The count of invalid ones goes in the report too.

If anything is unjudged, an evaluator skipped it, wrote an invalid verdict for it, or failed to write its file. Spawn one more evaluator for just the affected items, named `retry1`, then run the command again. Whatever is still unjudged after that one retry is listed in the report as not judged; do not judge it yourself.

## 5. Write the report

Get the header facts:

```
python3 S/registry.py header
```

Write `RUN/report.md` following `report-template.md` exactly. Build it only from these sources:

- `RUN/items.json`: the items, and under `found` how many of each kind were discovered;
- `RUN/valid-verdicts.json`: the verdicts and their evidence;
- `RUN/invalid-verdicts.json` and `RUN/missing-verdicts.json`: the counts set aside and left unjudged;
- `rubric/rubric.json`: each criterion's question;
- the header facts.

Do not add findings of your own, soften a verdict, or leave one out.

## 6. Close

Give the user the report's path and a three-line summary: how many items were reviewed, how many criteria failed across them, and the rubric's tested status from the header. If they disagree with a verdict, the answer is a `refine-rubric` run, not an edit to the rubric or the report.
