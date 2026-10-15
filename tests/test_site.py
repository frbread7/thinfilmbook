import html.parser
import copy
import io
import json
from pathlib import Path
import posixpath
import tempfile
import sys
from contextlib import redirect_stderr
from unittest.mock import patch
import unittest
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
sys.path.insert(0, str(ROOT / "tools"))
import build_site


class Links(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.resources = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        for attribute in ("href", "src"):
            value = attrs.get(attribute)
            if value:
                self.resources.append(value)


def parsed(path):
    parser = Links()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


class ThinFilmBookSiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "library-manifest.json").read_text(encoding="utf-8"))
        cls.chapters = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted((ROOT / "content" / "chapters").glob("c*.json"))
        ]
        cls.labs = json.loads((ROOT / "content" / "labs.json").read_text(encoding="utf-8"))["experiments"]

    def test_candidate_is_complete_bilingual_and_not_published(self):
        self.assertEqual(self.manifest["status"], "in-progress")
        self.assertEqual(self.manifest["version"], "0.1.0")
        self.assertEqual(self.manifest["chapterCount"], 12)
        self.assertEqual(len(self.manifest["chapters"]), 12)
        self.assertEqual(len(self.manifest["experiments"]), 3)
        self.assertEqual(self.manifest["languages"], ["en", "ko"])
        self.assertNotIn("repositoryUrl", self.manifest)
        self.assertNotIn("productionUrl", self.manifest)
        self.assertNotIn("languageUrls", self.manifest)
        self.assertFalse(self.manifest.get("publicationEvidence"))
        self.assertFalse(self.manifest.get("releaseDate"))

    def test_chapter_source_has_both_complete_editions_and_known_citations(self):
        self.assertEqual(len(self.chapters), 12)
        refs = {
            item["id"]
            for item in json.loads((ROOT / "content" / "references.json").read_text(encoding="utf-8"))["references"]
        }
        for number, chapter in enumerate(self.chapters, 1):
            with self.subTest(chapter=number):
                self.assertEqual(chapter["number"], number)
                for language in ("en", "ko"):
                    self.assertEqual(len(chapter["sections"][language]), 4)
                    self.assertGreaterEqual(len(chapter["objectives"][language]), 3)
                    self.assertGreaterEqual(len(chapter["questions"][language]), 3)
                    self.assertTrue(chapter["workedExample"][language].strip())
                self.assertLessEqual(set(chapter["references"]), refs)

    def test_all_local_resources_and_fragments_resolve(self):
        pages = sorted(SITE.rglob("*.html"))
        self.assertEqual(len(pages), 32)
        html_cache = {}
        for page in pages:
            source = page.relative_to(SITE).as_posix()
            parser = parsed(page)
            for value in parser.resources:
                parts = urlsplit(value)
                if parts.scheme or parts.netloc or value.startswith("data:"):
                    continue
                target = posixpath.normpath(posixpath.join(posixpath.dirname(source), unquote(parts.path))) if parts.path else source
                target_path = SITE / target
                with self.subTest(page=source, resource=value):
                    self.assertTrue(target_path.is_file(), f"missing local resource {target}")
                    if parts.fragment and target_path.suffix == ".html":
                        if target not in html_cache:
                            html_cache[target] = parsed(target_path).ids
                        self.assertIn(unquote(parts.fragment), html_cache[target], f"missing fragment in {target}")

    def test_every_declared_lab_has_bilingual_anchor_and_controls(self):
        for language, prefix in (("en", ""), ("ko", "ko/")):
            page = SITE / f"{prefix}lab.html"
            parser = parsed(page)
            for lab in self.labs:
                with self.subTest(language=language, lab=lab["id"]):
                    self.assertIn(lab["id"], parser.ids)
            source = page.read_text(encoding="utf-8")
            self.assertIn("run-ald", source)
            self.assertIn("run-cvd", source)
            self.assertIn("run-stoney", source)
            self.assertIn('aria-live="polite"', source)

    def test_language_switches_and_citations_are_emitted(self):
        english = parsed(SITE / "chapters" / "07-ald.html")
        korean = parsed(SITE / "ko" / "chapters" / "07-ald.html")
        self.assertIn("../ko/chapters/07-ald.html", english.resources)
        self.assertIn("../../chapters/07-ald.html", korean.resources)
        self.assertTrue(any("references.html#ref-r" in link for link in english.resources))
        self.assertTrue(any("references.html#ref-r" in link for link in korean.resources))

    def test_generated_pages_have_no_remote_runtime_dependencies(self):
        for page in SITE.rglob("*.html"):
            with self.subTest(page=page.relative_to(SITE).as_posix()):
                parser = parsed(page)
                remote_scripts = [url for url in parser.resources if url.startswith(("http://", "https://")) and url.endswith((".js", ".mjs"))]
                self.assertEqual(remote_scripts, [])

    def test_generated_pages_have_no_trailing_whitespace(self):
        for page in SITE.rglob("*.html"):
            with self.subTest(page=page.relative_to(SITE).as_posix()):
                lines = page.read_text(encoding="utf-8").splitlines()
                self.assertTrue(all(line == line.rstrip() for line in lines))

    def test_reference_ids_reject_html_attribute_injection(self):
        chapters, references, labs, ui, pages = build_site.load_data()
        malformed = copy.deepcopy(references)
        malformed["references"][0]["id"] = 'r01" onmouseover="alert(1)'
        with self.assertRaisesRegex(ValueError, "reference ID is invalid"):
            build_site.validate_content(chapters, malformed, labs, ui, pages)

    def test_generated_site_comparison_detects_stale_and_unexpected_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            expected = Path(temporary) / "expected"
            actual = Path(temporary) / "actual"
            expected.mkdir()
            actual.mkdir()
            (expected / "index.html").write_text("current", encoding="utf-8")
            (actual / "index.html").write_text("current", encoding="utf-8")
            self.assertEqual(build_site.compare_sites(expected, actual), [])

            (actual / "index.html").write_text("stale", encoding="utf-8")
            (actual / "extra.txt").write_text("unexpected", encoding="utf-8")
            self.assertEqual(
                build_site.compare_sites(expected, actual),
                ["unexpected: extra.txt", "stale or modified: index.html"],
            )

    def test_check_command_rejects_a_stale_generated_site(self):
        with tempfile.TemporaryDirectory() as temporary:
            stale_site = Path(temporary)
            (stale_site / "000-stale.html").write_text("old output", encoding="utf-8")
            error = io.StringIO()
            with patch.object(build_site, "SITE", stale_site), patch.object(sys, "argv", ["build_site.py", "--check"]), redirect_stderr(error):
                self.assertEqual(build_site.main(), 1)
            self.assertIn("generated site differs from current sources", error.getvalue())
            self.assertIn("unexpected: 000-stale.html", error.getvalue())


if __name__ == "__main__":
    unittest.main()
