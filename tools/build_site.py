#!/usr/bin/env python3
"""Validate ThinFilmBook source and build its dependency-free static site."""
from __future__ import annotations

import argparse
from datetime import date
from html import escape
import json
from pathlib import Path
import posixpath
import re
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
LANGUAGES = ("en", "ko")
PLANNED_ROUTE_BASE = "https://frbread7.github.io/thinfilmbook/"
EXPECTED_GROUPS = {
    1: "g1", 2: "g1", 3: "g2", 4: "g2", 5: "g3", 6: "g3",
    7: "g3", 8: "g4", 9: "g5", 10: "g5", 11: "g6", 12: "g6",
}
CITATION = re.compile(r"\[\s*\[?(r\d{2})\]?\s*\]")
SAFE_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SAFE_REFERENCE_ID = re.compile(r"^r\d{2}$")


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {path.relative_to(ROOT)}: {exc}") from exc


def text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")


def localized(record, label):
    if not isinstance(record, dict) or set(record) != set(LANGUAGES):
        raise ValueError(f"{label} must provide exactly en and ko")
    for lang in LANGUAGES:
        text(record[lang], f"{label}.{lang}")


def load_data():
    chapters = [read_json(ROOT / "content" / "chapters" / f"c{number:02d}.json") for number in range(1, 13)]
    references = read_json(ROOT / "content" / "references.json")
    labs = read_json(ROOT / "content" / "labs.json")
    ui = read_json(ROOT / "content" / "ui.json")
    pages = read_json(ROOT / "content" / "pages.json")
    validate_content(chapters, references, labs, ui, pages)
    return chapters, references, labs, ui, pages


