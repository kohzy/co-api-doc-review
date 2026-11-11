import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import support  # noqa: F401
import agreement as ag
import registry

CONFIG = {
    "thresholds_confirmed": True,
    "spot_check": {"contested": 8, "unanimous": 4, "unanimous_usability_passes": 3,
                   "max_per_criterion": 2},
    "thresholds": {"overall_ac1": 0.8, "criterion_ac1": 0.6, "user_agreement_unanimous": 0.85},
}

RUBRIC = {"version": 1, "page_types": ["other"], "criteria": [
    {"id": "U1", "dimension": "usability", "question": "Usable one?", "guidance": "", "status": "active"},
    {"id": "U2", "dimension": "usability", "question": "Usable two?", "guidance": "", "status": "active"},
    {"id": "S1", "dimension": "structure", "question": "Structured?", "guidance": "", "status": "active"},
    {"id": "K1", "dimension": "clarity", "question": "Clear?", "guidance": "", "status": "active"},
]}


def units(criterion, patterns, evaluators=("a", "b", "c")):
    """Build verdicts from strings such as 'PPF': one letter per evaluator, '-' for none."""
    result = []
    for index, pattern in enumerate(patterns, start=1):
        for evaluator, letter in zip(evaluators, pattern):
            if letter == "-":
                continue
            result.append({"evaluator": evaluator, "item": f"p{index:03d}", "criterion": criterion,
                           "verdict": "pass" if letter == "P" else "fail",
                           "evidence": {"quote": "q"}})
    return result


class Ac1Tests(unittest.TestCase):
    def test_identical_verdicts_give_perfect_agreement(self):
        summary = ag.summarise(units("K1", ["PPP", "FFF", "PPP"]))
        self.assertEqual(summary["criteria"]["K1"]["ac1"], 1.0)
        self.assertEqual(summary["overall_ac1"], 1.0)

    def test_criterion_every_page_passes_is_perfect_and_never_fails(self):
        k1 = ag.summarise(units("K1", ["PPP", "PPP", "PPP"]))["criteria"]["K1"]
        self.assertEqual(k1["ac1"], 1.0)
        self.assertEqual(k1["pass_rate"], 1.0)
        self.assertTrue(k1["never_fails"])

    def test_hand_worked_example(self):
        # Five pages, three evaluators: PPP PPP PPF FFF PFF.
        # Observed agreement = (1 + 1 + 1/3 + 1 + 1/3) / 5 = 0.7333.
        # Share of pass verdicts = (1 + 1 + 2/3 + 0 + 1/3) / 5 = 0.6.
        # Chance agreement = 2 * 0.6 * 0.4 = 0.48.  AC1 = (0.7333 - 0.48) / 0.52 = 0.4872.
        k1 = ag.summarise(units("K1", ["PPP", "PPP", "PPF", "FFF", "PFF"]))["criteria"]["K1"]
        self.assertAlmostEqual(k1["ac1"], 0.49, places=2)
        self.assertAlmostEqual(k1["pass_rate"], 0.6, places=2)
        self.assertAlmostEqual(k1["unanimous_share"], 0.6, places=2)
        self.assertFalse(k1["never_fails"])

    def test_fewer_than_two_applicable_pages_is_not_tested(self):
        k1 = ag.summarise(units("K1", ["PPP"]))["criteria"]["K1"]
        self.assertFalse(k1["tested"])
        self.assertIsNone(k1["ac1"])

    def test_one_to_one_split_is_no_majority_and_left_out_of_pass_rate(self):
        summary = ag.summarise(units("K1", ["PF-", "PPP", "FFF"]))
        k1 = summary["criteria"]["K1"]
        self.assertEqual(k1["no_majority"], 1)
        self.assertAlmostEqual(k1["pass_rate"], 0.5)
        unit = next(u for u in summary["units"] if u["item"] == "p001")
        self.assertIsNone(unit["majority"])
        self.assertTrue(unit["contested"])


