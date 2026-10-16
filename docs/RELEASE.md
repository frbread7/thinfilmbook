# Release and Pages evidence

## Source-manifest convention

The book-local `library-manifest.json` remains `in-progress` at version `0.1.0`
as source metadata. Publication is recorded separately in the central My
Library catalog after the public repository, release, and production site have
been verified.

## Release gates

1. Review the complete source and generated-site diff, bilingual content,
   model assumptions, license scope, provenance, third-party references, and
   independent review findings.
2. Run `npm test`; it rebuilds the static site, checks generated output,
   validates JavaScript syntax and bilingual content, and tests the numerical
   models and local routes.
3. Push the reviewed source revision to `main`. The Pages workflow must run
   `npm test`, upload that run's generated `site/` artifact, and deploy that
   artifact only after validation succeeds.
4. Verify that the successful Pages deployment identifies the reviewed source
   revision. Check both language landing pages, all 24 chapter routes, all
   three lab routes and calculations, citations, license links, and responsive
   behavior in a browser.
5. Create the `v1.0.0` release tag only after the production checks pass. Keep
   the source manifest at `in-progress` / `0.1.0`; update the central catalog
   only with evidence from the verified public release and deployment.

## Evidence to retain

For each public release, record the source commit, version tag, successful
validation workflow URL, Pages deployment run or identifier, deployed URL and
source revision, production route and lab checks, and browser/device widths
checked. A successful local build or CI run alone does not prove that the
production deployment completed or serves the same revision.

## Pages artifact flow

The `.github/workflows/pages.yml` workflow runs `npm test` on pull requests and
on pushes to `main`. The validation job uploads the freshly generated `site/`
directory as the Pages artifact. Deployment runs only for `main` after
validation succeeds and uses that uploaded artifact rather than the checked-in
generated site.