def validate_content(chapters, references, labs, ui, pages):
    if len(chapters) != 12 or [item.get("number") for item in chapters] != list(range(1, 13)):
        raise ValueError("exactly twelve sequential chapters are required")
    chapter_ids = set()
    for number, chapter in enumerate(chapters, 1):
        if chapter.get("schemaVersion") != 1 or chapter.get("number") != number:
            raise ValueError(f"chapter {number}: schema version or number is invalid")
        localized(chapter.get("title"), f"chapter {number} title")
        localized(chapter.get("summary"), f"chapter {number} summary")
        if chapter.get("group") != EXPECTED_GROUPS[number]:
            raise ValueError(f"chapter {number}: unexpected editorial group")
        if not SAFE_SLUG.fullmatch(chapter.get("slug", "")):
            raise ValueError(f"chapter {number}: slug is invalid")
        chapter_id = chapter.get("id")
        if not isinstance(chapter_id, str) or chapter_id in chapter_ids:
            raise ValueError(f"chapter {number}: missing or duplicate id")
        chapter_ids.add(chapter_id)
        for field in ("objectives", "sections", "workedExample", "limitations", "questions"):
            value = chapter.get(field)
            if not isinstance(value, dict) or set(value) != set(LANGUAGES):
                raise ValueError(f"chapter {number}: {field} must provide en and ko")
        cited = set()
        for lang in LANGUAGES:
            objectives = chapter["objectives"][lang]
            questions = chapter["questions"][lang]
            sections = chapter["sections"][lang]
            if not 3 <= len(objectives) <= 5 or any(not isinstance(x, str) or not x.strip() for x in objectives):
                raise ValueError(f"chapter {number}: {lang} must have 3–5 learning objectives")
            if len(sections) != 4:
                raise ValueError(f"chapter {number}: {lang} must have four authored sections")
            if len(questions) < 3 or any(not isinstance(x, str) or not x.strip() for x in questions):
                raise ValueError(f"chapter {number}: {lang} must have at least three review questions")
            if not chapter["limitations"][lang] or not all(isinstance(x, str) and x.strip() for x in chapter["limitations"][lang]):
                raise ValueError(f"chapter {number}: {lang} limitations must be non-empty")
            for section in sections:
                text(section.get("heading"), f"chapter {number} {lang} section heading")
                paragraphs = section.get("paragraphs")
                if not isinstance(paragraphs, list) or len(paragraphs) < 2:
                    raise ValueError(f"chapter {number}: each {lang} section needs at least two paragraphs")
                for paragraph in paragraphs:
                    text(paragraph, f"chapter {number} {lang} paragraph")
                    cited.update(CITATION.findall(paragraph))
            text(chapter["workedExample"][lang], f"chapter {number} {lang} worked example")
        refs = chapter.get("references")
        if not isinstance(refs, list) or not refs or not cited.issubset(set(refs)):
            raise ValueError(f"chapter {number}: inline citations must be listed in its references")
    reference_list = references.get("references")
    if not isinstance(reference_list, list) or len(reference_list) < 8:
        raise ValueError("at least eight public technical references are required")
    ref_ids = [item.get("id") for item in reference_list]
    if len(set(ref_ids)) != len(ref_ids):
        raise ValueError("reference IDs must be unique")
    ref_map = {item["id"]: item for item in reference_list}
    for item in reference_list:
        if not isinstance(item.get("id"), str) or not SAFE_REFERENCE_ID.fullmatch(item["id"]):
            raise ValueError(f"reference ID is invalid: {item.get('id')!r}")
        for key in ("authors", "title", "container", "details", "year", "publisher", "url", "note"):
            text(item.get(key), f"reference {item.get('id')} {key}")
        if not item["url"].startswith("https://"):
            raise ValueError(f"reference {item['id']}: source URL must use HTTPS")
    for chapter in chapters:
        if set(chapter["references"]) - set(ref_map):
            raise ValueError(f"chapter {chapter['number']}: unknown reference ID")
        inline = set()
        for lang in LANGUAGES:
            for section in chapter["sections"][lang]:
                for paragraph in section["paragraphs"]:
                    inline.update(CITATION.findall(paragraph))
        if not inline.issubset(set(chapter["references"])):
            raise ValueError(f"chapter {chapter['number']}: cited source is absent from reference list")
    experiments = labs.get("experiments")
    if not isinstance(experiments, list) or len(experiments) != 3:
        raise ValueError("the v1 candidate requires three analytical labs")
    experiment_ids = set()
    for experiment in experiments:
        if not SAFE_SLUG.fullmatch(experiment.get("id", "")) or experiment["id"] in experiment_ids:
            raise ValueError("lab IDs must be unique URL-safe slugs")
        experiment_ids.add(experiment["id"])
        if experiment.get("chapterId") not in chapter_ids:
            raise ValueError(f"lab {experiment['id']} links to an unknown chapter")
        for key in ("title", "kind", "description"):
            localized(experiment.get(key), f"lab {experiment['id']} {key}")
    if set(ui) != set(LANGUAGES) or set(pages) != set(LANGUAGES):
        raise ValueError("localized interface and page copy must provide en and ko")
    for lang in LANGUAGES:
        if not isinstance(pages[lang].get("groups"), dict) or set(pages[lang]["groups"]) != set(EXPECTED_GROUPS.values()):
            raise ValueError(f"{lang}: the overview must define all six chapter groups")


def route_for(lang, route):
    return ("ko/" if lang == "ko" else "") + route


def href_from(current_route, target_route):
    return posixpath.relpath(target_route, posixpath.dirname(current_route) or ".")


