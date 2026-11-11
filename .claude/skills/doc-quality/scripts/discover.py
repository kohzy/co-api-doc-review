#!/usr/bin/env python3
"""Find what can be evaluated in a folder, a list of URLs, or a PDF's text,
label each item with its input kind and a first guess at its page type, and
draw a reproducible sample.

Every item gets a snapshot: the text evaluators read and quotes are checked
against. Local files are their own snapshot. URLs are fetched once and saved.
"""
import argparse
import random
import re
import shutil
import subprocess
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

from rubric_store import read_json, write_json

PROSE_SUFFIXES = {".md", ".mdx", ".rst", ".adoc"}
SOURCE_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".java", ".rb", ".rs", ".c", ".h",
                   ".cpp", ".cs", ".php", ".swift", ".kt"}
SKIPPED_DIRS = {".git", ".hg", ".svn", "node_modules", "vendor", "dist", "build", "target",
                ".venv", "venv", "__pycache__", ".next", ".tox", "site-packages"}
COMMENT = re.compile(r'"""|\'\'\'|/\*\*|^\s*(#(?!!)|//)\s?\w', re.MULTILINE)

PAGE_TYPE_WORDS = (
    ("readme", {"readme"}),
    ("quickstart", {"quickstart", "getting", "started"}),
    ("tutorial", {"tutorial", "tutorials"}),
    ("how-to", {"howto", "how", "guide", "guides", "recipe", "recipes"}),
    ("reference", {"reference", "api", "cli"}),
    ("explanation", {"concept", "concepts", "explanation", "architecture", "overview", "about"}),
    ("landing", {"index"}),
)


def guess_page_type(path_text):
    """A first guess from the path alone; the skill confirms the type after reading the page."""
    parts = [p for p in re.split(r"[\\/]", path_text.lower()) if p]
    for part in reversed(parts):
        words = set(re.split(r"[^a-z0-9]+", part.rsplit(".", 1)[0]))
        for page_type, markers in PAGE_TYPE_WORDS:
            if words & markers:
                return page_type
    return "other"


def _item(number, kind, page_type, source, snapshot):
    return {"id": f"p{number:03d}", "kind": kind, "page_type": page_type,
            "source": source, "snapshot": snapshot}


def discover(root):
    """List prose documentation and commented source files under a folder."""
    root = Path(root).resolve()
    found = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in SKIPPED_DIRS for part in relative.parts[:-1]):
            continue
        suffix = path.suffix.lower()
        if suffix in PROSE_SUFFIXES or path.name.lower().startswith("readme"):
            found.append(("prose", guess_page_type(relative.as_posix()), relative, path))
        elif suffix in SOURCE_SUFFIXES:
            if COMMENT.search(path.read_text(encoding="utf-8", errors="replace")):
                found.append(("code-comment", "other", relative, path))
    return [_item(n, kind, page_type, relative.as_posix(), str(path))
            for n, (kind, page_type, relative, path) in enumerate(found, start=1)]


def read_url_list(text):
    """Distinct URLs in file order, ignoring blank lines and lines starting with #."""
    urls = []
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and line not in urls:
            urls.append(line)
    return urls


