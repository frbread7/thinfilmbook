# Release gates

Current state: local candidate, manifest status `in-progress`, version `0.1.0`. The repository, chapter, and lab routes remain unverified; no GitHub repository has been created, no release tag exists, and no public site has been deployed or verified. The My Library record omits its top-level public destinations, so it exposes no repo or site action. Public repository creation and Pages deployment are authorized for this release task; publication remains gated on final source review and a complete file-level rights map.

The candidate is buildable offline. Before release:

1. Review the final source and generated diff, the license and attribution record, bilingual content, numerical assumptions, and all independent review findings.
2. Confirm the existing licenses and rights-holder authority cover every tracked source file and generated asset; do not infer a new license assignment for an unmapped file.
3. Create the authorized public repository and configure the Pages workflow for deployment from Actions.
4. Run CI and the release checks on the exact candidate revision; create a versioned release only after review passes.
5. Verify the successful Pages deployment's source SHA and check both language landing pages, all 24 chapter routes, the three lab anchors, citations, and license links against the live site.
6. Record deployment evidence separately from the release tag. Keep the My Library manifest `in-progress` until its production requirements and evidence are reviewed and explicitly updated.

The current local verification cannot satisfy steps 2–5. The candidate now has local Git history, but no public remote, CI run, source publication, or deployment evidence.

## Pages validation and artifact flow

The `.github/workflows/pages.yml` workflow validates pull requests and main-branch releases with `npm test`. That command builds the site, checks the complete generated output and source routes, checks JavaScript syntax, runs the numerical model tests, and runs the bilingual content/site tests. The validation job uploads the freshly generated `site/` directory as the Pages artifact. Deployment runs only for `main` after validation succeeds and deploys that artifact; it does not use the checked-in generated site as its input.

Local checks do not provide external CI or deployment traceability. Record the exact source SHA separately from the release tag and deployed production revision after the Pages run succeeds.
