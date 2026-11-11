#!/usr/bin/env python3
"""Record which doc sets have been seen and which rubric versions passed a
held-out test, and compute the facts a review report states in its header.

State files: rubric/seen.json and rubric/held-out.json.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

from rubric_store import INPUT_KINDS, read_json, write_json

CODE_HOSTS = ("github.com", "gitlab.com", "bitbucket.org", "codeberg.org")
EMPTY_SEEN = {"doc_sets": []}
EMPTY_HELD_OUT = {"results": []}


def normalise_identity(source):
    """Reduce a git remote, a site URL, or a plain name to one comparable identity."""
    text = source.strip()
    ssh = re.match(r"^[\w.-]+@([\w.-]+):(.+)$", text)
    if ssh:
        host, path = ssh.group(1), ssh.group(2)
        return _repo_identity(host, path)
    if re.match(r"^[a-z][a-z0-9+.-]*://", text, re.I):
        parts = urlsplit(text)
        host = (parts.hostname or "").lower()
        if host in CODE_HOSTS or parts.path.rstrip("/").endswith(".git"):
            return _repo_identity(host, parts.path)
        return host
    return text.lower()


def _repo_identity(host, path):
    path = path.strip("/")
    if path.endswith(".git"):
        path = path[:-4]
    return f"{host}/{path}".lower()


def identify(source):
    """Identity for a doc set given as a folder, a URL-list file, or a name."""
    path = Path(source)
    if path.is_dir():
        remote = subprocess.run(["git", "-C", str(path), "remote", "get-url", "origin"],
                                capture_output=True, text=True)
        if remote.returncode == 0 and remote.stdout.strip():
            return normalise_identity(remote.stdout.strip())
        return normalise_identity(path.resolve().name)
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                return normalise_identity(line.strip())
    return normalise_identity(source)


def seen_entry(seen, source):
    identity = normalise_identity(source)
    for entry in seen["doc_sets"]:
        if entry["id"] == identity:
            return entry
    return None


def record_use(seen, source, mode, date, run):
    entry = seen_entry(seen, source)
    if entry is None:
        entry = {"id": normalise_identity(source), "uses": []}
        seen["doc_sets"].append(entry)
    entry["uses"].append({"mode": mode, "date": date, "run": run})
    return entry


def held_out_refusal(seen, source):
    """None when the doc set may serve as a held-out test, otherwise the reason it may not."""
    entry = seen_entry(seen, source)
    if entry is None:
        return None
    uses = ", ".join(f"{u['mode']} on {u['date']}" for u in entry["uses"])
    return (f"{entry['id']} has already been seen ({uses}), so it cannot be a held-out test. "
            "A held-out test needs a doc set the rubric has never been run on.")


def record_held_out(held_out, version, date, doc_set, passed, measures, input_kinds,
                    not_tested, reasons):
    held_out["results"].append({
        "version": version,
        "date": date,
        "doc_set": normalise_identity(doc_set),
        "passed": passed,
        "measures": measures,
        "input_kinds": sorted(input_kinds),
        "not_tested": sorted(not_tested),
        "reasons": reasons,
    })
    return held_out


def header_facts(current_version, changelog, held_out):
    """What a review report must say about how far the rubric has been tested."""
    passes = [r for r in held_out["results"] if r["passed"]]
    facts = {
        "current_version": current_version,
        "last_passed_version": None,
        "changes_since_pass": None,
        "coverage": {kind: False for kind in INPUT_KINDS},
        "not_tested": [],
    }
    if not passes:
        return facts
    latest = max(passes, key=lambda r: r["version"])
    facts["last_passed_version"] = latest["version"]
    facts["changes_since_pass"] = sum(1 for e in changelog if e["version"] > latest["version"])
    for kind in latest["input_kinds"]:
        facts["coverage"][kind] = True
    facts["not_tested"] = list(latest["not_tested"])
    return facts


def read_changelog(path):
    path = Path(path)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _load(path, empty):
    path = Path(path)
    return read_json(path) if path.exists() else json.loads(json.dumps(empty))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="repository root holding rubric/")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("identify", help="print the identity a doc set is recorded under")
    p.add_argument("source")
    sub.add_parser("list-seen", help="print every doc set in the seen record")
    p = sub.add_parser("check-held-out", help="exit 1 when the doc set has been seen")
    p.add_argument("source")
    p = sub.add_parser("record-use", help="record a doc set as seen")
    p.add_argument("source")
    p.add_argument("--mode", required=True, choices=("refine-rubric", "held-out"))
    p.add_argument("--date", required=True)
    p.add_argument("--run", required=True)
    p = sub.add_parser("record-held-out", help="record a held-out decision from a run directory")
    p.add_argument("source")
    p.add_argument("--date", required=True)
    p.add_argument("--run", required=True, help="run directory holding decision.json")
    sub.add_parser("header", help="print the report header facts as JSON")
    args = parser.parse_args(argv)

    base = Path(args.root) / "rubric"
    seen_path, held_path = base / "seen.json", base / "held-out.json"
    seen = _load(seen_path, EMPTY_SEEN)
    held_out = _load(held_path, EMPTY_HELD_OUT)

    if args.command == "identify":
        print(identify(args.source))
    elif args.command == "list-seen":
        if not seen["doc_sets"]:
            print("no doc sets have been seen yet")
        for entry in seen["doc_sets"]:
            uses = ", ".join(f"{u['mode']} {u['date']}" for u in entry["uses"])
            print(f"{entry['id']}: {uses}")
    elif args.command == "check-held-out":
        reason = held_out_refusal(seen, identify(args.source))
        if reason:
            print(reason)
            return 1
        print("unseen: may be used as a held-out test")
    elif args.command == "record-use":
        entry = record_use(seen, identify(args.source), args.mode, args.date, args.run)
        write_json(seen_path, seen)
        print(f"recorded {entry['id']} as seen ({args.mode})")
    elif args.command == "record-held-out":
        decision = read_json(Path(args.run) / "decision.json")
        if decision.get("refused"):
            print("refused decisions are not recorded: " + "; ".join(decision["reasons"]))
            return 1
        record_held_out(held_out, decision["rubric_version"], args.date, identify(args.source),
                        decision["passed"], decision["measures"], decision["input_kinds"],
                        decision["not_tested"], decision["reasons"])
        write_json(held_path, held_out)
        print("recorded held-out result: " + ("passed" if decision["passed"] else "not passed"))
    elif args.command == "header":
        rubric = read_json(base / "rubric.json")
        facts = header_facts(rubric["version"], read_changelog(base / "changelog.jsonl"), held_out)
        print(json.dumps(facts, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
