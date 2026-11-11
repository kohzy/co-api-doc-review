import unittest

import support
import rubric_store as rs

RUBRIC_DIR = support.REPO / "rubric"


class SeedRubricTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rubric = rs.read_json(RUBRIC_DIR / "rubric.json")

    def active(self, dimension=None):
        return [c for c in self.rubric["criteria"] if c["status"] == "active"
                and (dimension is None or c["dimension"] == dimension)]

    def test_rubric_passes_validation(self):
        self.assertEqual(rs.validate(self.rubric), [])

    def test_every_dimension_has_at_least_four_active_criteria(self):
        for dimension in rs.DIMENSIONS:
            self.assertGreaterEqual(len(self.active(dimension)), 4, dimension)

    def test_page_types_cover_diataxis_and_the_mixed_types(self):
        for page_type in ("tutorial", "how-to", "reference", "explanation",
                          "readme", "quickstart", "landing", "other"):
            self.assertIn(page_type, self.rubric["page_types"])

    def test_no_structure_criterion_applies_to_code_comments(self):
        applied = rs.applicable(self.rubric, "other", "code-comment")
        self.assertTrue(applied)
        self.assertFalse([c["id"] for c in applied if c["dimension"] == "structure"])

    def test_single_type_criterion_spares_readmes_quickstarts_and_landing_pages(self):
        single = [c for c in self.active("structure") if "one job" in c["question"]]
        self.assertEqual(len(single), 1)
        types = single[0]["applies_to"]["page_types"]
        for mixed in ("readme", "quickstart", "landing"):
            self.assertNotIn(mixed, types)
            self.assertNotIn(single[0]["id"],
                             [c["id"] for c in rs.applicable(self.rubric, mixed, "prose")])
        self.assertIn(single[0]["id"],
                      [c["id"] for c in rs.applicable(self.rubric, "tutorial", "prose")])

    def test_every_criterion_has_guidance(self):
        for criterion in self.active():
            self.assertTrue(criterion["guidance"].strip(), criterion["id"])

    def test_rendered_rubric_is_current(self):
        rendered = (RUBRIC_DIR / "RUBRIC.md").read_text(encoding="utf-8")
        self.assertEqual(rendered, rs.render(self.rubric))


if __name__ == "__main__":
    unittest.main()