class SpotCheckTests(unittest.TestCase):
    def mostly_unanimous(self):
        verdicts = []
        verdicts += units("U1", ["PPP"] * 6)
        verdicts += units("U2", ["PPP"] * 6)
        verdicts += units("S1", ["PPP", "FFF", "PPP", "PPP", "PPP", "PPF"])
        verdicts += units("K1", ["FFF", "PPP", "PPP", "PPP", "PPP", "PFF"])
        return ag.summarise(verdicts)

    def test_set_still_contains_unanimous_items_mostly_usability_passes(self):
        items, sealed, notes = ag.select_spot_checks(self.mostly_unanimous(), RUBRIC, CONFIG, seed=7)
        unanimous = [i for i in items if sealed[i["id"]]["group"] == "unanimous"]
        usability_passes = [i for i in unanimous
                            if i["criterion"] in ("U1", "U2") and sealed[i["id"]]["majority"] == "pass"]
        self.assertGreaterEqual(len(unanimous), 4)
        self.assertGreaterEqual(len(usability_passes), 3)

    def test_shortfall_of_contested_items_is_filled_from_unanimous_and_noted(self):
        items, sealed, notes = ag.select_spot_checks(self.mostly_unanimous(), RUBRIC, CONFIG, seed=7)
        contested = [i for i in items if sealed[i["id"]]["group"] == "contested"]
        self.assertEqual(len(contested), 2)
        self.assertEqual(len(items), 12)
        self.assertTrue(any("contested" in note for note in notes), notes)

    def test_items_carry_no_verdict_or_evidence(self):
        items, _, _ = ag.select_spot_checks(self.mostly_unanimous(), RUBRIC, CONFIG, seed=7)
        for item in items:
            self.assertEqual(set(item), {"id", "item", "criterion", "question", "guidance"})

    def test_same_seed_gives_same_set(self):
        first, _, _ = ag.select_spot_checks(self.mostly_unanimous(), RUBRIC, CONFIG, seed=7)
        second, _, _ = ag.select_spot_checks(self.mostly_unanimous(), RUBRIC, CONFIG, seed=7)
        self.assertEqual(first, second)

    def test_at_most_two_contested_items_per_criterion(self):
        summary = ag.summarise(units("K1", ["PPF"] * 6) + units("S1", ["PFF"] * 6))
        items, sealed, _ = ag.select_spot_checks(summary, RUBRIC, CONFIG, seed=1)
        contested = [i for i in items if sealed[i["id"]]["group"] == "contested"]
        for criterion in ("K1", "S1"):
            self.assertLessEqual(sum(1 for i in contested if i["criterion"] == criterion), 2)


class ScoreTests(unittest.TestCase):
    SEALED = {
        "s1": {"group": "unanimous", "majority": "pass"},
        "s2": {"group": "unanimous", "majority": "fail"},
        "s3": {"group": "contested", "majority": "pass"},
        "s4": {"group": "contested", "majority": None},
    }

    def test_groups_are_scored_separately_and_no_majority_is_unscored(self):
        scores = ag.score_user({"s1": "pass", "s2": "pass", "s3": "pass", "s4": "fail"}, self.SEALED)
        self.assertEqual(scores["unanimous"], {"agree": 1, "total": 2})
        self.assertEqual(scores["contested"], {"agree": 1, "total": 1})


