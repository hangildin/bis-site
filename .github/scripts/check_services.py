#!/usr/bin/env python3
"""Checks new BIS commercial pages and their routes. No third-party dependencies."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
PAGES = ["services.html", "corporate-events.html", "city-events.html", "brand-events.html", "sports-events.html", "children-events.html"]
CASES = {"corporate-events.html": "himfest.html", "city-events.html": "zelenodolsk.html",
         "brand-events.html": "kastamonu.html", "sports-events.html": "spartakiada.html"}
errors = []

class Inspect(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.h1 = 0
        self.title = 0
        self.ids = set()
        self.anchor_hrefs = []
        self.imgs = []
        self.styles = []
        self.description = []
        self.canonical = []
        self.og = {}
        self.forms = 0
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"): self.ids.add(a["id"])
        if tag == "h1": self.h1 += 1
        if tag == "title": self.title += 1
        if tag == "form": self.forms += 1
        if tag == "a" and "href" in a: self.anchor_hrefs.append(a["href"])
        if tag == "img": self.imgs.append(a)
        if tag == "link" and a.get("rel") == "stylesheet": self.styles.append(a.get("href"))
        if tag == "link" and a.get("rel") == "canonical": self.canonical.append(a.get("href"))
        if tag == "meta" and a.get("name") == "description": self.description.append(a.get("content"))
        if tag == "meta" and a.get("property", "").startswith("og:"):
            self.og[a.get("property")] = a.get("content")
def parse(name):
    p = Inspect()
    p.feed((ROOT/name).read_text(encoding="utf-8"))
    return p

cache = {}
for page in PAGES + ["index.html","projects.html"]:
    if not (ROOT/page).is_file(): errors.append(f"Missing HTML page: {page}")
    else: cache[page] = parse(page)
if not (ROOT/"assets/bis-services.css").is_file(): errors.append("Missing shared CSS")
else:
    css = (ROOT/"assets/bis-services.css").read_text(encoding="utf-8")
    if "@media(max-width:760px)" not in css or "@media(max-width:520px)" not in css:
        errors.append("Missing tablet/mobile CSS breakpoints")

for name in PAGES:
    if name not in cache: continue
    p = cache[name]
    if p.title != 1 or p.h1 != 1: errors.append(f"{name}: title or H1 count incorrect")
    if len(p.description) != 1 or not p.description[0]: errors.append(f"{name}: missing description")
    if p.canonical != [f"https://hangildin.github.io/bis-site/{name}"]:
        errors.append(f"{name}: canonical mismatch")
    if any(not p.og.get(x) for x in ["og:title","og:description","og:url","og:image"]):
        errors.append(f"{name}: incomplete social preview")
    if "assets/bis-services.css" not in p.styles: errors.append(f"{name}: shared CSS not loaded")
    if p.forms: errors.append(f"{name}: form published without consent/receiver approval")
    if "index.html#contacts" not in p.anchor_hrefs: errors.append(f"{name}: missing conversion CTA")
    for img in p.imgs:
        if not img.get("src") or not img.get("alt"):
            errors.append(f"{name}: missing img source or meaningful alt")
        else:
            target=(ROOT/img["src"]).resolve()
            if not target.is_relative_to(ROOT) or not target.is_file():
                errors.append(f"{name}: missing image {img['src']}")
    if name != "services.html":
        if name in CASES and CASES[name] not in p.anchor_hrefs:
            errors.append(f"{name}: missing real case link")
        for other in PAGES:
            if other != name and other not in p.anchor_hrefs:
                errors.append(f"{name}: cannot reach {other}")

    for href in p.anchor_hrefs:
        uri = urlsplit(href)
        if uri.scheme or uri.netloc: continue
        target = unquote(uri.path) or name
        if not (ROOT/target).resolve().is_relative_to(ROOT):
            errors.append(f"{name}: unsafe local href {href}"); continue
        path = ROOT/target
        if not path.is_file(): errors.append(f"{name}: broken href {href}"); continue
        if uri.fragment and path.suffix == ".html":
            target_page = cache.get(target)
            if target_page is None:
                target_page = parse(target)
                cache[target] = target_page
            if unquote(uri.fragment) not in target_page.ids:
                errors.append(f"{name}: missing anchor #{uri.fragment} in {target}")

for referrer in ["index.html", "projects.html"]:
    if referrer in cache and "services.html" not in cache[referrer].anchor_hrefs:
        errors.append(f"{referrer}: no link to commercial pages")

for err in errors: print("ERROR:", err)
if errors: raise SystemExit(1)
print(f"OK: {len(PAGES)} commercial pages, shared CSS, images, links, case evidence, SEO and CTAs checked.")
