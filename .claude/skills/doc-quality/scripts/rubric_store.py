#!/usr/bin/env python3
"""Load, validate, version and render the documentation-quality rubric.

The rubric lives in rubric/rubric.json. rubric/RUBRIC.md is rendered from it
and is never edited by hand. Accepted changes are appended to
rubric/changelog.jsonl, one line per change.
"""
import argparse
import copy
import json
import sys
from pathlib import Path

DIMENSIONS = ("structure", "usability", "clarity")
INPUT_KINDS = ("prose", "pdf-section", "code-comment")
CHANGE_TYPES = ("reword", "split", "add", "drop")
ANY_PAGE_TYPE = "*"

DIMENSION_TITLES = {
    "structure": "Page structure",
    "usability": "Usability by reading",
    "clarity": "Sentence-level clarity",
}


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def validate(rubric):
    """Return a list of problems; an empty list means the rubric is valid."""
    errors = []
    if not isinstance(rubric.get("version"), int) or rubric["version"] < 1:
        errors.append("version must be a positive integer")
    page_types = rubric.get("page_types") or []
    if not page_types:
        errors.append("page_types must list at least one page type")
    seen = set()
    for c in rubric.get("criteria", []):
        cid = c.get("id", "<missing id>")
        if cid in seen:
            errors.append(f"{cid}: duplicate criterion id")
        seen.add(cid)
        if c.get("dimension") not in DIMENSIONS:
            errors.append(f"{cid}: dimension must be one of {', '.join(DIMENSIONS)}")
        if not str(c.get("question", "")).strip().endswith("?"):
            errors.append(f"{cid}: question must be a yes/no question ending in a question mark")
        if c.get("status") not in ("active", "dropped"):
            errors.append(f"{cid}: status must be active or dropped")
        applies = c.get("applies_to") or {}
        types = applies.get("page_types") or []
        kinds = applies.get("input_kinds") or []
        if not types:
            errors.append(f"{cid}: applies_to.page_types must not be empty")
        for t in types:
            if t != ANY_PAGE_TYPE and t not in page_types:
                errors.append(f"{cid}: page type {t} is not in the rubric's page_types")
        if not kinds:
            errors.append(f"{cid}: applies_to.input_kinds must not be empty")
        for k in kinds:
            if k not in INPUT_KINDS:
                errors.append(f"{cid}: input kind {k} must be one of {', '.join(INPUT_KINDS)}")
        if c.get("dimension") == "structure" and "code-comment" in kinds:
            errors.append(f"{cid}: structure criteria may not apply to the code-comment input kind")
    return errors


def applicable(rubric, page_type, input_kind):
    """Active criteria that apply to a page of this type and input kind."""
    result = []
    for c in rubric["criteria"]:
        if c["status"] != "active":
            continue
        applies = c["applies_to"]
        if input_kind not in applies["input_kinds"]:
            continue
        if ANY_PAGE_TYPE in applies["page_types"] or page_type in applies["page_types"]:
            result.append(c)
    return result


def _next_id(rubric):
    numbers = [int(c["id"][1:]) for c in rubric["criteria"] if c["id"][1:].isdigit()]
    return f"C{max(numbers, default=0) + 1}"


def _find(rubric, cid):
    for c in rubric["criteria"]:
        if c["id"] == cid:
            if c["status"] != "active":
                raise ValueError(f"{cid} has been dropped and cannot be changed")
            return c
    raise ValueError(f"no criterion with id {cid}")


def _new_criterion(rubric, fields, version):
    return {
        "id": _next_id(rubric),
        "dimension": fields["dimension"],
        "applies_to": copy.deepcopy(fields["applies_to"]),
        "question": fields["question"],
        "guidance": fields.get("guidance", ""),
        "added_in": version,
        "status": "active",
    }


def apply_changes(rubric, changes, date):
    """Apply a batch of accepted changes as one version bump.

    Returns (new_rubric, changelog_entries). The input rubric is not modified.
    An empty batch returns the rubric unchanged with no entries.
    """
    if not changes:
        return rubric, []
    updated = copy.deepcopy(rubric)
    version = rubric["version"] + 1
    updated["version"] = version
    entries = []
    for change in changes:
        kind = change.get("type")
        if kind not in CHANGE_TYPES:
            raise ValueError(f"change type must be one of {', '.join(CHANGE_TYPES)}")
        if not str(change.get("reason", "")).strip():
            raise ValueError(f"{kind} change needs a reason")
        entry = {
            "version": version,
            "date": date,
            "type": kind,
            "reason": change["reason"],
            "evidence": change.get("evidence", ""),
        }
        if kind == "add":
            new = _new_criterion(updated, change["criterion"], version)
            updated["criteria"].append(new)
            entry["ids"] = [new["id"]]
            entry["after"] = [new["question"]]
        elif kind == "drop":
            target = _find(updated, change["id"])
            target["status"] = "dropped"
            entry["ids"] = [target["id"]]
            entry["before"] = [target["question"]]
        elif kind == "reword":
            target = _find(updated, change["id"])
            entry["ids"] = [target["id"]]
            entry["before"] = [target["question"]]
            for field in ("question", "guidance"):
                if field in change:
                    target[field] = change[field]
            entry["after"] = [target["question"]]
        elif kind == "split":
            target = _find(updated, change["id"])
            entry["before"] = [target["question"]]
            inherited = {**target, **change["new"]}
            new = _new_criterion(updated, inherited, version)
            for field in ("question", "guidance"):
                if field in change["keep"]:
                    target[field] = change["keep"][field]
            updated["criteria"].append(new)
            entry["ids"] = [target["id"], new["id"]]
            entry["after"] = [target["question"], new["question"]]
        entries.append(entry)
    errors = validate(updated)
    if errors:
        raise ValueError("changes would break the rubric: " + "; ".join(errors))
    return updated, entries


