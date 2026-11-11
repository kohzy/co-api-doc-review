#!/usr/bin/env python3
"""Check evaluator verdicts against the page snapshots they cite.

A verdict is pass or fail on one criterion for one item, with evidence: either
a quote that appears in the item's snapshot, or an absence record saying what
was looked for and where. Verdicts that fail the check are set aside and
counted, never silently used.
"""
import argparse
import json
import sys
from pathlib import Path

from rubric_store import read_json, write_json

VERDICTS = ("pass", "fail")


def squash(text):
    """Collapse all runs of whitespace, so line wrapping never breaks a quote match."""
    return " ".join(text.split())


def verdict_problem(verdict, item, snapshot_text):
    """None when the verdict is usable, otherwise a sentence saying what is wrong with it."""
    if verdict.get("verdict") not in VERDICTS:
        return "verdict must be pass or fail"
    if verdict.get("criterion") not in item["criteria"]:
        return f"criterion {verdict.get('criterion')} does not apply to item {item['id']}"
    evidence = verdict.get("evidence")
    if not isinstance(evidence, dict):
        return "evidence must be a quote or an absence record"
    if "quote" in evidence:
        if not isinstance(evidence["quote"], str):
            return "quote must be text"
        quote = squash(evidence["quote"])
        if not quote:
            return "quote is empty"
        if quote not in squash(snapshot_text):
            return "quote not found in the item's snapshot"
        return None
    if "absent" in evidence:
        absent = evidence["absent"]
        if not isinstance(absent, dict):
            return "absence record must name looked_for and searched"
        for field in ("looked_for", "searched"):
            if not str(absent.get(field, "")).strip():
                return f"absence record is missing {field}"
        return None
    return "evidence must be a quote or an absence record"


def validate_verdicts(submitted, items_by_id, snapshots_by_id):
    """Split one evaluator's verdicts into (valid, invalid). Invalid entries gain a 'problem'."""
    evaluator = submitted.get("evaluator", "unknown")
    valid, invalid, seen = [], [], set()
    for verdict in submitted.get("verdicts", []):
        if not isinstance(verdict, dict):
            invalid.append({"evaluator": evaluator, "problem": "verdict is not an object"})
            continue
        record = dict(verdict, evaluator=evaluator)
        item = items_by_id.get(verdict.get("item"))
        key = (verdict.get("item"), verdict.get("criterion"))
        if item is None:
            problem = f"no item with id {verdict.get('item')}"
        elif key in seen:
            problem = "duplicate verdict for this item and criterion"
        else:
            problem = verdict_problem(verdict, item, snapshots_by_id[item["id"]])
        if problem:
            invalid.append(dict(record, problem=problem))
        else:
            seen.add(key)
            valid.append(record)
    return valid, invalid


def load_run(run_dir):
    """Read a run's items and their snapshot texts."""
    run_dir = Path(run_dir)
    data = read_json(run_dir / "items.json")
    items = {item["id"]: item for item in data["items"]}
    snapshots = {}
    for item in data["items"]:
        path = Path(item["snapshot"])
        if not path.is_absolute():
            path = run_dir / path
        snapshots[item["id"]] = path.read_text(encoding="utf-8", errors="replace")
    return data, items, snapshots


def validate_run(run_dir):
    """Validate every verdicts-*.json in a run directory. Returns (valid, invalid)."""
    run_dir = Path(run_dir)
    _, items, snapshots = load_run(run_dir)
    valid, invalid = [], []
    for path in sorted(run_dir.glob("verdicts-*.json")):
        good, bad = validate_verdicts(read_json(path), items, snapshots)
        valid += good
        invalid += bad
    return valid, invalid


def missing_verdicts(items, valid):
    """Each (item id, criterion id) pair that has no valid verdict from anyone."""
    judged = {(verdict["item"], verdict["criterion"]) for verdict in valid}
    return [(item["id"], criterion) for item in items.values()
            for criterion in item["criteria"] if (item["id"], criterion) not in judged]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", help="run directory holding items.json and verdicts-*.json")
    args = parser.parse_args(argv)
    valid, invalid = validate_run(args.run)
    run_dir = Path(args.run)
    _, items, _ = load_run(run_dir)
    missing = missing_verdicts(items, valid)
    write_json(run_dir / "valid-verdicts.json", valid)
    write_json(run_dir / "invalid-verdicts.json", invalid)
    write_json(run_dir / "missing-verdicts.json",
               [{"item": item, "criterion": criterion} for item, criterion in missing])
    print(f"{len(valid)} valid verdicts, {len(invalid)} set aside as invalid, "
          f"{len(missing)} criteria left unjudged")
    for entry in invalid:
        print(f"  invalid: {entry['evaluator']} {entry.get('item')} {entry.get('criterion')}: "
              f"{entry['problem']}")
    for item, criterion in missing:
        print(f"  unjudged: {item} {criterion}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
