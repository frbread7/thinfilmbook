# ThinFilmBook

ThinFilmBook is an original bilingual engineering textbook about thin-film growth, deposition, epitaxy, interfaces, film stress, characterization, and process integration.

This repository contains twelve English and Korean chapters, three bounded analytical labs, original cover and favicon artwork, citations, and local validation. The book-local manifest remains `in-progress` at version `0.1.0` as source metadata; publication and deployment status are recorded separately in [docs/RELEASE.md](docs/RELEASE.md). Nothing here is a calibrated process guide or evidence of fab qualification.

## Build and validate

Requirements: Python 3.10+ and Node.js 18+. There are no runtime or build dependencies to install.

```sh
npm test
npm run serve
```

Open `http://localhost:4173/` and use the language control for the Korean edition. `npm test` builds the generated `site/`, checks source and route consistency, tests the pure numerical models, and validates bilingual content and local links. The labs run entirely in the browser; they send no data to a server.

## Model scope

The ALD, CVD, and Stoney-equation labs are deliberately reduced teaching models. They expose units and assumptions and do not provide recipes, setpoints, equipment predictions, or material-specific acceptance limits. See [model assumptions and validation](docs/MODELS_AND_VALIDATION.md), [provenance](docs/PROVENANCE_AND_REVIEW.md), and [release gates](docs/RELEASE.md).

License scope is component-based: educational prose and original artwork use CC BY 4.0, while application code and software tooling use MIT. See [LICENSE.md](LICENSE.md), [LICENSE-AND-ATTRIBUTION.md](LICENSE-AND-ATTRIBUTION.md), and the [AI-assisted provenance record](docs/PROVENANCE_AND_REVIEW.md).