def page_shell(lang, title, route, body, ui, chapters, current_chapter=None):
    current_route = route_for(lang, route)
    home = route_for(lang, "index.html")
    lab = route_for(lang, "lab.html")
    references = route_for(lang, "references.html")
    license_page = route_for(lang, "license.html")
    other_lang = "ko" if lang == "en" else "en"
    other_route = route_for(other_lang, route)
    if other_lang == "ko" and route == "index.html":
        other_route = "ko/index.html"
    elif other_lang == "en" and route == "index.html":
        other_route = "index.html"
    asset_prefix = "../" * len(Path(current_route).parts[:-1])
    return f'''<!doctype html>
<html lang="{lang}">
<!-- Component notices: educational prose and original artwork are CC BY 4.0; page structure, controls, and application behavior are MIT. See LICENSE.md and LICENSE-AND-ATTRIBUTION.md. Referenced works retain their own rights. -->
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{escape(title, quote=True)} — ThinFilmBook">
  <meta name="theme-color" content="#172d38">
  <title>{escape(title)} · ThinFilmBook</title>
  <link rel="icon" href="{asset_prefix}assets/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="{asset_prefix}assets/css/site.css">
  <script type="module" src="{asset_prefix}assets/js/site.js"></script>
</head>
<body>
  <a class="skip-link" href="#main">{escape(ui['skip'])}</a>
  <header class="site-header">
    <a class="brand" href="{escape(href_from(current_route, home), quote=True)}">ThinFilmBook</a>
    <span class="subtitle">{escape(ui['subtitle'])}</span>
    <nav aria-label="{escape(ui['nav'], quote=True)}">
      <a href="{escape(href_from(current_route, home), quote=True)}">{escape(ui['home'])}</a>
      <a href="{escape(href_from(current_route, lab), quote=True)}">{escape(ui['labs'])}</a>
      <a href="{escape(href_from(current_route, references), quote=True)}">{escape(ui['references'])}</a>
      <a href="{escape(href_from(current_route, license_page), quote=True)}">{escape(ui['license'])}</a>
    </nav>
    <a class="language-link" lang="{other_lang}" href="{escape(href_from(current_route, other_route), quote=True)}">{escape(ui['language'])}</a>
  </header>
  <div class="page-layout">
    {chapter_nav(lang, current_route, ui, chapters, current_chapter)}
    <main id="main">{body}<footer class="site-footer"><span>{escape(ui['footer'])}</span><a href="{escape(href_from(current_route, license_page), quote=True)}">{escape(ui['license'])}</a></footer></main>
  </div>
</body>
</html>
'''


def chapter_routes(chapters):
    return ["chapters/" + item["slug"] + ".html" for item in chapters]


def write_page(path, page):
    normalized = "\n".join(line.rstrip() for line in page.splitlines()) + "\n"
    path.write_text(normalized, encoding="utf-8")


def chapter_nav(lang, current_route, ui, chapters, current_chapter):
    if current_chapter is None:
        return ""
    links = []
    for chapter, route in zip(chapters, chapter_routes(chapters)):
        active = ' aria-current="page"' if chapter["id"] == current_chapter["id"] else ""
        links.append(f'<a{active} href="{escape(href_from(current_route, route_for(lang, route)), quote=True)}"><span>{chapter["number"]:02d}</span> {escape(chapter["title"][lang])}</a>')
    return f'<aside class="chapter-nav" aria-label="{escape(ui["toc"], quote=True)}"><h2>{escape(ui["allChapters"])}</h2>{"".join(links)}</aside>'


def rich(text_value, reference_ids, references, reference_route):
    result = []
    last = 0
    for match in CITATION.finditer(text_value):
        result.append(escape(text_value[last:match.start()]))
        reference_id = match.group(1)
        record = references.get(reference_id)
        if not record or reference_id not in reference_ids:
            raise ValueError(f"citation {reference_id} must be listed for its chapter")
        result.append(f'<a class="citation" href="{escape(reference_route, quote=True)}#ref-{reference_id}" aria-label="{escape(record["title"], quote=True)}">[{reference_id}]</a>')
        last = match.end()
    result.append(escape(text_value[last:]))
    return "".join(result)