class DecideTests(unittest.TestCase):
    def healthy(self):
        verdicts = []
        for criterion in ("U1", "S1", "K1"):
            verdicts += units(criterion, ["PPP", "PPP", "FFF", "PPP", "FFF"])
        return ag.summarise(verdicts)

    def scores(self, unanimous=(4, 4), contested=(3, 8)):
        return {"unanimous": {"agree": unanimous[0], "total": unanimous[1]},
                "contested": {"agree": contested[0], "total": contested[1]}}

    def confirmed(self, summary, value=True):
        return {cid: value for cid in summary["criteria"]}

    def test_healthy_run_passes_even_with_low_contested_agreement(self):
        summary = self.healthy()
        decision = ag.decide_held_out(summary, self.scores(), self.confirmed(summary), CONFIG)
        self.assertTrue(decision["passed"], decision["reasons"])
        self.assertEqual(decision["measures"]["user_agreement_contested"], 3 / 8)

    def test_unconfirmed_thresholds_refuse_to_decide(self):
        summary = self.healthy()
        config = dict(CONFIG, thresholds_confirmed=False)
        decision = ag.decide_held_out(summary, self.scores(), self.confirmed(summary), config)
        self.assertFalse(decision["passed"])
        self.assertTrue(decision["refused"])
        self.assertIn("confirmed", decision["reasons"][0])

    def test_criterion_that_never_fails_blocks_the_pass_and_is_named(self):
        verdicts = units("U1", ["PPP", "PPP", "FFF", "PPP", "FFF"]) + units("K1", ["PPP"] * 5)
        summary = ag.summarise(verdicts)
        self.assertGreaterEqual(summary["overall_ac1"], 0.85)
        decision = ag.decide_held_out(summary, self.scores(), self.confirmed(summary), CONFIG)
        self.assertFalse(decision["passed"])
        self.assertTrue(any("K1" in reason and "never fails" in reason for reason in decision["reasons"]))

    def test_untested_criterion_is_recorded_and_does_not_block(self):
        summary = ag.summarise(units("U1", ["PPP", "PPP", "FFF", "PPP", "FFF"]) + units("S1", ["PPP"]))
        decision = ag.decide_held_out(summary, self.scores(), {"U1": True}, CONFIG)
        self.assertTrue(decision["passed"], decision["reasons"])
        self.assertEqual(decision["not_tested"], ["S1"])

    def test_criterion_with_no_applicable_pages_is_recorded_as_not_tested(self):
        summary = ag.summarise(units("U1", ["PPP", "PPP", "FFF", "PPP", "FFF"]))
        decision = ag.decide_held_out(summary, self.scores(), {"U1": True}, CONFIG,
                                      active_criteria=["U1", "S1"])
        self.assertEqual(decision["not_tested"], ["S1"])

    def test_low_agreement_on_unanimous_spot_checks_blocks_the_pass(self):
        summary = self.healthy()
        decision = ag.decide_held_out(summary, self.scores(unanimous=(3, 4)),
                                      self.confirmed(summary), CONFIG)
        self.assertFalse(decision["passed"])
        self.assertTrue(any("spot-check" in reason for reason in decision["reasons"]))

    def test_failure_the_user_says_does_not_matter_blocks_the_pass(self):
        summary = self.healthy()
        confirmed = self.confirmed(summary)
        confirmed["K1"] = False
        decision = ag.decide_held_out(summary, self.scores(), confirmed, CONFIG)
        self.assertFalse(decision["passed"])
        self.assertTrue(any("K1" in reason for reason in decision["reasons"]))

    def test_low_criterion_agreement_blocks_the_pass(self):
        verdicts = units("U1", ["PPP", "PPP", "FFF", "PPP", "FFF"] * 4)
        verdicts += units("K1", ["PPF", "PFF", "PPF", "PFF", "FFF"])
        summary = ag.summarise(verdicts)
        decision = ag.decide_held_out(summary, self.scores(), self.confirmed(summary), CONFIG)
        self.assertFalse(decision["passed"])
        self.assertTrue(any("K1" in reason and "agreement" in reason for reason in decision["reasons"]))


class DecideEdgeTests(unittest.TestCase):
    def scores(self, unanimous=(4, 4)):
        return {"unanimous": {"agree": unanimous[0], "total": unanimous[1]},
                "contested": {"agree": 0, "total": 0}}

    def test_overall_agreement_below_its_threshold_blocks_the_pass_on_its_own(self):
        # One criterion at AC1 0.79: above the per-criterion bar of 0.60, below the overall bar of 0.80.
        summary = ag.summarise(units("K1", ["PPP", "FFF", "PPP", "FFF", "PPF", "PPP"]))
        self.assertTrue(0.6 <= summary["criteria"]["K1"]["ac1"] < 0.8)
        decision = ag.decide_held_out(summary, self.scores(), {"K1": True}, CONFIG)
        self.assertFalse(decision["passed"])
        self.assertEqual(len(decision["reasons"]), 1)
        self.assertIn("overall agreement", decision["reasons"][0])

    def test_no_scored_unanimous_spot_checks_blocks_the_pass(self):
        summary = ag.summarise(units("K1", ["PPP", "PPP", "FFF", "PPP", "FFF"]))
        decision = ag.decide_held_out(summary, self.scores(unanimous=(0, 0)), {"K1": True}, CONFIG)
        self.assertFalse(decision["passed"])
        self.assertTrue(any("no unanimous spot-check" in r for r in decision["reasons"]))


