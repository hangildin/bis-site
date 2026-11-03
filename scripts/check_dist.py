#!/usr/bin/env python3
"""Check optimized published BIS V2 artifact: all routes, images, SEO and contact UX."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit,unquote
import xml.etree.ElementTree as ET
import json,re,sys,os
ROOT=Path(__file__).resolve().parents[1]
DIST=Path(sys.argv[1] if len(sys.argv)>1 else "dist").resolve()
BASE=os.environ.get("BIS_PRODUCTION_URL","https://hangildin.github.io/bis-site-v2/").rstrip("/")+"/"
tree=ET.parse(DIST/"sitemap.xml")
urls=[x.text for x in tree.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
assert len(urls)==25 and len(set(urls))==25
assert (DIST/"assets/bis-enhance.css").is_file()
class Check(HTMLParser):
 def __init__(self):
  super().__init__();self.links=[];self.images=[];self.css=[];self.mains=[];self.canon=[];self.robots=[];self.schemas=[];self._in_schema=False;self._buffer=""
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=="a" and a.get("href"):self.links.append(a["href"])
  if tag=="img" and a.get("src"):self.images.append(a)
  if tag=="link" and a.get("rel")=="stylesheet":self.css.append(a.get("href",""))
  if tag=="link" and a.get("rel")=="canonical":self.canon.append(a.get("href"))
  if tag=="main":self.mains.append(a.get("id"))
  if tag=="meta" and a.get("name")=="robots":self.robots.append(a.get("content",""))
  if tag=="script" and a.get("type")=="application/ld+json":self._in_schema=True;self._buffer=""
 def handle_data(self,data):
  if self._in_schema:self._buffer+=data
 def handle_endtag(self,tag):
  if tag=="script" and self._in_schema:
   self.schemas.append(json.loads(self._buffer));self._in_schema=False
all_webp=set()
for url in urls:
 name=url[len(BASE):] or "index.html"
 doc=DIST/name
 assert doc.is_file(),("Missing page",name)
 s=doc.read_text(encoding="utf-8")
 p=Check();p.feed(s)
 assert p.canon==[url],("canonical",name,p.canon)
 assert len(p.mains)==1 and p.mains[0],("main landmark",name,p.mains)
 assert f'href="#{p.mains[0]}"' in s,("skip target",name,p.mains[0])
 assert not any("noindex" in x.lower() for x in p.robots),("noindex",name)
 assert "assets/bis-enhance.css" in p.css,("ux stylesheet",name)
 assert 'class="bis-mobile-contact"' in s,("mobile contact bar",name)
 assert 'href="tel:+79631223399"' in s,("phone",name)
 assert 'href="https://t.me/+7z9ehE-JLUs0ZjNi"' in s,("telegram",name)
 if BASE!="https://hangildin.github.io/bis-site/":
  assert "https://hangildin.github.io/bis-site/" not in s,("old canonical host",name)
 if not name.startswith("journal-"):
  assert any(x.get("@type")=="Organization" for x in p.schemas),("Organization JSONLD",name)
 for image in p.images:
  src=image["src"]; ref=urlsplit(src)
  if not ref.scheme:
   img=DIST/unquote(ref.path)
   assert img.is_file(),("Missing image",name,src)
   assert image.get("alt") is not None,("Missing alt",name,src)
   if src.endswith(".webp"):
    all_webp.add(src)
    assert image.get("width") and image.get("height"),("Unstable image aspect",name,src)
   for item in re.findall(r'([^\s,]+)\s+\d+w',image.get("srcset","")):
    assert (DIST/item).is_file(),("Broken responsive image",name,item)
 for css in p.css:
  assert (DIST/css).is_file(),("Missing styles",name,css)
 for link in p.links:
  parsed=urlsplit(link)
  if parsed.scheme or link.startswith("#"):continue
  assert (DIST/unquote(parsed.path)).is_file(),("Missing internal route",name,link)
assert len(all_webp)>=25,("Image conversion too limited",len(all_webp))
old=sum(f.stat().st_size for f in (ROOT/"assets").rglob("*") if f.is_file() and f.suffix.lower() in (".jpg",".jpeg",".png"))
new=sum(f.stat().st_size for f in (DIST/"assets").rglob("*") if f.is_file() and f.suffix.lower() in (".jpg",".jpeg",".png",".webp"))
assert new<old*.7,("Images should be >=30% smaller, actual",old,new)
print(f"BIS DIST PASS: {len(urls)} published pages, {len(all_webp)} optimized referenced photos, source {old/1048576:.1f} MiB to {new/1048576:.1f} MiB, all internal routes, responsive images, schema and mobile CTA.")