def render_chapter(chapter, lang, references, all_chapters, labs, ui, pages):
    route = "chapters/" + chapter["slug"] + ".html"
    section_html = []
    for section in chapter["sections"][lang]:
        paragraphs = "".join(f"<p>{rich(p, chapter['references'], references, href_from(route_for(lang, route), route_for(lang, 'references.html')))}</p>" for p in section["paragraphs"])
        section_html.append(f"<section><h2>{escape(section['heading'])}</h2>{paragraphs}</section>")
    ref_links = []
    for ref_id in chapter["references"]:
        record = references[ref_id]
        ref_links.append(f'<li><a href="{escape(href_from(route_for(lang, route), route_for(lang, "references.html")), quote=True)}#ref-{escape(ref_id, quote=True)}">{escape(record["authors"])} ({escape(record["year"])}). {escape(record["title"])}.</a></li>')
    position = chapter["number"] - 1
    routes = chapter_routes(all_chapters)
    prev_link = ""
    next_link = ""
    if position > 0:
        prev = all_chapters[position - 1]
        prev_link = f'<a class="chapter-step" rel="prev" href="{escape(href_from(route_for(lang, route), route_for(lang, routes[position - 1])), quote=True)}">← {escape(ui["previous"])}: {escape(prev["title"][lang])}</a>'
    if position + 1 < len(all_chapters):
        nxt = all_chapters[position + 1]
        next_link = f'<a class="chapter-step next" rel="next" href="{escape(href_from(route_for(lang, route), route_for(lang, routes[position + 1])), quote=True)}">{escape(ui["next"])}: {escape(nxt["title"][lang])} →</a>'
    experiment = next((item for item in labs["experiments"] if item["chapterId"] == chapter["id"]), None)
    lab_link = ""
    if experiment:
        lab_route = route_for(lang, "lab.html")
        lab_link = f'<p class="related-lab"><a href="{escape(href_from(route_for(lang, route), lab_route), quote=True)}#{experiment["id"]}">{escape(ui["openLab"])}: {escape(experiment["title"][lang])} →</a></p>'
    body = f'''<article class="chapter-content" id="{escape(chapter['id'], quote=True)}">
  <p class="eyebrow">{escape(ui['chapter'])} {chapter['number']:02d} · {escape(pages[lang]['groups'][chapter['group']]['title'])}</p>
  <h1>{escape(chapter['title'][lang])}</h1>
  <p class="lede">{escape(chapter['summary'][lang])}</p>
  <section class="objectives"><h2>{escape(ui['objectives'])}</h2><ul>{''.join('<li>'+escape(x)+'</li>' for x in chapter['objectives'][lang])}</ul></section>
  {''.join(section_html)}
  <section class="worked-example"><h2>{escape(ui['example'])}</h2><p>{escape(chapter['workedExample'][lang])}</p></section>
  {lab_link}
  <section class="limitations"><h2>{escape(ui['limitations'])}</h2><ul>{''.join('<li>'+escape(x)+'</li>' for x in chapter['limitations'][lang])}</ul></section>
  <section><h2>{escape(ui['questions'])}</h2><ol>{''.join('<li>'+escape(x)+'</li>' for x in chapter['questions'][lang])}</ol></section>
  <section class="chapter-references"><h2>{escape(ui['cited'])}</h2><ul>{''.join(ref_links)}</ul></section>
  <nav class="chapter-steps" aria-label="{escape(ui['toc'], quote=True)}">{prev_link}{next_link}</nav>
</article>'''
    return route, body


def field(label, input_id, *, value, minimum, maximum, step):
    return f'<label for="{input_id}">{escape(label)}<input id="{input_id}" name="{input_id}" type="number" value="{value}" min="{minimum}" max="{maximum}" step="{step}" inputmode="decimal" required></label>'