def render(rubric):
    """Markdown view of the active criteria, grouped by dimension."""
    lines = [
        "# Documentation quality rubric",
        "",
        f"Version {rubric['version']}. Rendered from `rubric/rubric.json`; do not edit by hand.",
        "",
        "Every criterion is a yes/no question. A verdict must quote the passage that "
        "justifies it, or, when it rests on something being absent, say what was looked "
        "for and where.",
        "",
        "Page types: " + ", ".join(rubric["page_types"]) + ".",
    ]
    for dimension in DIMENSIONS:
        active = [c for c in rubric["criteria"]
                  if c["dimension"] == dimension and c["status"] == "active"]
        if not active:
            continue
        lines += ["", f"## {DIMENSION_TITLES[dimension]}", ""]
        for c in active:
            types = c["applies_to"]["page_types"]
            scope = "all page types" if ANY_PAGE_TYPE in types else ", ".join(types)
            kinds = ", ".join(c["applies_to"]["input_kinds"])
            lines.append(f"### {c['id']}. {c['question']}")
            lines.append("")
            if c.get("guidance"):
                lines.append(c["guidance"])
                lines.append("")
            lines.append(f"Applies to: {scope}; {kinds}. Added in version {c['added_in']}.")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def annotate_items(rubric, items):
    """Attach to each item the ids of the criteria that apply to it."""
    for item in items:
        if item["page_type"] not in rubric["page_types"]:
            raise ValueError(f"{item['id']}: page type {item['page_type']} is not one of "
                             + ", ".join(rubric["page_types"]))
        item["criteria"] = [c["id"] for c in applicable(rubric, item["page_type"], item["kind"])]
    return items


def _paths(root):
    base = Path(root) / "rubric"
    return base / "rubric.json", base / "RUBRIC.md", base / "changelog.jsonl"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="repository root holding rubric/")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate", help="check rubric.json and that RUBRIC.md is current")
    sub.add_parser("render", help="rewrite RUBRIC.md from rubric.json")
    p = sub.add_parser("annotate", help="add applicable criteria ids to a run's items file")
    p.add_argument("items")
    p = sub.add_parser("apply", help="apply a file of accepted changes as one new version")
    p.add_argument("changes", help="JSON file holding a list of accepted changes")
    p.add_argument("--date", required=True)
    args = parser.parse_args(argv)

    rubric_path, rendered_path, changelog_path = _paths(args.root)
    rubric = read_json(rubric_path)

    if args.command == "validate":
        errors = validate(rubric)
        if not rendered_path.exists() or rendered_path.read_text(encoding="utf-8") != render(rubric):
            errors.append("rubric/RUBRIC.md is out of date; run the render command")
        for e in errors:
            print(e, file=sys.stderr)
        if not errors:
            active = sum(1 for c in rubric["criteria"] if c["status"] == "active")
            print(f"rubric version {rubric['version']} is valid: {active} active criteria")
        return 1 if errors else 0

    if args.command == "render":
        rendered_path.write_text(render(rubric), encoding="utf-8")
        print(f"wrote {rendered_path}")
        return 0

    if args.command == "annotate":
        data = read_json(args.items)
        annotate_items(rubric, data["items"])
        data["rubric_version"] = rubric["version"]
        write_json(args.items, data)
        print(f"annotated {len(data['items'])} items against rubric version {rubric['version']}")
        return 0

    if args.command == "apply":
        updated, entries = apply_changes(rubric, read_json(args.changes), args.date)
        if not entries:
            print(f"no changes accepted; rubric stays at version {rubric['version']}")
            return 0
        write_json(rubric_path, updated)
        rendered_path.write_text(render(updated), encoding="utf-8")
        with changelog_path.open("a", encoding="utf-8") as log:
            for entry in entries:
                log.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(f"rubric is now version {updated['version']}: {len(entries)} changes logged")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
