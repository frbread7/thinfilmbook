# ThinFilmBook

ThinFilmBook is an original bilingual engineering textbook about thin-film growth, deposition, epitaxy, interfaces, film stress, characterization, and process integration.

This repository is a **local, in-progress release candidate**. It includes twelve English and Korean chapters, three bounded analytical labs, original cover artwork, citations, and local validation. Its manifest omits the top-level public repository and production destinations because neither exists. Chapter and lab routes, plus the nested attribution repository URL, describe prospective unverified locations; the My Library portal exposes no external action for this in-progress record. Nothing here is a calibrated process guide or evidence of fab qualification.

## Build and validate

Requirements: Python 3.10+ and Node.js 18+. There are no runtime or build dependencies to install.

```sh
npm test
npm run serve
```

Open `http://localhost:4173/` and use the language control for the Korean edition. `npm test` builds the generated `site/`, checks source and route consistency, tests the pure numerical models, and validates bilingual content and local links. The labs run entirely in the browser; they send no data to a server.

## Model scope

The ALD, CVD, and Stoney-equation labs are deliberately reduced teaching models. They expose units and assumptions and do not provide recipes, setpoints, equipment predictions, or material-specific acceptance limits. See [model assumptions and validation](docs/MODELS_AND_VALIDATION.md), [provenance](docs/PROVENANCE_AND_REVIEW.md), and [release gates](docs/RELEASE.md).

The book is registered as `in-progress` in its local manifest. No public repository or Pages deployment has been created or verified.
