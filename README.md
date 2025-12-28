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