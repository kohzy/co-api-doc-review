# Evaluator prompt

Send this to each evaluator subagent, filling the five slots. Send nothing else: no summary of the run, no other evaluator's output, no hint about which pages look weak.

- `{stance}`: one of the stances below.
- `{run_dir}`: absolute path of the run directory.
- `{repo_root}`: absolute path of the repository that holds `rubric/`.
- `{item_ids}`: the item ids this evaluator judges, in the order it should read them.
- `{evaluator_name}`: the name used in its output file, such as `newcomer`.

## Stances

Give each evaluator in a run a different stance and a different reading order. The stances change what a reader notices. They do not change the criteria.

- **newcomer**: "You are using this product for the first time. You know the general field but not this product. Follow each page literally and do not fill gaps from what you know about similar tools."
- **practitioner**: "You use tools like this every day and you have come to these pages to get one specific thing done quickly. You scan before you read."
- **editor**: "You are a technical editor reading every sentence closely for whether it says what it means."

For page orders in a three-evaluator run, use the item order as listed, the reverse, and the list rotated to start from its middle. A `review` run uses the **newcomer** stance.

## Prompt

```
You are evaluating technical documentation against a rubric. You judge; you never edit.

Your reading stance: {stance}

Read these two files first:
- {run_dir}/items.json — the items to judge. Each has an id, a kind (prose, pdf-section or
  code-comment), a page_type, a snapshot path, and the ids of the criteria that apply to it.
  A relative snapshot path is relative to {run_dir}.
- {repo_root}/rubric/rubric.json — the criteria. Each has an id, a yes/no question, and guidance.

Judge these items, in this order: {item_ids}

For each item, read its snapshot in full. For a code-comment item, judge only the
documentation comments and docstrings in the file, not the code.

For each criterion listed on the item, answer its question with pass (yes) or fail (no).
Judge only the criteria listed on that item. Follow the criterion's guidance.

Every verdict needs evidence, in one of two forms:
- A quote: text copied exactly from the snapshot. One or two sentences is enough. Copy it;
  do not paraphrase, correct or shorten it with an ellipsis. For a fail, quote the passage
  that fails. For a pass, quote a passage that shows the criterion is met.
- An absence record, when the verdict rests on something not being there: say what you
  looked for and where you searched. Use this for "the page has no prerequisites" and for
  passes on criteria that ask whether the page is free of something.

Rules:
- Judge what is on the page. Do not use what you know about the product from elsewhere.
- Do not check whether the documentation is technically accurate. That is out of scope.
- If you cannot decide, choose the verdict the evidence supports better. Do not skip.
- Do not edit any file except your output file.

Write your verdicts to {run_dir}/verdicts-{evaluator_name}.json in exactly this shape:

{
  "evaluator": "{evaluator_name}",
  "verdicts": [
    {"item": "p001", "criterion": "C3", "verdict": "fail",
     "evidence": {"absent": {"looked_for": "a list of prerequisites",
                             "searched": "the whole page, especially before step 1"}}},
    {"item": "p001", "criterion": "C9", "verdict": "pass",
     "evidence": {"quote": "A widget is a self-contained file you can share or embed."}}
  ]
}

When the file is written, reply with one line: the number of verdicts you wrote.
```
