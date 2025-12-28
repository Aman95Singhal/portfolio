"""Export the FastAPI/Jinja site to a static site in the `docs/` folder suitable for GitHub Pages.

- Renders templates using the same data files under `portfolio/data/`.
- Copies images and static assets and generates `docs/index.html`, `docs/styles.css`, and `docs/script.js` at the docs root.
- Rewrites a few dynamic bits (HTMX forms, HTMX attributes) to simple client-side fallbacks where possible.

Run: python scripts/export_static.py
"""
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
import json
import shutil
import re

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / 'portfolio' / 'templates'
STATIC = ROOT / 'portfolio' / 'static'
DATA = ROOT / 'portfolio' / 'data'
DOCS = ROOT / 'docs'

DOCS.mkdir(exist_ok=True)

env = Environment(loader=FileSystemLoader(str(TEMPLATES)), autoescape=select_autoescape(['html','xml']))

profile = json.loads((DATA / 'profile.json').read_text())
projects = json.loads((DATA / 'projects.json').read_text())

def render_to(path: Path, template_name: str, context: dict):
    html = env.get_template(template_name).render(**context)
    # Basic post-processing for static site:
    # - Replace /static/css/styles.css -> styles.css (use relative paths)
    html = html.replace('/static/css/styles.css', 'styles.css')
    # - Replace script includes (remove HTMX/Alpine/Chart.js includes since we'll include our combined script)
    html = re.sub(r'<script[^>]+htmx.org[^<]*<\/script>\s*', '', html, flags=re.I)
    html = re.sub(r'<script[^>]+alpinejs[^<]*<\/script>\s*', '', html, flags=re.I)
    html = re.sub(r'<script[^>]+chart.js[^<]*<\/script>\s*', '', html, flags=re.I)
    # - Replace references to static JS files with script.js (relative)
    html = html.replace('/static/js/lightbox.js', 'script.js')
    html = html.replace('/static/js/admin.js', 'script.js')
    # - Make image and static URLs relative (remove leading slash for /static/...)
    html = html.replace('src="/static/', 'src="static/')
    html = html.replace('href="/static/', 'href="static/')
    # - Also replace any remaining /static/... occurrences (e.g., in srcset) -> static/...
    html = html.replace('/static/', 'static/')

    # - Fix internal links so they point to the generated static pages (no leading slash)
    html = html.replace('href="/"', 'href="index.html"')
    html = html.replace('href="/about"', 'href="about.html"')
    html = html.replace('href="/projects"', 'href="projects.html"')
    html = html.replace('href="/contact"', 'href="contact.html"')
    # - Convert project links like /projects/slug to projects/slug/ (so GitHub Pages serves the folder)
    html = re.sub(r'href="/projects/([^"]+)"', r'href="projects/\1/"', html)

    # - Replace HTMX form for contact with a Formspree placeholder (so the form works as a simple POST)
    html = re.sub(r'<form[^>]+hx-post=[\"\"][^\"]+[\"\"][^>]*>', '<form method="POST" action="https://formspree.io/f/YOUR_FORM_ID">', html, flags=re.I)
    # - Remove hx- attributes left on elements (non-functional in static)
    html = re.sub(r'\s?hx-[a-zA-Z0-9:-]+="[^"]*"', '', html)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html)
    print('Wrote', path)

# Render pages
context_common = {'profile': profile, 'projects': projects, 'year': 2025}
# index
render_to(DOCS / 'index.html', 'index.html', {**context_common})
# about
render_to(DOCS / 'about.html', 'about.html', {**context_common})
# projects list
# compute tags like in app
tags = sorted({t for p in projects for t in p.get('tech', [])})
render_to(DOCS / 'projects.html', 'projects.html', {**context_common, 'tags': tags})
# project detail pages
for p in projects:
    slug = p.get('slug')
    out = DOCS / 'projects' / slug / 'index.html'
    render_to(out, 'project_detail.html', {**context_common, 'project': p})

# contact
render_to(DOCS / 'contact.html', 'contact.html', {**context_common})

# copy styles to docs root
styles_src = STATIC / 'css' / 'styles.css'
styles_dst = DOCS / 'styles.css'
shutil.copyfile(styles_src, styles_dst)
print('Copied', styles_dst)

# Build a single script.js by concatenating lightbox and a small static-site helper
script_dst = DOCS / 'script.js'
with script_dst.open('w') as out:
    # lightbox (if exists)
    lb = STATIC / 'js' / 'lightbox.js'
    if lb.exists():
        out.write('/* lightbox.js (bundled) */\n')
        out.write(lb.read_text())
        out.write('\n')
    # admin.js functionality adapted for static (SSE not used)
    out.write('/* static-site.js (generated) */\n')
    out.write('document.addEventListener("DOMContentLoaded", function(){\n')
    out.write("  // Projects client-side search\n")
    out.write("  const search = document.querySelector('input[placeholder=\"Search projects...\"]');\n")
    out.write("  if (search) {\n")
    out.write("    const list = document.getElementById('projects-list');\n")
    out.write("    search.addEventListener('input', function(){\n")
    out.write("      const q = this.value.toLowerCase();\n")
    out.write("      Array.from(list.querySelectorAll('.project-card')).forEach(function(card){\n")
    out.write("        const text = card.textContent.toLowerCase();\n")
    out.write("        card.parentElement.style.display = text.indexOf(q) !== -1 ? '' : 'none';\n")
    out.write("      });\n")
    out.write("    });\n")
    out.write("  }\n")
    out.write("  // simple contact form fallback: replace form action placeholder note\n")
    out.write("  const forms = document.querySelectorAll('form[action*=formspree]');\n")
    out.write("  forms.forEach(f => {\n")
    out.write("    f.addEventListener('submit', function(){\n")
    out.write("      // show a quick alert; user should replace YOUR_FORM_ID in HTML with a real ID\n")
    out.write("      setTimeout(() => alert('Form submitted (static) - configure Formspree with your form ID to actually receive emails.'), 100);\n")
    out.write("    });\n")
    out.write("  });\n")
    out.write('});\n')
print('Built', script_dst)

# copy images
img_src = STATIC / 'img'
img_dst = DOCS / 'static' / 'img'
if img_dst.exists():
    shutil.rmtree(img_dst)
shutil.copytree(img_src, img_dst)
print('Copied images to', img_dst)

print('\nStatic export complete.\n')
print('To publish on GitHub Pages:')
print('1. Commit the `docs/` directory and push to your repo (GitHub Pages -> Source: `docs/` folder).')
print('2. Replace the placeholder Formspree ID in docs/contact.html if you want working contact forms.')
print('3. Enable GitHub Pages from repository settings and pick `docs/` as the source.')
