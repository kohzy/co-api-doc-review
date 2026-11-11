#!/usr/bin/env python3
"""Measure how far independent evaluators agree, pick a blind spot-check set,
score the user's spot-check verdicts, and decide a held-out test.

Agreement is Gwet's AC1, which stays meaningful when nearly every page passes.
"""
import argparse
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

from rubric_store import read_json, write_json
from verdicts import VERDICTS, validate_run

GROUPS = ("unanimous", "contested")


def _ac1(vote_lists):
    """Gwet's AC1 over units, each a list of pass/fail votes. None when it cannot be computed."""
    rated = [votes for votes in vote_lists if len(votes) >= 2]
    if len(rated) < 2:
        return None
    observed = 0.0
    for votes in rated:
        counts = Counter(votes)
        n = len(votes)
        observed += sum(c * (c - 1) for c in counts.values()) / (n * (n - 1))
    observed /= len(rated)
    share_pass = sum(votes.count("pass") / len(votes) for votes in vote_lists) / len(vote_lists)
    chance = 2 * share_pass * (1 - share_pass)
    if chance >= 1:
        return None
    return (observed - chance) / (1 - chance)


def _criterion_order(criterion_id):
    """Sort C2 before C10."""
    digits = "".join(ch for ch in criterion_id if ch.isdigit())
    return (int(digits) if digits else 0, criterion_id)


def _majority(votes):
    counts = Counter(votes)
    for category in VERDICTS:
        if counts[category] >= 2:
            return category
    return None


def summarise(valid_verdicts):
    """Agreement and pass rate per criterion, overall agreement, and every judged unit.

    A unit is one criterion judged on one item. Its majority is at least two
    identical verdicts; a unit without one is marked no-majority.
    """
    grouped = defaultdict(list)
    for verdict in valid_verdicts:
        grouped[(verdict["item"], verdict["criterion"])].append(verdict)

    units = []
    for (item, criterion), verdicts in sorted(grouped.items()):
        votes = [v["verdict"] for v in verdicts]
        unanimous = len(votes) >= 2 and len(set(votes)) == 1
        units.append({
            "item": item,
            "criterion": criterion,
            "votes": votes,
            "majority": _majority(votes),
            "unanimous": unanimous,
            "contested": not unanimous,
            "verdicts": [{"evaluator": v["evaluator"], "verdict": v["verdict"],
                          "evidence": v["evidence"]} for v in verdicts],
        })

    criteria = {}
    for criterion in sorted({u["criterion"] for u in units}, key=_criterion_order):
        own = [u for u in units if u["criterion"] == criterion]
        decided = [u for u in own if u["majority"]]
        tested = sum(1 for u in own if len(u["votes"]) >= 2) >= 2
        criteria[criterion] = {
            "items": len(own),
            "tested": tested,
            "ac1": _ac1([u["votes"] for u in own]) if tested else None,
            "unanimous_share": sum(1 for u in own if u["unanimous"]) / len(own),
            "pass_rate": (sum(1 for u in decided if u["majority"] == "pass") / len(decided)
                          if decided else None),
            "no_majority": len(own) - len(decided),
            "never_fails": tested and not any(u["majority"] == "fail" for u in own),
        }
    return {
        "overall_ac1": _ac1([u["votes"] for u in units]),
        "criteria": criteria,
        "units": units,
    }