def lab_section(experiment, lang, ui):
    exp_id = experiment["id"]
    intro = f'<p class="lab-description">{escape(experiment["description"][lang])}</p>'
    if exp_id == "ald-conformality":
        controls = field(ui["phi"], "ald-phi", value="1.5", minimum="0", maximum="8", step="0.1") + field(ui["dose"], "ald-dose", value="1", minimum="0", maximum="10", step="0.1")
        button = "run-ald"
        chart = f'<figure><svg id="ald-chart" viewBox="0 0 720 260" role="img" aria-label="{escape(ui["profile"], quote=True)}"></svg><figcaption>{escape(ui["profile"])} · {escape(ui["chartLegend"])}</figcaption></figure>'
        caveat = ui["aldCaveat"]
    elif exp_id == "cvd-resistances":
        controls = field(ui["conc"], "cvd-concentration", value="1", minimum="0", maximum="1000000", step="0.1") + field(ui["km"], "cvd-km", value="0.1", minimum="0.000001", maximum="10000", step="0.01") + field(ui["ks"], "cvd-ks", value="0.1", minimum="0.000001", maximum="10000", step="0.01")
        button = "run-cvd"
        chart = ""
        caveat = ui["cvdCaveat"]
    elif exp_id == "stoney-stress":
        controls = field(ui["modulus"], "stoney-modulus", value="180", minimum="1", maximum="1000", step="1") + field(ui["poisson"], "stoney-poisson", value="0.28", minimum="0", maximum="0.49", step="0.01") + field(ui["substrate"], "stoney-substrate", value="500", minimum="1", maximum="10000", step="10") + field(ui["film"], "stoney-film", value="100", minimum="0.1", maximum="100000", step="10") + field(ui["curvature"], "stoney-curvature", value="0.1", minimum="-1000000", maximum="1000000", step="0.1")
        button = "run-stoney"
        chart = ""
        caveat = ui["stressCaveat"] + " " + ui["sign"]
    else:
        raise ValueError(f"no lab renderer for {exp_id}")
    return f'''<section class="lab-card" id="{escape(exp_id, quote=True)}" aria-labelledby="title-{escape(exp_id, quote=True)}">
  <p class="eyebrow">{escape(experiment['kind'][lang])}</p><h2 id="title-{escape(exp_id, quote=True)}">{escape(experiment['title'][lang])}</h2>
  {intro}<p class="assumption-note">{escape(ui['labNote'])}</p>
  <form class="model-form" data-model="{escape(exp_id, quote=True)}"><div class="field-grid">{controls}</div><button type="button" id="{button}">{escape(ui['run'])}</button></form>
  {chart}<div class="model-result" id="result-{escape(exp_id, quote=True)}" role="status" aria-live="polite"><span class="result-label">{escape(ui['result'])}</span><p>{escape(ui['labNote'])}</p></div>
  <details class="model-limits"><summary>{escape(ui['notices'])}</summary><p>{escape(caveat)}</p></details>
</section>'''