class SpotCheckQuotaTests(unittest.TestCase):
    def test_unanimous_quota_below_the_usability_quota_does_not_overfill_the_set(self):
        config = dict(CONFIG, spot_check={"contested": 0, "unanimous": 2,
                                          "unanimous_usability_passes": 3, "max_per_criterion": 2})
        summary = ag.summarise(units("U1", ["PPP"] * 10) + units("K1", ["PPP"] * 10))
        items, _, _ = ag.select_spot_checks(summary, RUBRIC, config, seed=1)
        self.assertEqual(len(items), 3)

    def test_units_without_a_majority_are_chosen_before_two_to_one_splits(self):
        config = dict(CONFIG, spot_check={"contested": 1, "unanimous": 0,
                                          "unanimous_usability_passes": 0, "max_per_criterion": 2})
        summary = ag.summarise(units("K1", ["PPF", "PF-", "PPF"]))
        for seed in range(5):
            items, sealed, _ = ag.select_spot_checks(summary, RUBRIC, config, seed=seed)
            self.assertIsNone(sealed[items[0]["id"]]["majority"])


class HeldOutCommandTests(unittest.TestCase):
    """The decide and record-held-out commands, run against a temporary repository root."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.run_dir = self.root / "runs" / "test"
        self.run_dir.mkdir(parents=True)
        (self.root / "rubric").mkdir()
        summary = ag.summarise(units("K1", ["PPP", "PPP", "FFF", "PPP", "FFF"]))
        self.write(self.run_dir / "summary.json", summary)
        self.write(self.run_dir / "items.json", {"items": [{"id": "p001", "kind": "prose"}]})
        self.write(self.run_dir / "user-scores.json",
                   {"unanimous": {"agree": 4, "total": 4}, "contested": {"agree": 1, "total": 2}})
        self.write(self.run_dir / "failures-confirmed.json", {"K1": True})
        rubric = {"version": 3, "page_types": ["other"],
                  "criteria": [c for c in RUBRIC["criteria"] if c["id"] == "K1"]}
        self.write(self.root / "rubric" / "rubric.json", rubric)

    def write(self, path, data):
        path.write_text(json.dumps(data), encoding="utf-8")

    def read(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def run_command(self, module, *arguments):
        with contextlib.redirect_stdout(io.StringIO()):
            return module.main(["--root", str(self.root), *arguments])

    def test_unconfirmed_thresholds_refuse_the_decision_and_nothing_is_recorded(self):
        self.write(self.root / "rubric" / "config.json", dict(CONFIG, thresholds_confirmed=False))
        self.assertEqual(self.run_command(ag, "decide", str(self.run_dir)), 1)
        decision = self.read(self.run_dir / "decision.json")
        self.assertTrue(decision["refused"])
        self.assertFalse(decision["passed"])
        recorded = self.run_command(registry, "record-held-out", "acme docs",
                                    "--date", "2026-11-11", "--run", str(self.run_dir))
        self.assertEqual(recorded, 1)
        self.assertFalse((self.root / "rubric" / "held-out.json").exists())

    def test_confirmed_thresholds_decide_and_record_a_pass_for_the_rubric_version(self):
        self.write(self.root / "rubric" / "config.json", CONFIG)
        self.assertEqual(self.run_command(ag, "decide", str(self.run_dir)), 0)
        self.assertTrue(self.read(self.run_dir / "decision.json")["passed"])
        recorded = self.run_command(registry, "record-held-out", "acme docs",
                                    "--date", "2026-11-11", "--run", str(self.run_dir))
        self.assertEqual(recorded, 0)
        result = self.read(self.root / "rubric" / "held-out.json")["results"][0]
        self.assertTrue(result["passed"])
        self.assertEqual(result["version"], 3)
        self.assertEqual(result["input_kinds"], ["prose"])


class IncompleteUnitTests(unittest.TestCase):
    """A unit one evaluator did not judge is neither unanimous nor contested."""

    def summary(self):
        return ag.summarise(units("U1", ["PP-", "PPP", "FFF", "PPP"]))

    def test_two_matching_votes_out_of_three_evaluators_is_not_unanimous(self):
        unit = next(u for u in self.summary()["units"] if u["item"] == "p001")
        self.assertFalse(unit["unanimous"])
        self.assertFalse(unit["contested"])
        self.assertEqual(unit["majority"], "pass")

    def test_incomplete_units_are_counted_per_criterion(self):
        u1 = self.summary()["criteria"]["U1"]
        self.assertEqual(u1["incomplete"], 1)
        self.assertAlmostEqual(u1["unanimous_share"], 0.75)

    def test_incomplete_unit_never_enters_the_spot_check_set(self):
        for seed in range(5):
            items, _, _ = ag.select_spot_checks(self.summary(), RUBRIC, CONFIG, seed=seed)
            self.assertNotIn("p001", [item["item"] for item in items])


if __name__ == "__main__":
    unittest.main()
