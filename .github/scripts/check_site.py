#!/usr/bin/env python3
"""Static SEO/link audit for the approved BIS pages. Python standard library only."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
PAGES = (
    "index.html", "projects.html", "letters.html",
    "zelenodolsk.html", "himfest.html", "kastamonu.html",
    "spartakiada.html", "festival-dobryh-del.html",
    "phuket-wedding.html", "plehanov-reu.html",
)
ARCHIVED = ("v2.html", "dark.html", "concept-3.html", "concept-4.html")
BASE = "https://hangildin.github.io/bis-site/"
ERRORS = []


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = 0
        self.h1 = 0
        self.description = []
        self.canonicals = []
        self.robots = []
        self.og = {}
        self.links = []
        self.images = []
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self.title += 1
        if tag == "h1":
            self.h1 += 1
        if tag == "meta":
            if a.get("name", "").lower() == "description":
                self.description.append(a.get("content", ""))
            if a.get("name", "").lower() == "robots":
                self.robots.append(a.get("content", ""))
            if a.get("property", "").startswith("og:"):
                self.og[a["property"]] = a.get("content", "")
        if tag == "link" and a.get("rel", "").lower() == "canonical":
            self.canonicals.append(a.get("href", ""))
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
        if tag == "img":
            self.images.append(a)
        if tag == "script" and a.get("src"):
            self.scripts.append(a["src"])


def error(message):
    ERRORS.append(message)


def check_path(page, raw_url):
    parsed = urlsplit(raw_url)
    if parsed.scheme or parsed.netloc or not parsed.path or raw_url.startswith("#"):
        return
    target = unquote(parsed.path)
    destination = (ROOT / target.lstrip("/") if target.startswith("/") else ROOT / page.parent / target).resolve()
    if not destination.is_relative_to(ROOT) or not destination.is_file():
        error(f"{page.name}: missing or unsafe local link: {raw_url}")


for name in PAGES:
    path = ROOT / name
    if not path.is_file():
        error(f"missing approved page: {name}")
        continue
    page = Page()
    page.feed(path.read_text(encoding="utf-8"))
    expected = BASE + ("" if name == "index.html" else name)
    if page.title != 1 or page.h1 != 1:
        error(f"{name}: expected exactly one title and one H1")
    if len(page.description) != 1 or not page.description[0]:
        error(f"{name}: missing/duplicate meta description")
    if page.canonicals != [expected]:
        error(f"{name}: canonical doesn't match sitemap destination: {page.canonicals}")
    if "noindex" in " ".join(page.robots).lower():
        error(f"{name}: approved page incorrectly noindex")
    if not all(page.og.get(x) for x in ("og:title", "og:description", "og:image", "og:url")):
        error(f"{name}: incomplete Open Graph preview")
    if "assets/bis-analytics.js" not in page.scripts:
        error(f"{name}: missing click-event instrumentation")
    for image in page.images:
        if "alt" not in image:
            error(f"{name}: missing alt attribute on image: {image.get('src')}")
        if image.get("src"):
            check_path(path, image["src"])
    for href in page.links + page.scripts:
        check_path(path, href)

for name in ARCHIVED:
    path = ROOT / name
    if not path.is_file():
        error(f"missing archived concept: {name}")
        continue
    page = Page()
    page.feed(path.read_text(encoding="utf-8"))
    if not any("noindex" in value.lower() for value in page.robots):
        error(f"{name}: archived design not excluded from search index")

sitemap_path = ROOT / "sitemap.xml"
try:
    sitemap = ET.parse(sitemap_path).getroot()
    found = [element.text for element in sitemap.iter() if element.tag.endswith("}loc") or element.tag == "loc"]
    expected_urls = [BASE + ("" if name == "index.html" else name) for name in PAGES]
    if sorted(found) != sorted(expected_urls):
        error(f"sitemap mismatch: expected {len(expected_urls)} approved URLs, found {len(found)}")
except (OSError, ET.ParseError) as exc:
    error(f"sitemap missing or invalid: {exc}")

if ERRORS:
    print("BIS quality audit FAILED:")
    for issue in ERRORS:
        print("  -", issue)
    raise SystemExit(1)
print(f"BIS quality audit OK: {len(PAGES)} approved pages; {len(ARCHIVED)} noindex concepts; sitemap and local paths checked.")