def render_home(lang, chapters, labs, ui, pages):
    groups = []
    for group_id in ("g1", "g2", "g3", "g4", "g5", "g6"):
        chapters_in_group = [chapter for chapter in chapters if chapter["group"] == group_id]
        items = []
        for chapter in chapters_in_group:
            path = "chapters/" + chapter["slug"] + ".html"
            href = href_from(route_for(lang, "index.html"), route_for(lang, path))
            items.append(f'<li><a href="{escape(href, quote=True)}"><span>{chapter["number"]:02d}</span><strong>{escape(chapter["title"][lang])}</strong><small>{escape(chapter["summary"][lang])}</small></a></li>')
        group = pages[lang]["groups"][group_id]
        groups.append(f'<section class="chapter-group"><h2>{escape(group["title"])}</h2><p>{escape(group["summary"])}</p><ol>{"".join(items)}</ol></section>')
    lab_links = []
    for experiment in labs["experiments"]:
        lab_href = href_from(route_for(lang, "index.html"), route_for(lang, "lab.html")) + "#" + experiment["id"]
        chapter = next(item for item in chapters if item["id"] == experiment["chapterId"])
        chapter_href = href_from(route_for(lang, "index.html"), route_for(lang, "chapters/" + chapter["slug"] + ".html"))
        lab_links.append(f'<li><a href="{escape(lab_href, quote=True)}">{escape(experiment["title"][lang])}</a><span>{escape(experiment["kind"][lang])}</span><a class="text-link" href="{escape(chapter_href, quote=True)}">{escape(chapter["title"][lang])} →</a></li>')
    return f'''<article class="home-content">
  <section class="hero"><p class="eyebrow">{escape(ui['homeEyebrow'])}</p><h1>ThinFilmBook</h1><p class="lede">{escape(pages[lang]['homeLead'])}</p><div class="hero-actions"><a class="button-link" href="{escape(href_from(route_for(lang, 'index.html'), route_for(lang, 'lab.html')), quote=True)}">{escape(ui['labs'])}</a><a class="text-link" href="{escape(href_from(route_for(lang, 'index.html'), route_for(lang, 'references.html')), quote=True)}">{escape(ui['openReferences'])} →</a></div></section>
  <section class="scope"><h2>{escape(ui['scope'])}</h2><p>{escape(pages[lang]['homeIntro'])}</p><p class="assumption-note">{escape(pages[lang]['scope'])}</p></section>
  <section class="contents"><h2>{escape(ui['allChapters'])}</h2>{''.join(groups)}</section>
  <section class="lab-directory"><h2>{escape(ui['labs'])}</h2><ul>{''.join(lab_links)}</ul></section>
</article>'''


def render_references(lang, references, ui):
    entries = []
    for item in references.values():
        entries.append(f'<article class="reference-item" id="ref-{escape(item["id"], quote=True)}"><p class="eyebrow">{escape(item["publisher"])} · {escape(item["year"])}</p><h2>{escape(item["authors"])}. “{escape(item["title"])}.”</h2><p><cite>{escape(item["container"])}</cite>, {escape(item["details"])}.</p><p>{escape(item["note"])}</p><p><a href="{escape(item["url"], quote=True)}" rel="noopener noreferrer">{escape(item["url"])}</a></p></article>')
    return f'<article><p class="eyebrow">ThinFilmBook · {escape(ui["references"])}</p><h1>{escape(ui["referencesHeading"])}</h1><p class="lede">{escape(ui["referencesIntro"])}</p><div class="reference-list">{"".join(entries)}</div></article>'


def render_lab(lang, labs, ui):
    sections = "".join(lab_section(item, lang, ui) for item in labs["experiments"])
    return f'<article><p class="eyebrow">ThinFilmBook · {escape(ui["lab"])}</p><h1>{escape(ui["labs"])}</h1><p class="lede">{escape(ui["labNote"])}</p><div class="lab-list">{sections}</div></article>'


def render_license(lang, ui):
    prefix = "../" if lang == "ko" else ""
    return f'''<article class="license-page"><p class="eyebrow">ThinFilmBook · {escape(ui['license'])}</p><h1>{escape(ui['licenseHeading'])}</h1><p class="lede">{escape(ui['licenseIntro'])}</p><ul><li>{escape(ui['cc'])} <a href="{prefix}LICENSE-CC-BY-4.0">LICENSE-CC-BY-4.0</a>.</li><li>{escape(ui['mit'])} <a href="{prefix}LICENSE-MIT">LICENSE-MIT</a>.</li></ul><p>{escape(ui['rights'])}</p><p>{escape(ui['review'])}</p><p>{escape(ui['scopeMap'])} <a href="{prefix}LICENSE.md">LICENSE.md</a> · <a href="{prefix}LICENSE-AND-ATTRIBUTION.md">LICENSE-AND-ATTRIBUTION.md</a></p><h2>{escape(ui['references'])}</h2><p>{escape(ui['referencesIntro'])} <a href="references.html">{escape(ui['openReferences'])}</a></p></article>'''


