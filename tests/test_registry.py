import subprocess
import tempfile
import unittest
from pathlib import Path

import support  # noqa: F401
import registry as reg


class IdentityTests(unittest.TestCase):
    def test_remote_spellings_resolve_to_one_identity(self):
        forms = [
            "https://GitHub.com/Acme/Docs.git",
            "https://github.com/acme/docs",
            "git@github.com:acme/docs.git",
            "https://github.com/acme/docs/",
        ]
        self.assertEqual({reg.normalise_identity(f) for f in forms}, {"github.com/acme/docs"})

    def test_site_url_resolves_to_its_origin(self):
        self.assertEqual(reg.normalise_identity("https://Docs.Example.com/guide/start?x=1"),
                         "docs.example.com")

    def test_plain_name_is_lowercased_and_trimmed(self):
        self.assertEqual(reg.normalise_identity("  Acme Docs "), "acme docs")


class IdentifyTests(unittest.TestCase):
    def repo(self, tmp):
        root = Path(tmp) / "checkout"
        (root / "docs").mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        subprocess.run(["git", "-C", str(root), "remote", "add", "origin",
                        "https://github.com/Acme/Product.git"], check=True)
        return root

    def test_repository_root_is_identified_by_its_remote(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(reg.identify(str(self.repo(tmp))), "github.com/acme/product")

    def test_subfolder_of_a_repository_is_identified_by_remote_and_subpath(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.repo(tmp)
            self.assertEqual(reg.identify(str(root / "docs")), "github.com/acme/product/docs")

    def test_folder_outside_any_repository_is_identified_by_its_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "Vendor Docs"
            folder.mkdir()
            self.assertEqual(reg.identify(str(folder)), "vendor docs")

    def test_url_list_file_is_identified_by_the_origin_of_its_first_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            listing = Path(tmp) / "urls.txt"
            listing.write_text("\nhttps://docs.example.com/start\n", encoding="utf-8")
            self.assertEqual(reg.identify(str(listing)), "docs.example.com")


class SeenTests(unittest.TestCase):
    def setUp(self):
        self.seen = {"doc_sets": []}

    def test_unrecorded_doc_set_is_unseen(self):
        self.assertIsNone(reg.seen_entry(self.seen, "github.com/acme/docs"))
        self.assertIsNone(reg.held_out_refusal(self.seen, "https://github.com/acme/docs"))

    def test_doc_set_used_for_refinement_is_refused_as_held_out(self):
        reg.record_use(self.seen, "https://github.com/acme/docs.git", "refine-rubric",
                       "2026-11-11", "runs/a")
        reason = reg.held_out_refusal(self.seen, "git@github.com:acme/docs.git")
        self.assertIn("seen", reason)
        self.assertIn("refine-rubric", reason)

    def test_doc_set_used_for_held_out_is_refused_a_second_time(self):
        reg.record_use(self.seen, "acme docs", "held-out", "2026-11-11", "runs/a")
        self.assertIn("held-out", reg.held_out_refusal(self.seen, "Acme Docs"))

    def test_recording_twice_keeps_both_uses_under_one_identity(self):
        reg.record_use(self.seen, "acme docs", "refine-rubric", "2026-11-11", "runs/a")
        reg.record_use(self.seen, "Acme Docs", "refine-rubric", "2026-11-12", "runs/b")
        self.assertEqual(len(self.seen["doc_sets"]), 1)
        self.assertEqual(len(self.seen["doc_sets"][0]["uses"]), 2)


class HeaderFactsTests(unittest.TestCase):
    def changelog(self, *versions):
        return [{"version": v, "type": "reword"} for v in versions]

    def test_no_passing_version_on_record(self):
        facts = reg.header_facts(2, self.changelog(2), {"results": []})
        self.assertIsNone(facts["last_passed_version"])
        self.assertIsNone(facts["changes_since_pass"])
        self.assertEqual(facts["coverage"],
                         {"prose": False, "pdf-section": False, "code-comment": False})

    def test_failed_held_out_result_is_not_a_pass(self):
        held = {"results": [{"version": 2, "passed": False, "input_kinds": ["prose"],
                             "not_tested": []}]}
        self.assertIsNone(reg.header_facts(2, self.changelog(2), held)["last_passed_version"])

    def test_last_passed_version_and_changes_since(self):
        held = {"results": [{"version": 3, "passed": True, "input_kinds": ["prose"],
                             "not_tested": []}]}
        facts = reg.header_facts(5, self.changelog(2, 3, 4, 5), held)
        self.assertEqual(facts["current_version"], 5)
        self.assertEqual(facts["last_passed_version"], 3)
        self.assertEqual(facts["changes_since_pass"], 2)

    def test_pass_on_prose_only_leaves_code_comments_uncovered(self):
        held = {"results": [{"version": 1, "passed": True, "input_kinds": ["prose"],
                             "not_tested": []}]}
        coverage = reg.header_facts(1, [], held)["coverage"]
        self.assertTrue(coverage["prose"])
        self.assertFalse(coverage["code-comment"])
        self.assertFalse(coverage["pdf-section"])

    def test_held_out_result_carries_untested_criteria_into_header(self):
        held = {"results": []}
        reg.record_held_out(held, version=1, date="2026-11-11", doc_set="acme docs", passed=True,
                            measures={"overall_ac1": 0.9}, input_kinds=["prose"],
                            not_tested=["C8"], reasons=[])
        self.assertEqual(held["results"][0]["not_tested"], ["C8"])
        self.assertEqual(reg.header_facts(1, [], held)["not_tested"], ["C8"])

    def test_most_recent_passing_version_wins(self):
        held = {"results": [
            {"version": 1, "passed": True, "input_kinds": ["prose"], "not_tested": []},
            {"version": 4, "passed": True, "input_kinds": ["prose", "code-comment"],
             "not_tested": []},
        ]}
        facts = reg.header_facts(4, self.changelog(2, 3, 4), held)
        self.assertEqual(facts["last_passed_version"], 4)
        self.assertEqual(facts["changes_since_pass"], 0)
        self.assertTrue(facts["coverage"]["code-comment"])


class UrlListIdentityTests(unittest.TestCase):
    def identity(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            listing = Path(tmp) / "urls.txt"
            listing.write_text(text, encoding="utf-8")
            return reg.identify(str(listing))

    def test_leading_comment_line_is_not_the_identity(self):
        self.assertEqual(self.identity("# Acme docs\nhttps://docs.acme.example/start\n"),
                         "docs.acme.example")

    def test_lists_with_the_same_comment_and_different_hosts_differ(self):
        first = self.identity("# Product docs\nhttps://one.example/a\n")
        second = self.identity("# Product docs\nhttps://two.example/a\n")
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
