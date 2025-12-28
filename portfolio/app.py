from fastapi import FastAPI, Request, Form, HTTPException, BackgroundTasks, File, UploadFile, Response
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import json
import logging
from datetime import datetime
import os
import smtplib
from email.message import EmailMessage
from typing import Optional
from .utils.images import generate_responsive_images

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

UPLOADS_DIR = BASE_DIR / "static" / "img" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Aman Singhal — Portfolio")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Live lead subscribers (for SSE broadcast to admin)
import asyncio
LEADS_SUBSCRIBERS = []

def broadcast_lead(entry: dict):
    # Push to all subscriber queues (best-effort)
    for q in list(LEADS_SUBSCRIBERS):
        try:
            q.put_nowait(entry)
        except Exception:
            logger.exception("Failed to broadcast lead to subscriber")

# Add a helper filter for responsive srcset generation
templates.env.filters['responsive_srcset'] = lambda image_path: ', '.join([f"{image_path.replace('.webp', f'-{w}.webp')} {w}w" for w in (600,1200,1800)])

logger = logging.getLogger("portfolio")
logger.setLevel(logging.INFO)

# Load profile and projects
PROFILE_PATH = DATA_DIR / "profile.json"
PROJECTS_PATH = DATA_DIR / "projects.json"
LEADS_PATH = DATA_DIR / "leads.json"
if not LEADS_PATH.exists():
    LEADS_PATH.write_text("[]")

def load_json(path: Path):
    try:
        return json.loads(path.read_text())
    except Exception:
        return None

profile = load_json(PROFILE_PATH) or {}
projects = load_json(PROJECTS_PATH) or []

# Helpers
def find_project(slug: str):
    for p in projects:
        if p.get("slug") == slug:
            return p
    return None

# --- Email sending helpers -----------------------------------------
def send_email_via_sendgrid(api_key: str, to_email: str, subject: str, content: str, from_email: str) -> bool:
    # Import httpx lazily so the app can start even if httpx is not installed in some environments
    try:
        import httpx as _httpx
    except Exception:
        logger.exception("httpx not available")
        return False
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": from_email},
        "subject": subject,
        "content": [{"type": "text/plain", "value": content}]
    }
    try:
        r = _httpx.post("https://api.sendgrid.com/v3/mail/send", json=payload, headers=headers, timeout=10.0)
        r.raise_for_status()
        return True
    except Exception:
        logger.exception("SendGrid send failed")
        return False


def send_email_via_smtp(host: str, port: int, user: Optional[str], password: Optional[str], from_email: str, to_email: str, subject: str, content: str, use_tls: bool = True, use_ssl: bool = False) -> bool:
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = to_email
        msg.set_content(content)
        if use_ssl:
            server = smtplib.SMTP_SSL(host, port, timeout=10)
        else:
            server = smtplib.SMTP(host, port, timeout=10)
        server.ehlo()
        if use_tls and not use_ssl:
            server.starttls()
            server.ehlo()
        if user:
            server.login(user, password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception:
        logger.exception("SMTP send failed")
        return False


def send_contact_email(entry: dict) -> None:
    """Try SendGrid first, fallback to SMTP if configured."""
    from_email = os.environ.get("EMAIL_FROM", profile.get("email"))
    to_email = os.environ.get("EMAIL_TO", profile.get("email"))
    subject = f"Portfolio contact form: {entry.get('name')}"
    body = f"Name: {entry.get('name')}\nEmail: {entry.get('email')}\nMessage:\n{entry.get('message')}\n\nReceived: {entry.get('ts')}"

    sendgrid_key = os.environ.get("SENDGRID_API_KEY")
    if sendgrid_key:
        ok = send_email_via_sendgrid(sendgrid_key, to_email, subject, body, from_email)
        if ok:
            logger.info("Contact email sent via SendGrid")
            return

    smtp_host = os.environ.get("SMTP_HOST")
    if smtp_host:
        smtp_port = int(os.environ.get("SMTP_PORT", 587))
        smtp_user = os.environ.get("SMTP_USER")
        smtp_pass = os.environ.get("SMTP_PASSWORD")
        use_ssl = os.environ.get("SMTP_SSL", "0") == "1"
        use_tls = os.environ.get("SMTP_TLS", "1") == "1"
        ok = send_email_via_smtp(smtp_host, smtp_port, smtp_user, smtp_pass, from_email, to_email, subject, body, use_tls=use_tls, use_ssl=use_ssl)
        if ok:
            logger.info("Contact email sent via SMTP")
            return

    logger.warning("No email provider configured; skipping send")
# Simple admin auth helper
def _is_admin(request: Request) -> bool:
    # simple cookie-based admin; set via /admin/login
    return request.cookies.get("_is_admin") == "1"


# Routes
def list_gallery_images():
    img_dir = BASE_DIR / "static" / "img"
    out = []
    for p in sorted(img_dir.iterdir()):
        if p.is_file() and p.parent == img_dir and p.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp', '.svg'):
            out.append(f"/static/img/{p.name}")
    return out

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    gallery_images = list_gallery_images()
    resp = templates.TemplateResponse("index.html", {"request": request, "profile": profile, "projects": projects, "gallery_images": gallery_images, "year": datetime.now().year})
    logger.debug("index returning %s", type(resp))
    return resp


# Admin login
@app.get("/admin/login", response_class=HTMLResponse)
def admin_login_get(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request, "error": None, "profile": profile, "year": datetime.now().year})