def manifest_data(chapters, labs):
    manifest = read_json(ROOT / "library-manifest.json")
    production = manifest.get("productionUrl", PLANNED_ROUTE_BASE).rstrip("/") + "/"
    manifest["status"] = "in-progress"
    manifest["chapterCount"] = len(chapters)
    manifest["chapters"] = []
    for chapter in chapters:
        slug = chapter["slug"] + ".html"
        manifest["chapters"].append({
            "id": chapter["id"], "number": chapter["number"], "title": chapter["title"],
            "urls": {"en": production + "chapters/" + slug, "ko": production + "ko/chapters/" + slug},
            "topics": [chapter["group"], "thin-film-engineering"],
        })
    manifest["experiments"] = [{
        "id": item["id"], "chapterId": item["chapterId"], "title": item["title"],
        "kind": item["kind"], "url": production + "lab.html#" + item["id"],
    } for item in labs["experiments"]]
    manifest["lastUpdated"] = date.today().isoformat()
    manifest["attribution"] = {
        "license": "CC BY 4.0 for original educational prose, explanations, exercises, and artwork; MIT for original application code and software tooling. See LICENSE.md for component-level scope.",
        "repositoryUrl": manifest["attribution"]["repositoryUrl"],
        "notes": "AI-assisted provenance is documented at repository scope. The source manifest remains in-progress by catalog convention; publication and deployment evidence are recorded separately. Cited publications are linked for study and are not reproduced.",
    }
    return manifest


def validate_manifest(manifest, chapters, labs):
    if manifest.get("status") != "in-progress":
        raise ValueError("book-local status must remain in-progress until release and production evidence exist")
    if manifest.get("chapterCount") != len(chapters) or [x.get("id") for x in manifest.get("chapters", [])] != [x["id"] for x in chapters]:
        raise ValueError("manifest chapter count and IDs must match authored chapter source")
    if set(manifest.get("languages", [])) != set(LANGUAGES):
        raise ValueError("manifest language list must match the English and Korean editions")
    production = manifest.get("productionUrl", PLANNED_ROUTE_BASE).rstrip("/") + "/"
    for chapter, record in zip(chapters, manifest["chapters"]):
        route = chapter["slug"] + ".html"
        expected = {"en": production + "chapters/" + route, "ko": production + "ko/chapters/" + route}
        if record.get("urls") != expected or record.get("title") != chapter["title"]:
            raise ValueError(f"manifest routes or titles do not match chapter {chapter['id']}")
    records = manifest.get("experiments", [])
    if [x.get("id") for x in records] != [x["id"] for x in labs["experiments"]]:
        raise ValueError("manifest experiment index must match lab source")
    for item, record in zip(labs["experiments"], records):
        expected = production + "lab.html#" + item["id"]
        if record.get("chapterId") != item["chapterId"] or record.get("url") != expected:
            raise ValueError(f"manifest experiment route is invalid for {item['id']}")
    attribution = manifest.get("attribution", {})
    if "CC BY 4.0" not in attribution.get("license", "") or "MIT" not in attribution.get("license", ""):
        raise ValueError("manifest must identify both content and code licenses")