def select_spot_checks(summary, rubric, config, seed):
    """Choose spot-check items. Returns (items, sealed, notes).

    Items carry only what the user needs to judge. Sealed holds the evaluators'
    verdicts, keyed by item id, and is read only after the user has answered.
    """
    quota = config["spot_check"]
    rng = random.Random(seed)
    by_id = {c["id"]: c for c in rubric["criteria"]}
    notes = []

    contested = [u for u in summary["units"] if u["contested"]]
    rng.shuffle(contested)

    def difficulty(unit):
        ac1 = summary["criteria"][unit["criterion"]]["ac1"]
        return (unit["majority"] is not None, ac1 if ac1 is not None else -1.0)

    contested.sort(key=difficulty)
    chosen, per_criterion = [], Counter()
    for unit in contested:
        if len(chosen) == quota["contested"]:
            break
        if per_criterion[unit["criterion"]] >= quota["max_per_criterion"]:
            continue
        per_criterion[unit["criterion"]] += 1
        chosen.append(("contested", unit))

    unanimous = [u for u in summary["units"] if u["unanimous"]]
    rng.shuffle(unanimous)
    usability_passes = [u for u in unanimous if u["majority"] == "pass"
                        and by_id.get(u["criterion"], {}).get("dimension") == "usability"]
    picked = usability_passes[:quota["unanimous_usability_passes"]]
    if len(picked) < quota["unanimous_usability_passes"]:
        notes.append(f"only {len(picked)} unanimous usability passes were available")
    rest = [u for u in unanimous if all(u is not p for p in picked)]
    target = quota["contested"] + quota["unanimous"]
    shortfall = quota["contested"] - len(chosen)
    if shortfall:
        notes.append(f"only {len(chosen)} contested items were available; "
                     "the rest of the set is filled from unanimous items")
    picked += rest[:max(0, target - len(chosen) - len(picked))]
    chosen += [("unanimous", unit) for unit in picked]
    if len(chosen) < target:
        notes.append(f"the set has {len(chosen)} items; there were not enough verdicts for {target}")

    rng.shuffle(chosen)
    items, sealed = [], {}
    for index, (group, unit) in enumerate(chosen, start=1):
        spot_id = f"s{index:02d}"
        criterion = by_id.get(unit["criterion"], {})
        items.append({
            "id": spot_id,
            "item": unit["item"],
            "criterion": unit["criterion"],
            "question": criterion.get("question", ""),
            "guidance": criterion.get("guidance", ""),
        })
        sealed[spot_id] = {"group": group, "majority": unit["majority"],
                           "verdicts": unit["verdicts"]}
    return items, sealed, notes


def _empty_scores():
    return {group: {"agree": 0, "total": 0} for group in GROUPS}


def score_user(user_verdicts, sealed):
    """Count how often the user matched the evaluators' majority, per group.

    Items with no majority are shown to the user but not scored.
    """
    scores = _empty_scores()
    for spot_id, answer in user_verdicts.items():
        entry = sealed[spot_id]
        if entry["majority"] is None:
            continue
        scores[entry["group"]]["total"] += 1
        if answer == entry["majority"]:
            scores[entry["group"]]["agree"] += 1
    return scores


def _ratio(score):
    return score["agree"] / score["total"] if score["total"] else None


def decide_held_out(summary, user_scores, failures_confirmed, config, active_criteria=None):
    """Decide whether a held-out test passed, with the reasons when it did not."""
    measures = {
        "overall_ac1": summary["overall_ac1"],
        "criteria": {cid: {"ac1": c["ac1"], "pass_rate": c["pass_rate"]}
                     for cid, c in summary["criteria"].items()},
        "user_agreement_unanimous": _ratio(user_scores["unanimous"]),
        "user_agreement_contested": _ratio(user_scores["contested"]),
    }
    tested = [cid for cid, c in summary["criteria"].items() if c["tested"]]
    everything = set(summary["criteria"]) | set(active_criteria or [])
    result = {"passed": False, "refused": False, "reasons": [], "measures": measures,
              "not_tested": sorted(everything - set(tested))}

    if not config.get("thresholds_confirmed"):
        result["refused"] = True
        result["reasons"].append("the pass thresholds have not been confirmed by the user yet")
        return result

    limits = config["thresholds"]
    reasons = result["reasons"]
    overall = summary["overall_ac1"]
    if overall is None or overall < limits["overall_ac1"]:
        shown = "unavailable" if overall is None else f"{overall:.2f}"
        reasons.append(f"overall agreement is {shown}, below {limits['overall_ac1']:.2f}")
    for cid in tested:
        criterion = summary["criteria"][cid]
        if criterion["ac1"] is None or criterion["ac1"] < limits["criterion_ac1"]:
            reasons.append(f"{cid}: agreement is {_format(criterion['ac1'])}, "
                           f"below {limits['criterion_ac1']:.2f}")
        if criterion["never_fails"]:
            reasons.append(f"{cid} never fails on this doc set, so it tells no pages apart")
        elif failures_confirmed.get(cid) is not True:
            reasons.append(f"{cid}: the user did not confirm that its failures matter")
    agreement = measures["user_agreement_unanimous"]
    if agreement is None:
        reasons.append("no unanimous spot-check items were scored")
    elif agreement < limits["user_agreement_unanimous"]:
        reasons.append(f"spot-check agreement on unanimous items is {agreement:.0%}, "
                       f"below {limits['user_agreement_unanimous']:.0%}")
    result["passed"] = not reasons
    return result


def example_failures(summary):
    """One majority-fail unit per tested criterion, for the user to judge whether it matters."""
    examples = {}
    for unit in summary["units"]:
        cid = unit["criterion"]
        if summary["criteria"][cid]["tested"] and unit["majority"] == "fail":
            examples.setdefault(cid, unit)
    return examples


