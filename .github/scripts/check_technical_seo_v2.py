#!/usr/bin/env python3
"""BIS V2 technical SEO release-prep audit (not a production publish)."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
BASE="https://hangildin.github.io/bis-site/"
PAGES=["index.html","services.html","corporate-events.html","city-events.html",
"brand-events.html","sports-events.html","children-events.html","projects.html","zelenodolsk.html",
"himfest.html","kastamonu.html","spartakiada.html","festival-dobryh-del.html",
"phuket-wedding.html","plehanov-reu.html","letters.html","journal.html",
"journal-corporate-brief.html","journal-new-year-corporate.html","journal-children-birthday.html",
"journal-kids-festival-zone.html","journal-city-festival.html","journal-brand-launch.html",
"journal-company-spartakiad.html","journal-event-budget.html"]
issues=[]
class Inspect(HTMLParser):
 def __init__(self):
  super().__init__(convert_charrefs=True)
  self.canonical=[];self.og={};self.desc=[];self.robots=[];self.h1=0;self.titles=0;self.img=[]
 def handle_starttag(self, tag, attrs):
  a=dict(attrs)
  if tag=="h1":self.h1+=1
  if tag=="title":self.titles+=1
  if tag=="img" and a.get("src"):self.img.append(a["src"])
  if tag=="link" and a.get("rel")=="canonical":self.canonical.append(a.get("href"))
  if tag=="meta":
   if a.get("name")=="description":self.desc.append(a.get("content"))
   if a.get("name")=="robots":self.robots.append(a.get("content",""))
   if a.get("property","").startswith("og:"):self.og[a["property"]]=a.get("content","")

tree=ET.parse(ROOT/"sitemap.xml")
ns={"sm":"http://www.sitemaps.org/schemas/sitemap/0.9"}
urls=[node.text for node in tree.findall("sm:url/sm:loc",ns)]
expected=[BASE+("" if name=="index.html" else name) for name in PAGES]
if len(urls)!=len(expected) or set(urls)!=set(expected):
 issues.append(f"Sitemap must contain exactly {len(PAGES)} confirmed pages")
if len(set(urls))!=len(urls):issues.append("Sitemap duplicate URLs")
for name in PAGES:
 src=(ROOT/name).read_text(encoding="utf-8")
 p=Inspect();p.feed(src)
 url=BASE+("" if name=="index.html" else name)
 if p.canonical!=[url]:issues.append(f"{name}: canonical mismatch")
 if p.og.get("og:url")!=url:issues.append(f"{name}: og:url mismatch")
 if p.og.get("og:type")!=("article" if name.startswith("journal-") else "website"):
  issues.append(f"{name}: og:type invalid")
 for tag in ("og:title","og:description","og:image"):
  if not p.og.get(tag):issues.append(f"{name}: missing {tag}")
 if p.titles!=1 or p.h1!=1:issues.append(f"{name}: one title/H1 required")
 if len(p.desc)!=1 or not p.desc[0]:issues.append(f"{name}: description missing")
 if name=="index.html":
  if not any("noindex" in m for m in p.robots):
   issues.append("V2 preview index must remain noindex until explicitly approved")
 else:
  if any("noindex" in m for m in p.robots):
   issues.append(f"{name}: accidentally noindexed release content")
 for urlref in [p.og.get("og:image","")]+p.img[:1]:
  if not urlref:continue
  if urlref.startswith(BASE):
   target=urlref[len(BASE):]
  elif urlref.startswith("assets/"):target=urlref
  else:
   issues.append(f"{name}: offsite / unsupported image {urlref}");continue
  if not (ROOT/target).is_file():
   issues.append(f"{name}: missing image {target}")
for problem in issues:print("ERROR:",problem)
if issues:raise SystemExit(1)
print("BIS V2 TECH SEO PASS: exactly 25 real pages, canonical, OG and sitemap consistent; staging noindex enforced.")