@app.post("/admin/login")
def admin_login_post(request: Request, password: str = Form(...)):
    admin_pass = os.environ.get("ADMIN_PASS")
    if admin_pass and password == admin_pass:
        resp = RedirectResponse(url="/admin", status_code=303)
        resp.set_cookie("_is_admin", "1", httponly=True)
        return resp
    return templates.TemplateResponse("admin_login.html", {"request": request, "error": "Invalid password", "profile": profile, "year": datetime.now().year})

@app.get("/admin", response_class=HTMLResponse)
def admin_get(request: Request):
    if not _is_admin(request):
        return RedirectResponse(url="/admin/login")
    uploads = [p.name for p in (UPLOADS_DIR).glob("*") if p.is_file()]
    return templates.TemplateResponse("admin.html", {"request": request, "uploads": uploads, "profile": profile, "year": datetime.now().year})

@app.post("/admin/upload")
def admin_upload(request: Request, slug: str = Form(...), file: UploadFile = File(...), assign: bool = Form(True)):
    # simple admin-protected upload
    if not _is_admin(request):
        return RedirectResponse(url="/admin/login")
    if not file.filename:
        return RedirectResponse(url="/admin")
    safe_name = Path(file.filename).name
    dest = UPLOADS_DIR / safe_name
    with dest.open("wb") as fh:
        fh.write(file.file.read())
    generated = generate_responsive_images(dest, UPLOADS_DIR)
    # assign largest (detail) as project image if assign True and project exists
    if assign and generated and find_project(slug):
        # pick detail size
        detail_url = generated.get("detail")
        for p in projects:
            if p.get("slug") == slug:
                p["image"] = detail_url
        PROJECTS_PATH.write_text(json.dumps(projects, indent=2))
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/admin/upload_resume")
def admin_upload_resume(request: Request, resume: UploadFile = File(None)):
    if not _is_admin(request):
        return RedirectResponse(url="/admin/login")
    if resume:
        dest = BASE_DIR / "static" / "Aman_Singhal_Resume.pdf"
        with dest.open("wb") as fh:
            fh.write(resume.file.read())
    return RedirectResponse(url="/admin", status_code=303)

@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request, "profile": profile, "year": datetime.now().year})

@app.get("/projects", response_class=HTMLResponse)
def projects_list(request: Request):
    # compute unique sorted tags for project filtering and pass to template
    tags = sorted({t for p in projects for t in p.get('tech', [])})
    return templates.TemplateResponse("projects.html", {"request": request, "projects": projects, "tags": tags, "profile": profile, "year": datetime.now().year})

@app.get("/projects/search", response_class=HTMLResponse)
def projects_search(request: Request, q: str = "", tag: str = ""):
    """Return a partial list of projects matching query or tag for HTMX replacement."""
    filtered = projects
    if q:
        qlow = q.lower()
        filtered = [p for p in filtered if qlow in p.get('title','').lower() or qlow in p.get('summary','').lower()]
    if tag:
        filtered = [p for p in filtered if tag in p.get('tech', [])]
    return templates.TemplateResponse("_projects_list.html", {"request": request, "projects": filtered})

