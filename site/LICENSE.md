# ThinFilmBook license scope

This file is the component-level map for the two license instruments in this
repository. The file extension alone does not determine a license: where a file
contains more than one kind of material, each component keeps the license
listed for that component below.

`frbread7` is the project maintainer and authorized licensor for material only
to the extent the maintainer controls the relevant rights. Naming the
maintainer does not claim authorship or copyright ownership over every item,
and does not grant rights belonging to third parties. AI-assisted provenance
is recorded in [docs/PROVENANCE_AND_REVIEW.md](docs/PROVENANCE_AND_REVIEW.md).
Nothing in that record or this map asserts copyright ownership beyond rights
that exist under applicable law.

## Component map

| Location or component | License and scope |
| --- | --- |
| `content/chapters/*.json` | CC BY 4.0 for the English and Korean educational text: titles, summaries, objectives, section headings and prose, worked examples, limitations, and review questions. JSON keys, identifiers, citation IDs, and structural fields are MIT-licensed application data/configuration. |
| `content/pages.json` | CC BY 4.0 for the original overview, learning descriptions, and explanatory prose in both languages. JSON keys, group IDs, and structural fields are MIT-licensed application data/configuration. |
| `content/labs.json` | CC BY 4.0 for original lab descriptions and educational explanations. Lab IDs, chapter links, and fields used to configure the application are MIT-licensed application data/configuration. |
| `content/ui.json` | CC BY 4.0 for substantive educational explanations and model assumptions or caveats, including `labNote`, `referencesIntro`, `licenseIntro`, `labCaveat`, `stressCaveat`, `cvdCaveat`, `aldCaveat`, and `sign`, in English and Korean. Navigation, control, chart, result, and other functional interface labels and their JSON structure are MIT-licensed application material. |
| `content/references.json` | The original explanatory notes are CC BY 4.0. Bibliographic facts, titles, author names, publication details, and links identify the cited works; ThinFilmBook does not license those works or claim rights in their contents. No source text, figure, table, dataset, or executable material from the references is included. |
| `assets/covers/thinfilmbook.svg`, `assets/favicon.svg` | The original cover and favicon artwork are CC BY 4.0. Their SVG drawing instructions are part of the artwork, not application code. |
| `assets/js/*.js`, `assets/js/*.mjs`, `assets/css/**`, `tools/**`, `tests/**` | MIT for original application code, simulator implementations, styles, build scripts, tests, and related software tools. |
| `.github/workflows/**`, `package.json`, `.gitignore` | MIT for original workflow and software configuration. The workflow invokes GitHub-maintained Actions by pinned revision; their code and terms are not relicensed by this repository. |
| `library-manifest.json` | CC BY 4.0 for original descriptive prose and book, chapter, and lab descriptions. MIT for schema fields, identifiers, routing values, tags, and software/catalog structure. URLs are references to destinations and do not grant rights to their targets. |
| `README.md`, `docs/**`, `LICENSE-AND-ATTRIBUTION.md`, and this file, including generated copies under `site/` | CC BY 4.0 for original explanatory and educational prose. Any code or command snippets are MIT-licensed software material. The complete license texts in `LICENSE-CC-BY-4.0` and `LICENSE-MIT` remain the license instruments for their respective covered material. |
| Generated `site/**/*.html` | Mixed by component: copied educational prose, examples, assumptions, and explanations are CC BY 4.0; page templates, structure, navigation, controls, and inline application behavior are MIT. The generated pages contain separate component notices. Linked bibliographic records identify external works and do not relicense them. |
| Generated `site/assets/**` | The generated cover and favicon remain CC BY 4.0; generated JavaScript, CSS, and simulator output code remain MIT, matching their source components. |
| `LICENSE-CC-BY-4.0`, `LICENSE-MIT`, and their generated copies in `site/`; third-party reference works | The license files are instruments/notices, not a blanket grant of rights by ThinFilmBook. See each instrument and the cited source's own terms. Generated license files are copies of the corresponding source instruments. |

## Attribution and provenance

For CC BY 4.0 material, a reasonable attribution may identify the source as
“ThinFilmBook, maintained by frbread7,” link to the [project repository](https://github.com/frbread7/thinfilmbook)
and [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), retain any
applicable notices supplied with the material, and describe changes made. This
wording identifies the project and maintainer; it does not assert that the
maintainer authored or owns every AI-assisted output. Do not suggest
endorsement by the maintainer or by any cited source.

AI tools, including Codex, assisted with material in this project. See the
provenance record for the known scope and its limits. The license mapping does
not determine whether any particular AI-assisted output is copyrightable or
who owns it. Third-party materials, if any are later added, must be identified
and their rights assessed separately before they are included under either
license.

For MIT-licensed application material, retain `LICENSE-MIT` and its bounded
maintainer notice in redistributed copies or substantial portions. Use the
component map above when redistributing a mixed HTML, JavaScript, or generated
site file; keep the distinct notices for the separately licensed components.

The CC BY 4.0 license grants only rights the licensor is authorized to grant.
It does not clear third-party, privacy, publicity, trademark, patent, or other
rights. No legal certification is made here.
