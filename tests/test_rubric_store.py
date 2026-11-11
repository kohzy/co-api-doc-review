import copy
import unittest

import support  # noqa: F401
import rubric_store as rs


def criterion(cid, dimension="clarity", question="Is it clear?", page_types=("*",),
              input_kinds=("prose", "pdf-section", "code-comment")):
    return {
        "id": cid,
        "dimension": dimension,
        "applies_to": {"page_types": list(page_types), "input_kinds": list(input_kinds)},
        "question": question,
        "guidance": "Pass when it is.",
        "added_in": 1,
        "status": "active",
    }


def rubric(*criteria):
    return {
        "version": 1,
        "page_types": ["tutorial", "reference", "readme", "other"],
        "criteria": list(criteria),
    }


class ValidateTests(unittest.TestCase):
    def test_valid_rubric_has_no_errors(self):
        self.assertEqual(rs.validate(rubric(criterion("C1"), criterion("C2"))), [])

    def test_duplicate_id_is_rejected_and_named(self):
        errors = rs.validate(rubric(criterion("C1"), criterion("C1")))
        self.assertTrue(any("C1" in e and "duplicate" in e for e in errors), errors)

    def test_question_must_end_with_question_mark(self):
        errors = rs.validate(rubric(criterion("C1", question="It is clear.")))
        self.assertTrue(any("question mark" in e for e in errors), errors)

    def test_dimension_outside_the_three_is_rejected(self):
        errors = rs.validate(rubric(criterion("C1", dimension="coverage")))
        self.assertTrue(any("dimension" in e for e in errors), errors)

    def test_page_type_outside_vocabulary_is_rejected(self):
        errors = rs.validate(rubric(criterion("C1", page_types=("blog-post",))))
        self.assertTrue(any("blog-post" in e for e in errors), errors)

    def test_structure_criterion_may_not_apply_to_code_comments(self):
        errors = rs.validate(rubric(criterion("C1", dimension="structure")))
        self.assertTrue(any("code-comment" in e for e in errors), errors)


class ApplicableTests(unittest.TestCase):
    def setUp(self):
        self.rubric = rubric(
            criterion("C1", dimension="structure", input_kinds=("prose", "pdf-section")),
            criterion("C2", page_types=("tutorial",)),
            criterion("C3"),
        )

    def test_code_comment_item_gets_no_structure_criterion(self):
        ids = [c["id"] for c in rs.applicable(self.rubric, "other", "code-comment")]
        self.assertEqual(ids, ["C3"])

    def test_page_type_filters_criteria(self):
        ids = [c["id"] for c in rs.applicable(self.rubric, "reference", "prose")]
        self.assertEqual(ids, ["C1", "C3"])

    def test_dropped_criteria_never_apply(self):
        self.rubric["criteria"][2]["status"] = "dropped"
        ids = [c["id"] for c in rs.applicable(self.rubric, "tutorial", "prose")]
        self.assertEqual(ids, ["C1", "C2"])


class ApplyChangesTests(unittest.TestCase):
    def setUp(self):
        self.rubric = rubric(criterion("C1"), criterion("C2"), criterion("C3"))

    def test_accepting_two_of_four_changes_bumps_version_once_and_logs_two(self):
        proposed = [
            {"type": "reword", "id": "C1", "question": "Is each sentence clear?",
             "reason": "evaluators split on scope", "evidence": "runs/x/summary.json"},
            {"type": "drop", "id": "C2", "reason": "never fails", "evidence": "runs/x"},
            {"type": "reword", "id": "C3", "question": "Rejected?", "reason": "r", "evidence": "e"},
            {"type": "add", "criterion": criterion("ignored"), "reason": "r", "evidence": "e"},
        ]
        accepted = proposed[:2]
        updated, entries = rs.apply_changes(self.rubric, accepted, "2026-11-11")
        self.assertEqual(updated["version"], 2)
        self.assertEqual(len(entries), 2)
        self.assertTrue(all(e["reason"] and e["version"] == 2 for e in entries))
        by_id = {c["id"]: c for c in updated["criteria"]}
        self.assertEqual(by_id["C1"]["question"], "Is each sentence clear?")
        self.assertEqual(by_id["C2"]["status"], "dropped")
        self.assertEqual(by_id["C3"]["question"], "Is it clear?")
        self.assertEqual(len(updated["criteria"]), 3)

    def test_original_rubric_is_not_mutated(self):
        before = copy.deepcopy(self.rubric)
        rs.apply_changes(self.rubric, [{"type": "drop", "id": "C1", "reason": "r", "evidence": "e"}],
                         "2026-11-11")
        self.assertEqual(self.rubric, before)

    def test_dropped_id_is_not_reused(self):
        dropped, _ = rs.apply_changes(
            self.rubric, [{"type": "drop", "id": "C3", "reason": "r", "evidence": "e"}], "2026-11-11")
        added, _ = rs.apply_changes(dropped, [{
            "type": "add", "reason": "gap found", "evidence": "e",
            "criterion": {"dimension": "clarity", "question": "Is jargon avoided?",
                          "guidance": "g",
                          "applies_to": {"page_types": ["*"], "input_kinds": ["prose"]}},
        }], "2026-11-12")
        ids = [c["id"] for c in added["criteria"]]
        self.assertEqual(ids, ["C1", "C2", "C3", "C4"])
        self.assertEqual(added["criteria"][3]["added_in"], 3)

    def test_split_keeps_original_id_and_gives_new_part_next_id(self):
        updated, entries = rs.apply_changes(self.rubric, [{
            "type": "split", "id": "C2", "reason": "two questions in one", "evidence": "e",
            "keep": {"question": "Are terms defined?"},
            "new": {"question": "Are abbreviations expanded?"},
        }], "2026-11-11")
        by_id = {c["id"]: c for c in updated["criteria"]}
        self.assertEqual(by_id["C2"]["question"], "Are terms defined?")
        self.assertEqual(by_id["C4"]["question"], "Are abbreviations expanded?")
        self.assertEqual(by_id["C4"]["dimension"], by_id["C2"]["dimension"])
        self.assertEqual(entries[0]["ids"], ["C2", "C4"])

    def test_empty_batch_changes_nothing(self):
        updated, entries = rs.apply_changes(self.rubric, [], "2026-11-11")
        self.assertEqual(updated, self.rubric)
        self.assertEqual(entries, [])

    def test_change_without_reason_is_refused(self):
        with self.assertRaises(ValueError):
            rs.apply_changes(self.rubric, [{"type": "drop", "id": "C1", "evidence": "e"}], "2026-11-11")

    def test_change_to_unknown_id_is_refused(self):
        with self.assertRaises(ValueError):
            rs.apply_changes(self.rubric, [{"type": "drop", "id": "C9", "reason": "r", "evidence": "e"}],
                             "2026-11-11")

    def test_change_that_breaks_the_rubric_is_refused(self):
        with self.assertRaises(ValueError):
            rs.apply_changes(self.rubric, [{"type": "reword", "id": "C1", "question": "No mark",
                                            "reason": "r", "evidence": "e"}], "2026-11-11")


class RenderTests(unittest.TestCase):
    def test_render_lists_active_criteria_once_and_omits_dropped(self):
        r = rubric(criterion("C1", question="Is A clear?"), criterion("C2", question="Is B clear?"))
        r["criteria"][1]["status"] = "dropped"
        text = rs.render(r)
        self.assertEqual(text.count("Is A clear?"), 1)
        self.assertNotIn("Is B clear?", text)
        self.assertIn("version 1", text.lower())


if __name__ == "__main__":
    unittest.main()
