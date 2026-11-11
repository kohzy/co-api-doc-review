# refine-rubric, held-out

Test the rubric on a doc set it has never been run on. This run never changes the rubric and never proposes changes. Each test uses up one unseen doc set, so check everything before any evaluator runs.

`S` below stands for `.claude/skills/doc-quality/scripts`, and `RUN` for the run directory.

## 1. Checks before starting

Stop at the first check that fails, and tell the user why.

1. **Thresholds confirmed.** If `rubric/config.json` has `"thresholds_confirmed": false`, stop. A pass would be judged against values the user has never seen. They are confirmed at the end of the second `refine-rubric` run.
2. **Doc set unseen.** `python3 S/registry.py check-held-out <doc-set>`. If it exits 1, stop and show its message.
3. **Not seen under another name.** `python3 S/registry.py list-seen`. Show the list and ask the user to confirm this doc set is not among them under a different address or name. The same docs can be supplied as a cloned folder one time and a URL list the next, and the record cannot always tell.

## 2. Collect, type, evaluate, measure

Follow steps 1 to 4 of `refine-rubric.md` unchanged, with one difference: sample `held_out_sample` pages, not `refine_sample`.

## 3. Blind spot-checks

Follow step 5 of `refine-rubric.md` unchanged, including never opening the sealed file yourself.

## 4. Do the failures matter?

A rubric can pass on agreement alone while its criteria catch nothing worth catching. So for each criterion that was tested and failed on at least one page:

```
python3 S/agreement.py failures RUN
```

This writes `RUN/failure-examples.json`: one failing page per criterion, with the evaluators' evidence. For each one, show the user the criterion, the page and the quoted evidence, and ask: does this failure matter to a reader? Yes or no.

Write the answers to `RUN/failures-confirmed.json` as `{"C3": true, "C17": false}`.

## 5. Decide and record

```
python3 S/agreement.py decide RUN
python3 S/registry.py record-held-out <doc-set> --date <YYYY-MM-DD> --run RUN
python3 S/registry.py record-use <doc-set> --mode held-out --date <YYYY-MM-DD> --run RUN
```

`decide` prints passed or not passed with every reason. Criteria the sample could not exercise are listed as not tested; they do not block a pass, and review reports will say so.

## 6. Close

Tell the user the result and each reason behind it. If the test did not pass, say which criteria were responsible and that the way to fix them is another `refine-rubric` run on a different doc set. Do not propose rubric changes here.
