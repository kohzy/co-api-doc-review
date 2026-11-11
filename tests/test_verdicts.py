import unittest

import support  # noqa: F401
import verdicts as vd

SNAPSHOT = """# Install

Run the installer,
then restart   the service.

You need Python 3.11 or later.
"""

ITEM = {"id": "p001", "criteria": ["C1", "C2"]}


def verdict(**overrides):
    base = {"item": "p001", "criterion": "C1", "verdict": "pass",
            "evidence": {"quote": "You need Python 3.11 or later."}}
    base.update(overrides)
    return base


class ValidateVerdictTests(unittest.TestCase):
    def test_exact_quote_is_accepted(self):
        self.assertIsNone(vd.verdict_problem(verdict(), ITEM, SNAPSHOT))

    def test_quote_with_different_line_wrapping_is_accepted(self):
        v = verdict(evidence={"quote": "Run the installer, then restart the service."})
        self.assertIsNone(vd.verdict_problem(v, ITEM, SNAPSHOT))

    def test_quote_not_in_snapshot_is_rejected(self):
        v = verdict(evidence={"quote": "Run the uninstaller."})
        self.assertIn("not found", vd.verdict_problem(v, ITEM, SNAPSHOT))

    def test_empty_quote_is_rejected(self):
        v = verdict(evidence={"quote": "   "})
        self.assertIsNotNone(vd.verdict_problem(v, ITEM, SNAPSHOT))

    def test_fail_with_no_evidence_is_rejected(self):
        v = verdict(verdict="fail", evidence={})
        self.assertIn("evidence", vd.verdict_problem(v, ITEM, SNAPSHOT))

    def test_absence_record_is_accepted(self):
        v = verdict(verdict="fail", evidence={"absent": {
            "looked_for": "a list of prerequisites", "searched": "whole page"}})
        self.assertIsNone(vd.verdict_problem(v, ITEM, SNAPSHOT))

    def test_absence_record_missing_what_was_looked_for_is_rejected(self):
        v = verdict(verdict="fail", evidence={"absent": {"looked_for": "", "searched": "whole page"}})
        self.assertIn("looked_for", vd.verdict_problem(v, ITEM, SNAPSHOT))

    def test_verdict_other_than_pass_or_fail_is_rejected(self):
        self.assertIn("pass or fail", vd.verdict_problem(verdict(verdict="not-applicable"), ITEM, SNAPSHOT))

    def test_criterion_that_does_not_apply_to_the_item_is_rejected(self):
        self.assertIn("does not apply", vd.verdict_problem(verdict(criterion="C9"), ITEM, SNAPSHOT))


class ValidateFileTests(unittest.TestCase):
    def test_invalid_verdicts_are_separated_and_counted(self):
        submitted = {"evaluator": "newcomer", "verdicts": [
            verdict(),
            verdict(criterion="C2", evidence={"quote": "This sentence is invented."}),
            verdict(item="p404"),
        ]}
        valid, invalid = vd.validate_verdicts(submitted, {"p001": ITEM}, {"p001": SNAPSHOT})
        self.assertEqual(len(valid), 1)
        self.assertEqual(len(invalid), 2)
        self.assertTrue(all("problem" in entry for entry in invalid))

    def test_duplicate_verdict_for_same_item_and_criterion_is_rejected(self):
        submitted = {"evaluator": "newcomer", "verdicts": [verdict(), verdict(verdict="fail")]}
        valid, invalid = vd.validate_verdicts(submitted, {"p001": ITEM}, {"p001": SNAPSHOT})
        self.assertEqual(len(valid), 1)
        self.assertIn("duplicate", invalid[0]["problem"])


class MalformedEvidenceTests(unittest.TestCase):
    def test_absence_record_missing_where_it_searched_is_rejected(self):
        v = verdict(verdict="fail", evidence={"absent": {"looked_for": "prerequisites", "searched": ""}})
        self.assertIn("searched", vd.verdict_problem(v, ITEM, SNAPSHOT))

    def test_evidence_that_is_plain_text_is_rejected_not_raised(self):
        v = verdict(evidence="the quote is You need Python 3.11 or later.")
        self.assertIn("evidence", vd.verdict_problem(v, ITEM, SNAPSHOT))

    def test_absence_record_that_is_plain_text_is_rejected_not_raised(self):
        v = verdict(verdict="fail", evidence={"absent": "no prerequisites anywhere"})
        self.assertIn("looked_for", vd.verdict_problem(v, ITEM, SNAPSHOT))

    def test_null_quote_is_rejected_even_when_the_page_contains_the_word_none(self):
        v = verdict(evidence={"quote": None})
        self.assertIsNotNone(vd.verdict_problem(v, ITEM, SNAPSHOT + "None of this applies.\n"))

    def test_one_malformed_verdict_does_not_stop_the_others_being_validated(self):
        submitted = {"evaluator": "newcomer", "verdicts": [
            "not an object", verdict(evidence={"absent": "text"}), verdict()]}
        valid, invalid = vd.validate_verdicts(submitted, {"p001": ITEM}, {"p001": SNAPSHOT})
        self.assertEqual(len(valid), 1)
        self.assertEqual(len(invalid), 2)


class MissingVerdictTests(unittest.TestCase):
    def test_criteria_nobody_judged_are_listed(self):
        valid = [dict(verdict(), evaluator="batch1")]
        self.assertEqual(vd.missing_verdicts({"p001": ITEM}, valid), [("p001", "C2")])

    def test_nothing_is_missing_when_every_criterion_has_a_verdict(self):
        valid = [dict(verdict(), evaluator="b"), dict(verdict(criterion="C2"), evaluator="b")]
        self.assertEqual(vd.missing_verdicts({"p001": ITEM}, valid), [])


if __name__ == "__main__":
    unittest.main()