def _format(value, pattern="{:.2f}"):
    return "n/a" if value is None else pattern.format(value)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="repository root holding rubric/")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, text in (
        ("summarise", "validate verdicts and write summary.json"),
        ("spot-check", "write the blind items file and the sealed answers file"),
        ("score", "score user-verdicts.json against the sealed answers"),
        ("failures", "show one failing example per tested criterion"),
        ("decide", "decide a held-out test and write decision.json"),
    ):
        p = sub.add_parser(name, help=text)
        p.add_argument("run")
        if name == "spot-check":
            p.add_argument("--seed", type=int, required=True)
    p = sub.add_parser("reveal", help="print the sealed answer for one spot-check item")
    p.add_argument("run")
    p.add_argument("id")
    args = parser.parse_args(argv)

    run = Path(args.run)
    rubric_dir = Path(args.root) / "rubric"

    if args.command == "summarise":
        valid, invalid = validate_run(run)
        write_json(run / "invalid-verdicts.json", invalid)
        summary = summarise(valid)
        summary["invalid_verdicts"] = len(invalid)
        write_json(run / "summary.json", summary)
        print(f"{len(valid)} valid verdicts, {len(invalid)} set aside as invalid")
        for evaluator, count in sorted(Counter(e["evaluator"] for e in invalid).items()):
            print(f"  {count} from {evaluator}")
        print(f"overall agreement (AC1): {_format(summary['overall_ac1'])}")
        for cid, c in summary["criteria"].items():
            flags = [] if c["tested"] else ["not tested"]
            if c["never_fails"]:
                flags.append("never fails")
            if c["no_majority"]:
                flags.append(f"{c['no_majority']} without a majority")
            print(f"  {cid}: AC1 {_format(c['ac1'])}, pass rate {_format(c['pass_rate'], '{:.0%}')}, "
                  f"{c['items']} items" + (f" ({'; '.join(flags)})" if flags else ""))
    elif args.command == "spot-check":
        items, sealed, notes = select_spot_checks(
            read_json(run / "summary.json"), read_json(rubric_dir / "rubric.json"),
            read_json(rubric_dir / "config.json"), args.seed)
        write_json(run / "spot-check-items.json", {"seed": args.seed, "items": items, "notes": notes})
        write_json(run / "spot-check-sealed.json", sealed)
        print(f"wrote {len(items)} spot-check items")
        for note in notes:
            print(f"  note: {note}")
    elif args.command == "reveal":
        entry = read_json(run / "spot-check-sealed.json")[args.id]
        print(f"majority: {entry['majority'] or 'none'} ({entry['group']})")
        for verdict in entry["verdicts"]:
            evidence = verdict["evidence"]
            shown = (f'"{evidence["quote"]}"' if "quote" in evidence else
                     f"looked for {evidence['absent']['looked_for']} in {evidence['absent']['searched']}")
            print(f"  {verdict['evaluator']}: {verdict['verdict']} — {shown}")
    elif args.command == "score":
        scores = score_user(read_json(run / "user-verdicts.json"),
                            read_json(run / "spot-check-sealed.json"))
        write_json(run / "user-scores.json", scores)
        for group, score in scores.items():
            print(f"{group}: agreed on {score['agree']} of {score['total']}")
    elif args.command == "failures":
        examples = example_failures(read_json(run / "summary.json"))
        write_json(run / "failure-examples.json", examples)
        for cid, unit in examples.items():
            print(f"{cid}: fails on {unit['item']}")
    elif args.command == "decide":
        rubric = read_json(rubric_dir / "rubric.json")
        items = read_json(run / "items.json")["items"]
        confirmed_path = run / "failures-confirmed.json"
        scores_path = run / "user-scores.json"
        decision = decide_held_out(
            read_json(run / "summary.json"),
            read_json(scores_path) if scores_path.exists() else _empty_scores(),
            read_json(confirmed_path) if confirmed_path.exists() else {},
            read_json(rubric_dir / "config.json"),
            active_criteria=[c["id"] for c in rubric["criteria"] if c["status"] == "active"])
        decision["rubric_version"] = rubric["version"]
        decision["input_kinds"] = sorted({item["kind"] for item in items})
        write_json(run / "decision.json", decision)
        if decision["refused"]:
            print("refused: " + decision["reasons"][0])
            return 1
        print("held-out test " + ("passed" if decision["passed"] else "not passed"))
        for reason in decision["reasons"]:
            print(f"  {reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
