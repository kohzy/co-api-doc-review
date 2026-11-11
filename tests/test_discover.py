import tempfile
import unittest
from pathlib import Path

import support
import discover as dc

DOCSET = support.FIXTURES / "docset-mini"


class DiscoverTests(unittest.TestCase):
    def test_fixture_yields_prose_items_and_a_code_comment_item(self):
        items = dc.discover(DOCSET)
        found = {(item["source"], item["kind"], item["page_type"]) for item in items}
        self.assertEqual(found, {
            ("README.md", "prose", "readme"),
            ("docs/reference-build.md", "prose", "reference"),
            ("docs/tutorial-first-widget.md", "prose", "tutorial"),
            ("src/widget.py", "code-comment", "other"),
        })
        self.assertEqual([item["id"] for item in items], ["p001", "p002", "p003", "p004"])

    def test_vendored_and_tooling_directories_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for relative in ("node_modules/pkg/README.md", ".git/notes.md", "docs/guide.md",
                             "build/out.md"):
                target = root / relative
                target.parent.mkdir(parents=True)
                target.write_text("# x\n", encoding="utf-8")
            sources = [item["source"] for item in dc.discover(root)]
        self.assertEqual(sources, ["docs/guide.md"])

    def test_source_file_without_any_comment_is_not_listed(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "bare.py").write_text("x = 1\n", encoding="utf-8")
            (Path(tmp) / "noted.js").write_text("/** Adds. */\nfunction add() {}\n", encoding="utf-8")
            sources = [item["source"] for item in dc.discover(tmp)]
        self.assertEqual(sources, ["noted.js"])

    def test_empty_folder_returns_no_items(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(dc.discover(tmp), [])


class UrlListTests(unittest.TestCase):
    def test_blank_lines_comments_and_duplicates_are_dropped(self):
        text = "https://a.example/one\n\n# a note\nhttps://a.example/two\nhttps://a.example/one\n"
        self.assertEqual(dc.read_url_list(text), ["https://a.example/one", "https://a.example/two"])


class HtmlTextTests(unittest.TestCase):
    def setUp(self):
        self.text = dc.html_to_text((support.FIXTURES / "page.html").read_text(encoding="utf-8"))

    def test_headings_keep_their_levels(self):
        self.assertIn("# Install the CLI", self.text)
        self.assertIn("## Steps", self.text)
        self.assertIn("### Troubleshooting & help", self.text)

    def test_body_text_is_kept(self):
        self.assertIn("You need Python 3.11 or later.", self.text)
        self.assertIn("Run install.sh.", self.text)
        self.assertIn("$ install.sh\ndone", self.text)

    def test_script_and_style_content_is_removed(self):
        self.assertNotIn("tracking", self.text)
        self.assertNotIn("console.log", self.text)
        self.assertNotIn("color: red", self.text)

    def test_page_with_only_scripts_has_no_extractable_text(self):
        html = "<html><body><div id='app'></div><script>render()</script></body></html>"
        self.assertEqual(dc.html_to_text(html), "")


class SliceTests(unittest.TestCase):
    TEXT = "".join(f"line {n}\n" for n in range(1, 11))

    def test_three_starts_give_three_sections_that_rejoin_to_the_original(self):
        sections = dc.slice_text(self.TEXT, [1, 4, 8])
        self.assertEqual(len(sections), 3)
        self.assertEqual("".join(sections), self.TEXT)
        self.assertTrue(sections[1].startswith("line 4\n"))

    def test_starts_must_begin_at_line_one_and_increase(self):
        with self.assertRaises(ValueError):
            dc.slice_text(self.TEXT, [2, 5])
        with self.assertRaises(ValueError):
            dc.slice_text(self.TEXT, [1, 5, 5])


class SampleTests(unittest.TestCase):
    def items(self, **counts):
        result = []
        for page_type, count in counts.items():
            for n in range(count):
                result.append({"id": f"{page_type}{n}", "page_type": page_type, "kind": "prose"})
        return result

    def test_fewer_items_than_the_sample_size_returns_all(self):
        items = self.items(tutorial=2, reference=1)
        self.assertEqual(len(dc.sample(items, 12, seed=1)), 3)

    def test_same_seed_same_sample_and_another_seed_can_differ(self):
        items = self.items(tutorial=10, reference=10, other=10)
        first = [i["id"] for i in dc.sample(items, 6, seed=1)]
        self.assertEqual(first, [i["id"] for i in dc.sample(items, 6, seed=1)])
        others = {tuple(i["id"] for i in dc.sample(items, 6, seed=s)) for s in range(2, 8)}
        self.assertTrue(any(other != tuple(first) for other in others))

    def test_sample_is_spread_across_page_types(self):
        items = self.items(tutorial=20, reference=2, other=2)
        chosen = dc.sample(items, 6, seed=3)
        types = [i["page_type"] for i in chosen]
        self.assertEqual(types.count("reference"), 2)
        self.assertEqual(types.count("other"), 2)
        self.assertEqual(types.count("tutorial"), 2)

    def test_source_file_cap_limits_code_comment_items_only(self):
        items = self.items(tutorial=3)
        items += [{"id": f"c{n}", "page_type": "other", "kind": "code-comment"} for n in range(9)]
        kept = dc.cap_source_files(items, 4, seed=1)
        self.assertEqual(sum(1 for i in kept if i["kind"] == "code-comment"), 4)
        self.assertEqual(sum(1 for i in kept if i["kind"] == "prose"), 3)


if __name__ == "__main__":
    unittest.main()
