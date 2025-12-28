# Portfolio Site (FastAPI)

This repository contains the FastAPI portfolio site and a static-export pipeline to publish the site via GitHub Pages.

Quick start
-----------
- Run locally: `uvicorn portfolio.app:app --reload`
- Build the static site: `python scripts/export_static.py` (outputs to `docs/`)
- The `docs/` folder contains `index.html`, `styles.css`, and `script.js` suitable for GitHub Pages.

Automatic publish
-----------------
This repo includes a GitHub Actions workflow `.github/workflows/deploy-gh-pages.yml` that will run the static exporter and publish `docs/` to the `gh-pages` branch on each push to `main`.

Replace the placeholder Formspree form action in `docs/contact.html` with your Formspree form ID to receive contact form submissions on the static site.

Files to review
---------------
- `portfolio/` — FastAPI app, templates, static assets
- `scripts/export_static.py` — static-site exporter (produces `docs/`)
- `docs/` — static output (auto-generated; can be committed)
- `.github/workflows/deploy-gh-pages.yml` — CI that builds and publishes `docs/`

If you want, I can commit and push the `docs/` folder and workflow, run the action, and confirm the Pages URL — would you like me to do that now?

---

Troubleshooting: Action cannot push (403 / git push failed)
--------------------------------------------------------
If you see an error in GitHub Actions such as `remote: Write access to repository not granted` or `fatal: unable to access ... 403`, follow these steps:

1. Enable workflow write permissions (easiest):
   - The workflow now requests `contents: write` permissions at the top. This usually fixes the issue if your repository settings allow workflows to push.

2. If the workflow still cannot push, create a Personal Access Token (PAT) and add it as a repo secret called `GH_PAGES_TOKEN`:
   - Go to GitHub > Settings > Developer settings > Personal access tokens > Tokens (classic) (or create a fine-grained token).
   - Create a token with `public_repo` permission (for public repos) or `repo` for private repos, or create a fine-grained token that allows repo contents write.
   - In your repository: Settings → Secrets and variables → Actions → New repository secret, name it `GH_PAGES_TOKEN` and paste the token.
   - The workflow is already configured to use `GH_PAGES_TOKEN` if present.

3. Ensure repository Actions permissions allow workflows to have `Read and write permissions`:
   - Settings → Actions → General → Workflow permissions → Select `Read and write permissions`.

4. If your workflow run originated from a forked PR, re-run the workflow from the protected branch (`main`) or push a commit directly to the repository to trigger a full-authorized run.

If you'd like, I can add example commands for PAT creation or walk through adding the secret step-by-step.