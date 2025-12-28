# Aman Singhal — Portfolio (FastAPI)

This is a small FastAPI-based portfolio site scaffold.

Run locally

1. Create a virtualenv and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Start the app (from workspace root):

```bash
uvicorn portfolio.app:app --reload
```

3. Open http://127.0.0.1:8000/

Notes
- Add a PDF resume to `portfolio/static/Aman_Singhal_Resume.txt` (replace with `Aman_Singhal_Resume.pdf` if you prefer PDF).
- Contact form stores leads in `portfolio/data/leads.json` (no email configured by default).
- Email sending: configure either **SendGrid** or SMTP env vars to send contact form submissions.

Environment variables (optional):
- `SENDGRID_API_KEY` — if set, SendGrid will be used to send messages.
- `SMTP_HOST`, `SMTP_PORT` (default 587), `SMTP_USER`, `SMTP_PASSWORD` — SMTP server details
- `SMTP_TLS` (default 1) / `SMTP_SSL` (default 0) — whether to use TLS/SSL
- `EMAIL_FROM` — sender email (defaults to profile email)
- `EMAIL_TO` — recipient email (defaults to profile email)
- `ADMIN_PASS` — set this to a password to protect the `/admin` upload UI

Example (Linux/macOS):

```bash
export SENDGRID_API_KEY="SG_xxx"
# or
export SMTP_HOST=smtp.example.com
export SMTP_PORT=587
export SMTP_USER=you
export SMTP_PASSWORD=secret
export EMAIL_TO=aman95singhal@gmail.com
# Admin UI password
export ADMIN_PASS="choose-a-strong-password"
```

Admin UI
- Visit `/admin/login` and enter the `ADMIN_PASS` to access the upload UI.
- Upload images via the form to generate responsive WebP sizes automatically. Images are saved under `static/img/uploads/` and added to projects when you select the project slug and check "Set as project image?".
- Upload the PDF resume via the admin UI to replace `static/Aman_Singhal_Resume.pdf`.

To test email sending locally, start the server and submit the contact form on `/contact` — messages are stored in `portfolio/data/leads.json` regardless of email delivery; email sending is attempted in background and logged to the server console.

To deploy, set the environment variables on your hosting provider (Render, Railway, etc.)

---

## GitHub Pages static export (auto-publish)

This repository includes a static export pipeline which renders the Jinja templates and produces a static site in the `docs/` folder suitable for GitHub Pages or static hosting.

- Run the exporter locally: `python scripts/export_static.py` (it will write to `docs/`).
- A GitHub Actions workflow `.github/workflows/deploy-gh-pages.yml` is included that runs the exporter and publishes the generated `docs/` to the `gh-pages` branch using `peaceiris/actions-gh-pages` on each push to `main`.
- The exported `docs/` root contains `index.html`, `styles.css` and `script.js` so it will satisfy GitHub Pages' requirement.

Important steps to complete hosting:
1. Commit and push your changes to `main` (the workflow will run and publish `docs/` to `gh-pages`).
2. Optionally replace the placeholder Formspree ID in `docs/contact.html` to make the contact form functional on the static site.
3. Confirm GitHub Pages settings (Settings → Pages) if you prefer to serve from `gh-pages` branch; the action will create/update that branch automatically.

If you want, I can commit and push the `docs/` folder and workflow for you and then enable Pages, or I can open a PR — which do you prefer?
