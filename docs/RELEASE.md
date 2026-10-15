# Release gates

Current state: local candidate, manifest status `in-progress`, version `0.1.0`. The proposed repository, chapter, and lab routes are prospective, unverified metadata; no GitHub repository has been created, no release tag exists, and no public site has been deployed or verified. The My Library record omits its top-level public destinations, so it exposes no repo or site action.

The candidate is buildable offline. Before any public release, the owner must authorize the external publication step. Then:

1. Review the final source and generated diff, the license and attribution record, bilingual content, numerical assumptions, and all independent review findings.
2. Create or designate the public repository and authorize the Pages workflow and deployment.
3. Run CI and the release checks on the exact candidate revision; create a versioned release only after review passes.
4. Verify the successful Pages deployment's source SHA and check both language landing pages, all 24 chapter routes, the three lab anchors, citations, and license links against the live site.
5. Record deployment evidence separately from the release tag. Keep the My Library manifest `in-progress` until its production requirements and evidence are reviewed and explicitly updated.

The current local verification cannot satisfy steps 2–5.

## Current publication workflow defect

The local `.github/workflows/pages.yml` workflow deploys the checked-in `site/` directory from `main` without first building the current source or running validation. A source change can therefore publish stale generated pages, and the deployment job has no passing build/test result to tie to its artifact. The file has intentionally not been changed during this candidate because it changes production release behavior. The minimal proposed repair is to add a CI job that runs `npm test` on the exact candidate revision, upload that job's generated `site/` directory as an artifact, and make the Pages deployment job depend on the successful CI job and deploy that artifact. Review and authorize this workflow change before enabling public publication.

This ThinFilmBook working directory is not a Git checkout, so it has no candidate commit SHA or local source history to record yet. The local build and browser checks establish only that the current files pass those checks; they do not provide release traceability.
