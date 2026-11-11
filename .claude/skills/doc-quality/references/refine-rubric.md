# refine-rubric

Sharpen the rubric using one public doc set. The doc set is a local folder (such as a cloned docs repository) or a text file listing one URL per line.

`S` below stands for `.claude/skills/doc-quality/scripts`, and `RUN` for the run directory.

## 1. Collect and sample the pages

Pick a seed for the run: any integer. Say what it is and reuse it wherever a seed is asked for.

- Folder: `python3 S/discover.py folder <path> --run RUN --seed <seed> --sample <refine_sample>`
- URL list: `python3 S/discover.py urls <file> --run RUN --seed <seed> --sample <refine_sample>`

If a URL yields no text, the command stops and names it. Tell the user, and ask whether to drop that URL from the list and rerun.

## 2. Fix each page's type

`RUN/items.json` holds a first guess at each item's `page_type`, made from its path alone. Read the opening of each prose snapshot and decide its type from the rubric's `page_types`: tutorial, how-to, reference, explanation, readme, quickstart, landing or other. Then record your decisions and attach the criteria that apply:

```
python3 S/discover.py set-types RUN p001=tutorial p002=reference
python3 S/rubric_store.py annotate RUN/items.json
```

Decide each type once, here. Evaluators do not get a say in which criteria apply, so that they disagree only about quality.

## 3. Run three evaluators

Spawn three subagents in parallel, each with the prompt in `evaluator.md`, the stances newcomer, practitioner and editor, and three different page orders. Wait for all three. Each writes `RUN/verdicts-<name>.json`.

If one fails to write its file, spawn it once more with the same prompt. If it fails again, stop the run and say so: two evaluators are not enough.

## 4. Measure agreement

```
python3 S/agreement.py summarise RUN
```

This checks every quote against its snapshot, sets invalid verdicts aside, and prints agreement and pass rate per criterion. Show the user that table. Say plainly how many verdicts were set aside and from which evaluator.

## 5. Blind spot-checks

```
python3 S/agreement.py spot-check RUN --seed <seed>
```

This writes `RUN/spot-check-items.json`. **Do not open `RUN/spot-check-sealed.json` yourself at any point.** It holds the evaluators' verdicts, and reading it before the user answers would let it leak into how you present the item.

Tell the user how many items there are and that the evaluators' verdicts stay hidden until they answer. Then, for each item in file order:

1. Show the criterion's question and guidance, and the page: its source, and the snapshot text (or the relevant part, for a long page, with the path so they can open the whole thing).
2. Ask for their verdict with the blocking question tool: pass, fail, or skip. Do not hint.
3. Record the answer, then reveal: `python3 S/agreement.py reveal RUN <id>`. Show them what the evaluators said.
4. If they disagree with the evaluators, or the evaluators split, ask in one line what tipped it for them. Note the answer; it is the best evidence you will get for a rewording.

Write the answers to `RUN/user-verdicts.json` as `{"s01": "pass", "s02": "fail"}`, leaving out skipped items, then:

```
python3 S/agreement.py score RUN
```

## 6. Propose rubric changes

A criterion is a candidate for change when any of these hold:

- its agreement is low, or several of its items had no majority;
- the user disagreed with the evaluators on it, especially on a unanimous verdict;
- it never fails, so it tells no pages apart;
- the user's comments showed it asks two questions at once, or misses something they cared about.

For each candidate, read the evaluators' evidence in `RUN/summary.json` to see why they diverged. Then write a proposal: reword, split, add or drop. A proposal needs a reason in one or two sentences and a pointer to its evidence (the run directory and the item ids). Do not propose a change you cannot tie to evidence from this run. Proposing nothing is a valid outcome.

Guard against one drift in particular: do not reword a criterion merely so that evaluators agree more easily. A criterion that is easy to agree on and never fails is worse than one that is contested and useful.

Present the proposals one at a time. For each, show the current wording, the proposed wording, the reason and the evidence, and ask the user to accept or reject it. Write the accepted ones to `RUN/accepted-changes.json` as a list in the shape `rubric_store.py` expects:

```json
[
  {"type": "reword", "id": "C10", "question": "...?", "guidance": "...",
   "reason": "...", "evidence": "runs/<run>: p003, p007"},
  {"type": "split", "id": "C12", "keep": {"question": "...?"}, "new": {"question": "...?", "guidance": "..."},
   "reason": "...", "evidence": "..."},
  {"type": "add", "criterion": {"dimension": "usability", "question": "...?", "guidance": "...",
   "applies_to": {"page_types": ["*"], "input_kinds": ["prose", "pdf-section"]}},
   "reason": "...", "evidence": "..."},
  {"type": "drop", "id": "C20", "reason": "...", "evidence": "..."}
]
```

Then apply them, which bumps the version once and logs each change:

```
python3 S/rubric_store.py apply RUN/accepted-changes.json --date <YYYY-MM-DD>
```

If the user accepted nothing, write an empty list and still run the command; it reports that the version is unchanged.

## 7. Record the doc set as seen

Only now, with the run's results on disk:

```
python3 S/registry.py record-use <doc-set> --mode refine-rubric --date <YYYY-MM-DD> --run RUN
```

## 8. Confirm the thresholds after the second run

Check `rubric/seen.json`. If this was the second or a later `refine-rubric` run and `rubric/config.json` still has `"thresholds_confirmed": false`, the user has now seen real numbers. Show them:

- overall agreement and the range of per-criterion agreement from the runs so far;
- their own agreement on unanimous and on contested spot-checks;
- the provisional values in `rubric/config.json`: the three thresholds, the sample sizes and the spot-check counts;
- the rule that a held-out pass is judged on their agreement with **unanimous** spot-checks only, with contested ones reported for information.

Ask them to confirm these or change them. Edit `rubric/config.json` with their answers and set `"thresholds_confirmed": true`. Held-out tests cannot run until this is done.

## 9. Close

Tell the user: the rubric version now, how many changes were accepted, how many doc sets have been seen, and whether held-out tests are available yet.