def write_site(chapters, references, labs, ui, pages, output_root=SITE, announce=True):
    if output_root.is_symlink():
        raise ValueError("site output directory must not be a symlink")
    output_root.mkdir(parents=True, exist_ok=True)
    reference_map = {item["id"]: item for item in references["references"]}
    routes = chapter_routes(chapters)
    for lang in LANGUAGES:
        content_routes = [("index.html", "ThinFilmBook", render_home(lang, chapters, labs, ui[lang], pages)),
                          ("lab.html", ui[lang]["labs"], render_lab(lang, labs, ui[lang])),
                          ("references.html", ui[lang]["referencesHeading"], render_references(lang, reference_map, ui[lang])),
                          ("license.html", ui[lang]["licenseHeading"], render_license(lang, ui[lang]))]
        for route, title, body in content_routes:
            page = page_shell(lang, title, route, body, ui[lang], chapters)
            target = output_root / route_for(lang, route)
            target.parent.mkdir(parents=True, exist_ok=True)
            write_page(target, page)
        for chapter in chapters:
            route, body = render_chapter(chapter, lang, reference_map, chapters, labs, ui[lang], pages)
            page = page_shell(lang, chapter["title"][lang], route, body, ui[lang], chapters, chapter)
            target = output_root / route_for(lang, route)
            target.parent.mkdir(parents=True, exist_ok=True)
            write_page(target, page)
    for name in ("css", "js", "covers"):
        source = ROOT / "assets" / name
        if source.is_dir():
            shutil.copytree(source, output_root / "assets" / name, dirs_exist_ok=True)
    favicon = ROOT / "assets" / "favicon.svg"
    if favicon.is_file():
        (output_root / "assets").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(favicon, output_root / "assets" / "favicon.svg")
    for name in ("LICENSE.md", "LICENSE-AND-ATTRIBUTION.md", "LICENSE-CC-BY-4.0", "LICENSE-MIT"):
        source = ROOT / name
        if source.is_file():
            shutil.copyfile(source, output_root / name)
    docs = ROOT / "docs"
    if docs.is_dir():
        shutil.copytree(docs, output_root / "docs", dirs_exist_ok=True)
    if announce:
        print(f"Built {len(chapters)} bilingual chapters and {len(labs['experiments'])} labs.")


def compare_sites(expected_root, actual_root):
    expected = {path.relative_to(expected_root).as_posix(): path for path in expected_root.rglob("*") if path.is_file()}
    actual = {path.relative_to(actual_root).as_posix(): path for path in actual_root.rglob("*") if path.is_file()}
    differences = []
    for relative in sorted(expected.keys() | actual.keys()):
        if relative not in actual:
            differences.append(f"missing: {relative}")
        elif relative not in expected:
            differences.append(f"unexpected: {relative}")
        elif expected[relative].read_bytes() != actual[relative].read_bytes():
            differences.append(f"stale or modified: {relative}")
    return differences


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--write-manifest", action="store_true", help="update the in-progress manifest and build")
    group.add_argument("--check", action="store_true", help="validate sources, manifest, and generated routes without writing")
    group.add_argument("--build", action="store_true", help="build from the already synchronized manifest")
    args = parser.parse_args()
    try:
        chapters, references, labs, ui, pages = load_data()
        manifest = manifest_data(chapters, labs) if args.write_manifest else read_json(ROOT / "library-manifest.json")
        if args.check or args.build:
            validate_manifest(manifest, chapters, labs)
        if args.check:
            if SITE.is_symlink():
                raise ValueError("site output directory must not be a symlink")
            with tempfile.TemporaryDirectory(prefix="thinfilmbook-check-") as temporary:
                expected_root = Path(temporary)
                write_site(chapters, references, labs, ui, pages, expected_root, announce=False)
                differences = compare_sites(expected_root, SITE) if SITE.is_dir() else ["missing: site output directory"]
            if differences:
                sample = "; ".join(differences[:10])
                remainder = len(differences) - min(10, len(differences))
                suffix = f"; and {remainder} more" if remainder else ""
                raise ValueError(f"generated site differs from current sources: {sample}{suffix}")
            print(f"Validated {len(chapters)} bilingual chapters, {len(labs['experiments'])} labs, and the complete generated site.")
            return 0
        write_site(chapters, references, labs, ui, pages)
        if args.write_manifest:
            (ROOT / "library-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"build_site: error: {exc}", file=sys.stderr)
        return 1


def routes_all(chapters):
    return chapter_routes(chapters) + ["ko/" + route for route in chapter_routes(chapters)]


if __name__ == "__main__":
    raise SystemExit(main())