class _TextExtractor(HTMLParser):
    SKIPPED = {"script", "style", "noscript", "template", "svg", "head", "nav", "footer"}
    BLOCKS = {"p", "div", "section", "article", "ul", "ol", "table", "tr", "blockquote", "dl",
              "dt", "dd", "figure", "main", "header", "aside"}
    HEADINGS = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}

    def __init__(self):
        super().__init__()
        self.out = []
        self.skip_depth = 0
        self.pre_depth = 0

    def _break(self, count=1):
        while self.out and self.out[-1].endswith((" ", "\t")):
            self.out[-1] = self.out[-1].rstrip(" \t")
        self.out.append("\n" * count)

    def _at_line_start(self):
        return not self.out or self.out[-1].endswith("\n")

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIPPED:
            self.skip_depth += 1
        if self.skip_depth:
            return
        if tag in self.HEADINGS:
            self._break(2)
            self.out.append("#" * self.HEADINGS[tag] + " ")
        elif tag == "li":
            self._break()
            self.out.append("- ")
        elif tag == "pre":
            self._break(2)
            self.pre_depth += 1
        elif tag == "br":
            self._break()
        elif tag in self.BLOCKS:
            self._break(2)

    def handle_endtag(self, tag):
        if tag in self.SKIPPED:
            self.skip_depth = max(0, self.skip_depth - 1)
            return
        if self.skip_depth:
            return
        if tag == "pre":
            self.pre_depth = max(0, self.pre_depth - 1)
            self._break(2)
        elif tag in self.HEADINGS or tag in self.BLOCKS or tag == "li":
            self._break(2 if tag != "li" else 1)

    def handle_data(self, data):
        if self.skip_depth:
            return
        if self.pre_depth:
            self.out.append(data)
            return
        text = re.sub(r"\s+", " ", data)
        if self._at_line_start():
            text = text.lstrip()
        if text:
            self.out.append(text)


def html_to_text(html):
    """Readable text from an HTML page, keeping heading levels; empty when there is none."""
    parser = _TextExtractor()
    parser.feed(html)
    parser.close()
    text = "".join(parser.out)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text + "\n" if text else ""


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "doc-quality-skill"})
    with urllib.request.urlopen(request, timeout=30) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def snapshot_urls(urls, run_dir):
    """Fetch each URL once, save its HTML and extracted text, and return the items."""
    pages = Path(run_dir) / "pages"
    pages.mkdir(parents=True, exist_ok=True)
    items = []
    for number, url in enumerate(urls, start=1):
        html = fetch(url)
        text = html_to_text(html)
        if not text:
            raise ValueError(f"no text could be extracted from {url}; "
                             "the page may be rendered by JavaScript")
        name = f"p{number:03d}"
        (pages / f"{name}.html").write_text(html, encoding="utf-8")
        (pages / f"{name}.txt").write_text(text, encoding="utf-8")
        path = urlsplit(url).path or "/"
        page_type = "landing" if path.strip("/") == "" else guess_page_type(path)
        items.append(_item(number, "prose", page_type, url, f"pages/{name}.txt"))
    return items


def pdf_text(path):
    """Text of a PDF from pdftotext, or None when pdftotext is not installed."""
    tool = shutil.which("pdftotext")
    if not tool:
        return None
    done = subprocess.run([tool, "-layout", str(path), "-"], capture_output=True, text=True,
                          check=True)
    return done.stdout


def slice_text(text, starts):
    """Cut text into sections beginning at the given 1-based line numbers."""
    if not starts or starts[0] != 1 or any(b <= a for a, b in zip(starts, starts[1:])):
        raise ValueError("section starts must begin at line 1 and strictly increase")
    lines = text.splitlines(keepends=True)
    if starts[-1] > len(lines):
        raise ValueError(f"section start {starts[-1]} is past the last line ({len(lines)})")
    bounds = [s - 1 for s in starts] + [len(lines)]
    return ["".join(lines[a:b]) for a, b in zip(bounds, bounds[1:])]


def snapshot_sections(text, starts, run_dir, source):
    pages = Path(run_dir) / "pages"
    pages.mkdir(parents=True, exist_ok=True)
    items = []
    for number, section in enumerate(slice_text(text, starts), start=1):
        name = f"p{number:03d}"
        (pages / f"{name}.txt").write_text(section, encoding="utf-8")
        items.append(_item(number, "pdf-section", "other", f"{source} section {number}",
                           f"pages/{name}.txt"))
    return items


def sample(items, size, seed):
    """Up to `size` items, spread evenly across page types, in their original order."""
    if len(items) <= size:
        return list(items)
    rng = random.Random(seed)
    groups = {}
    for item in items:
        groups.setdefault(item["page_type"], []).append(item)
    for page_type in sorted(groups):
        rng.shuffle(groups[page_type])
    chosen = []
    while len(chosen) < size:
        for page_type in sorted(groups):
            if groups[page_type] and len(chosen) < size:
                chosen.append(groups[page_type].pop())
    order = {id(item): index for index, item in enumerate(items)}
    return sorted(chosen, key=lambda item: order[id(item)])


