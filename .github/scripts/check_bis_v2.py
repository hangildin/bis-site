#!/usr/bin/env python3
"""BIS v2: commercial homepage regression and link smoke test (standard library)."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit
import re
ROOT = Path(__file__).resolve().parents[2]
home = (ROOT / "index.html").read_text(encoding="utf-8")
originals = ("Большие</span><span>интересные</span><span><em>события</em></span>",
  "Создаём корпоративные события, городские праздники", "Работаем в России и за рубежом.",
  'href="tel:+79631223399"', 'href="mailto:bis.manager@vk.com"')
services = {"corporate-events.html": "ХимФест",
  "city-events.html": "Зеленодольск", "brand-events.html": "Kastamonu",
  "sports-events.html": "спартакиада"}
errors = []
class Reader(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.h1=0; self.ids=set(); self.anchors=[]; self.images=[];self.cards=0;self.robots=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=="h1": self.h1 += 1
        if "id" in a: self.ids.add(a["id"])
        if tag=="a":
            if a.get("href"): self.anchors.append(a["href"])
            if "bis-service-card" in a.get("class","").split(): self.cards+=1
        if tag=="img": self.images.append(a)
        if tag=="meta" and a.get("name")=="robots":self.robots.append(a.get("content",""))
p=Reader();p.feed(home)
if p.h1!=1: errors.append("Expected one H1")
if p.cards!=5: errors.append("Expected five commercial service cards")
if "services" not in p.ids or "contacts" not in p.ids: errors.append("Broken services / contacts sections")
if not any("noindex" in x for x in p.robots):errors.append("Preview must remain noindex until release")
if '<a href="services.html">Услуги</a>' not in home:errors.append("No services in main navigation")
if '<a class="btn btn-orange" href="#contacts">Обсудить проект' not in home:
    errors.append("Commercial hero CTA missing")
if '<a class="btn btn-outline" href="#services">Наши услуги' not in home:
    errors.append("Secondary services CTA missing")
if re.search(r'\.bis-services-grid\s*\{',home) is None or '@media(max-width:510px)' not in home:
    errors.append("Service mobile styles missing")
if any(x not in home for x in originals):errors.append("Protected verified homepage structure/content modified or removed")
if "12+ лет" in home or "Более 12 лет" in home:errors.append("Unverified years-of-experience claim restored")
for f,case in services.items():
    if f not in p.anchors:errors.append("Missing service route "+f)
    if case.lower() not in home.lower():errors.append("Missing case proof "+case)
    if not (ROOT/f).is_file():errors.append("Missing page "+f)
if "services.html" not in p.anchors:errors.append("Missing catalog route")
if "children-events.html" not in p.anchors:errors.append("Children events route missing")
for image in p.images:
    if image.get("src","").startswith("assets/"):
        target=ROOT/image["src"]
        if not target.is_file(): errors.append("Broken photo "+image["src"])
        if "alt" not in image: errors.append("Missing alt on "+image["src"])
for href in p.anchors:
    parsed=urlsplit(href)
    if not parsed.scheme and not parsed.netloc and parsed.path and not (ROOT/parsed.path).is_file():
        errors.append("Missing local link "+href)
if errors:
    for x in errors:print("ERROR:",x)
    raise SystemExit(1)
print("PASS BIS v2: homepage commercial routes, images, links, protected content, noindex and mobile CSS.")