@app.get("/projects/{slug}", response_class=HTMLResponse)
def project_detail(request: Request, slug: str):
    p = find_project(slug)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return templates.TemplateResponse("project_detail.html", {"request": request, "project": p, "profile": profile, "year": datetime.now().year})

# Comments: simple JSON file per project
def _comments_path_for(slug: str) -> Path:
    return DATA_DIR / f"comments_{slug}.json"

@app.get("/projects/{slug}/comments", response_class=HTMLResponse)
def project_comments(request: Request, slug: str):
    path = _comments_path_for(slug)
    try:
        comments = json.loads(path.read_text()) if path.exists() else []
    except Exception:
        comments = []
    return templates.TemplateResponse("_comments_list.html", {"request": request, "comments": comments})

@app.post("/projects/{slug}/comments")
def submit_project_comment(request: Request, slug: str, name: str = Form(...), comment: str = Form(...)):
    entry = {"name": name, "comment": comment, "ts": datetime.utcnow().isoformat()}
    path = _comments_path_for(slug)
    try:
        cur = json.loads(path.read_text()) if path.exists() else []
        cur.append(entry)
        path.write_text(json.dumps(cur, indent=2))
    except Exception:
        logger.exception("Failed to save comment")
        return JSONResponse({"error": "failed"}, status_code=500)
    # return an HTML fragment representing the new comment for HTMX to insert
    return templates.TemplateResponse("_comment_item.html", {"request": request, "comment": entry})

@app.get("/projects/search", response_class=HTMLResponse)
def projects_search(request: Request, q: str = "", tag: str = ""):
    """Return a partial list of projects matching query or tag for HTMX replacement."""
    filtered = projects
    if q:
        qlow = q.lower()
        filtered = [p for p in filtered if qlow in p.get('title','').lower() or qlow in p.get('summary','').lower()]
    if tag:
        filtered = [p for p in filtered if tag in p.get('tech', [])]
    return templates.TemplateResponse("_projects_list.html", {"request": request, "projects": filtered})

@app.get("/contact", response_class=HTMLResponse)
def contact_get(request: Request, success: int = 0):
    return templates.TemplateResponse("contact.html", {"request": request, "success": success, "profile": profile, "year": datetime.now().year})

@app.post("/contact")
def contact_post(request: Request, name: str = Form(...), email: str = Form(...), message: str = Form(...), background_tasks: BackgroundTasks = None):
    entry = {"name": name, "email": email, "message": message, "ts": datetime.utcnow().isoformat()}
    try:
        leads = json.loads(LEADS_PATH.read_text())
        leads.append(entry)
        LEADS_PATH.write_text(json.dumps(leads, indent=2))
        logger.info(f"Lead saved: {name} <{email}>")
    except Exception as e:
        logger.exception("Failed to save lead")
        return JSONResponse({"error": "failed to save"}, status_code=500)

    # Send email in background if configured
    try:
        if background_tasks is not None:
            background_tasks.add_task(send_contact_email, entry)
        else:
            # best-effort synchronous send
            send_contact_email(entry)
    except Exception:
        logger.exception("Failed to queue/send contact email")

    # Broadcast to admin subscribers (SSE) if any
    try:
        broadcast_lead(entry)
    except Exception:
        logger.exception("Broadcast failed")

    # If HTMX/async request, return a small success partial to replace the form
    try:
        if request.headers.get("hx-request") == "true":
            return templates.TemplateResponse("_contact_success.html", {"request": request, "profile": profile, "year": datetime.now().year})
    except Exception:
        pass

    return RedirectResponse(url="/contact?success=1", status_code=303)

@app.get("/api/profile")
def api_profile():
    return profile

@app.get("/api/projects")
def api_projects():
    return projects

@app.get("/admin/lead_stream")
async def lead_stream(request: Request):
    """Server-Sent Events endpoint that streams new leads to admin UI."""
    q = asyncio.Queue()
    LEADS_SUBSCRIBERS.append(q)

    async def event_generator():
        try:
            while True:
                # disconnect support: break if client disconnects
                if await request.is_disconnected():
                    break
                data = await q.get()
                yield f"data: {json.dumps(data)}\n\n"
        finally:
            try:
                LEADS_SUBSCRIBERS.remove(q)
            except Exception:
                pass

    from fastapi.responses import StreamingResponse
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Simple health
@app.get("/health")
def health():
    return {"status": "ok"}