def cap_source_files(items, cap, seed):
    """Keep every prose item and at most `cap` code-comment items, chosen by seed."""
    code = [item for item in items if item["kind"] == "code-comment"]
    if len(code) <= cap:
        return list(items)
    kept = {id(item) for item in random.Random(seed).sample(code, cap)}
    return [item for item in items if item["kind"] != "code-comment" or id(item) in kept]


def _write_items(run_dir, items, seed, found):
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    counts = {}
    for item in found:
        counts[item["kind"]] = counts.get(item["kind"], 0) + 1
    write_json(run_dir / "items.json", {"seed": seed, "found": counts, "items": items})
    kinds = ", ".join(f"{n} {kind}" for kind, n in sorted(counts.items())) or "nothing"
    print(f"found {kinds}; {len(items)} items written to {run_dir / 'items.json'}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("folder", help="list documentation in a folder or repository")
    p.add_argument("path")
    p.add_argument("--run", required=True)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--sample", type=int, help="sample this many items across page types")
    p.add_argument("--source-cap", type=int, help="keep at most this many source files")
    p = sub.add_parser("urls", help="fetch and snapshot the pages in a URL list file")
    p.add_argument("path")
    p.add_argument("--run", required=True)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--sample", type=int)
    p = sub.add_parser("pdf-text", help="extract a PDF's text with pdftotext")
    p.add_argument("path")
    p.add_argument("--out", required=True)
    p = sub.add_parser("sections", help="cut a text file into section snapshots")
    p.add_argument("path")
    p.add_argument("--starts", required=True, help="comma-separated 1-based line numbers")
    p.add_argument("--run", required=True)
    p.add_argument("--source", required=True, help="name of the document, for the report")
    p = sub.add_parser("set-types", help="record the final page type of items, as ID=TYPE")
    p.add_argument("run")
    p.add_argument("assignments", nargs="+")
    args = parser.parse_args(argv)

    if args.command == "folder":
        found = discover(args.path)
        if not found:
            print(f"no documentation found under {args.path}")
            return 1
        items = found
        if args.source_cap is not None:
            items = cap_source_files(items, args.source_cap, args.seed)
        if args.sample is not None:
            items = sample(items, args.sample, args.seed)
        _write_items(args.run, items, args.seed, found)
    elif args.command == "urls":
        urls = read_url_list(Path(args.path).read_text(encoding="utf-8"))
        if not urls:
            print(f"no URLs found in {args.path}")
            return 1
        chosen = urls
        if args.sample is not None and len(urls) > args.sample:
            picked = set(random.Random(args.seed).sample(range(len(urls)), args.sample))
            chosen = [url for index, url in enumerate(urls) if index in picked]
        items = snapshot_urls(chosen, args.run)
        _write_items(args.run, items, args.seed,
                     [{"kind": "prose"} for _ in urls])
    elif args.command == "pdf-text":
        text = pdf_text(args.path)
        if text is None:
            print("pdftotext is not installed; transcribe the PDF with the host's PDF reading instead")
            return 3
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {len(text.splitlines())} lines to {args.out}")
    elif args.command == "sections":
        text = Path(args.path).read_text(encoding="utf-8")
        starts = [int(s) for s in args.starts.split(",")]
        items = snapshot_sections(text, starts, args.run, args.source)
        _write_items(args.run, items, 0, items)
    elif args.command == "set-types":
        path = Path(args.run) / "items.json"
        data = read_json(path)
        by_id = {item["id"]: item for item in data["items"]}
        for assignment in args.assignments:
            item_id, _, page_type = assignment.partition("=")
            if item_id not in by_id or not page_type:
                print(f"cannot apply {assignment}: expected ID=TYPE for an item in this run")
                return 1
            by_id[item_id]["page_type"] = page_type
        write_json(path, data)
        print(f"set the page type of {len(args.assignments)} items")
    return 0


if __name__ == "__main__":
    sys.exit(main())
