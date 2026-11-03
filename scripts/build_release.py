#!/usr/bin/env python3
"""Package BIS Commercial V2 into a self-contained static GitHub Pages release.

No network, no forms/CRM, no credentials. Main branch of source repo is untouched.
Production URLs and canonical tags are set from --base-url at build time.
Use only after choosing a separate GitHub Pages repository/domain.
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
STAGING = "https://hangildin.github.io/bis-site/"
def urls():
    tree=ET.parse(ROOT/"sitemap.xml")
    ns={"s":"http://www.sitemaps.org/schemas/sitemap/0.9"}
    vals=[x.text for x in tree.findall("s:url/s:loc",ns)]
    if len(vals)!=25 or not all(x and x.startswith(STAGING) for x in vals):
        raise ValueError("Expected 25 confirmed staging URLs in sitemap.xml")
    return vals

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--base-url",required=True,
      help="HTTPS destination, e.g. https://hangildin.github.io/bis-site-v2/")
    ap.add_argument("--out",type=Path,default=Path("dist"))
    ap.add_argument("--allow-primary-site",action="store_true",
      help="User approved promotion to the existing BIS primary public address")
    ap.add_argument("--publish",action="store_true",
      help="Explicitly remove staged noindex and emit crawlable robots.txt")
    a=ap.parse_args()
    url=a.base_url.rstrip("/")+"/"
    parsed=urlsplit(url)
    if parsed.scheme!="https" or not parsed.hostname or parsed.query or parsed.fragment or parsed.username:
        ap.error("--base-url must be an ordinary public HTTPS base URL")
    if url==STAGING and not a.allow_primary_site:
        ap.error("Publishing to BIS main site requires --allow-primary-site")
    target=(ROOT/a.out).resolve()
    if target==ROOT or ROOT in target.parents and target.name in ("assets","scripts"):
        ap.error("Unsafe output folder")
    # Clean stale pages so they do not appear in a subsequent deployment.
    if target.exists():shutil.rmtree(target)
    target.mkdir(parents=True)
    shutil.copytree(ROOT/"assets",target/"assets")
    for old in urls():
        name=old[len(STAGING):] or "index.html"
        src=ROOT/name
        if not src.is_file():raise FileNotFoundError(name)
        content=src.read_text(encoding="utf-8").replace(STAGING,url)
        if a.publish:
            content=re.sub(r'<meta\s+name="robots"\s+content="noindex,\s*nofollow"\s*/?>',"",content,flags=re.I)
            content=content.replace("<!-- BIS v2 preview only: REMOVE noindex before any future release -->","")
        # Adds conversion routes without forms or external tracking; original HTML is unchanged.
        main_tag=re.search(r'<main\b[^>]*>',content,re.I)
        if not main_tag:
            raise ValueError("Page missing a main landmark: "+name)
        existing_id=re.search(r'\bid="([^"]+)"',main_tag.group())
        main_id=existing_id.group(1) if existing_id else "main-content"
        if not existing_id:
            content=content[:main_tag.start()]+main_tag.group()[:-1]+' id="main-content">'+content[main_tag.end():]
        skip='<a class="skip-to-content" href="#'+main_id+'">К основному содержимому</a>'
        mobile=(
            '<nav class="bis-mobile-contact" aria-label="Быстрая связь с агентством">'
            '<a href="tel:+79631223399" data-bis-goal="phone_click" aria-label="Позвонить в Бис*">Позвонить</a>'
            '<a href="https://t.me/+7z9ehE-JLUs0ZjNi" target="_blank" rel="noopener noreferrer" '
            'data-bis-goal="telegram_click" aria-label="Написать агентству Бис* в Telegram">Telegram ↗</a>'
            '</nav>'
        )
        if '<body>' in content and '</body>' in content:
            content=content.replace('<body>', '<body>'+skip,1)
            content=content.replace('</body>',mobile+'</body>',1)
        if '</head>' in content:
            content=content.replace('</head>',
                '<link rel="stylesheet" href="assets/bis-enhance.css"></head>',1)
            # Don't duplicate Article JSON-LD. Search-facing organization claims use verified contacts only.
            if not name.startswith('journal-'):
                entity={
                    "@context":"https://schema.org",
                    "@type":"Organization",
                    "name":"Бис* — Большие интересные события",
                    "url":url,
                    "telephone":"+79631223399",
                    "email":"bis.manager@vk.com",
                    "description":"Агентство корпоративных, городских, брендовых, спортивных и детских мероприятий",
                }
                markup='<script type="application/ld+json">'+json.dumps(
                    entity,ensure_ascii=False).replace('<','\\u003c')+'</script>'
                content=content.replace('</head>',markup+'</head>',1)
        (target/name).write_text(content,encoding="utf-8")
    # self-contained paths needed by deployed html; do not expose repo internals.
    (target/"sitemap.xml").write_text(
      '<?xml version="1.0" encoding="UTF-8"?>\n'
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
      +"\n".join(f"  <url><loc>{url+(old[len(STAGING):] or '')}</loc></url>" for old in urls())
      +'\n</urlset>\n',encoding="utf-8")
    robots=f"User-agent: *\n{'Allow: /' if a.publish else 'Disallow: /'}\nSitemap: {url}sitemap.xml\n"
    (target/"robots.txt").write_text(robots,encoding="utf-8")
    (target/".nojekyll").write_text("",encoding="utf-8")
    print("BIS V2 RELEASE BUILD", "PUBLIC" if a.publish else "PREVIEW/NOINDEX",
          "pages:",len(urls()),"base:",url,"output:",target)
if __name__=="__main__":main()
