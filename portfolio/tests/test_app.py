import pytest
from httpx import AsyncClient
from portfolio.app import app, LEADS_PATH, projects, DATA_DIR
import json

@pytest.mark.asyncio
async def test_index():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/")
        assert r.status_code == 200

@pytest.mark.asyncio
async def test_api_profile():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/api/profile")
        assert r.status_code == 200
        assert "name" in r.json()

@pytest.mark.asyncio
async def test_contact_saves_lead(tmp_path):
    # keep a backup of the leads file and restore after test
    orig = LEADS_PATH.read_text()
    try:
        async with AsyncClient(app=app, base_url="http://test") as ac:
            r = await ac.post("/contact", data={"name": "Test", "email": "t@example.com", "message": "hello"})
            assert r.status_code in (200, 303)
        leads = json.loads(LEADS_PATH.read_text())
        assert any(l.get("email") == "t@example.com" for l in leads)
    finally:
        LEADS_PATH.write_text(orig)

@pytest.mark.asyncio
async def test_contact_via_htmx_posts(tmp_path):
    orig = LEADS_PATH.read_text()
    try:
        async with AsyncClient(app=app, base_url="http://test") as ac:
            headers = {"hx-request": "true"}
            r = await ac.post("/contact", data={"name": "Hx", "email": "hx@example.com", "message": "hi"}, headers=headers)
            assert r.status_code == 200
            assert "Thanks — your message was sent" in r.text
        leads = json.loads(LEADS_PATH.read_text())
        assert any(l.get("email") == "hx@example.com" for l in leads)
    finally:
        LEADS_PATH.write_text(orig)

@pytest.mark.asyncio
async def test_admin_login_and_upload(tmp_path, monkeypatch):
    # set admin password
    monkeypatch.setenv('ADMIN_PASS', 's3cret')
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.post('/admin/login', data={'password': 's3cret'})
        # login should redirect to /admin
        assert r.status_code in (200, 303)
        # perform a fake upload using a small PNG generated here
        img = tmp_path / 't.png'
        img.write_bytes(b'\x89PNG\r\n\x1a\n')
        with img.open('rb') as fh:
            r2 = await ac.post('/admin/upload', data={'slug': 'transaction-master', 'assign': 'on'}, files={'file': ('t.png', fh, 'image/png')})
            assert r2.status_code in (200, 303)
    # cleanup not necessary because uploads are in static/img/uploads

@pytest.mark.asyncio
async def test_projects_search():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get('/projects/search?q=flight')
        assert r.status_code == 200
        assert 'flight' in r.text.lower()

@pytest.mark.asyncio
async def test_project_comment_submit(tmp_path):
    slug = projects[0].get('slug') if projects else 'transaction-master'
    path = DATA_DIR / f"comments_{slug}.json"
    orig = path.read_text() if path.exists() else '[]'
    try:
        async with AsyncClient(app=app, base_url="http://test") as ac:
            r = await ac.post(f"/projects/{slug}/comments", data={'name':'Tester','comment':'nice work'})
            assert r.status_code == 200
            assert 'Tester' in r.text
        comments = json.loads(path.read_text())
        assert any(c.get('name')=='Tester' for c in comments)
    finally:
        path.write_text(orig)

