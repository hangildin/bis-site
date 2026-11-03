#!/usr/bin/env python3
"""Offline production smoke test: 25 pages, release URLs, links and Yandex ad drafts."""
import csv, json, re, subprocess, sys, tempfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit,unquote
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
BASE="https://example.org/bis-commercial-v2/"
class Links(HTMLParser):
 def __init__(self):
  super().__init__(convert_charrefs=True)
  self.links=[];self.images=[];self.canonical=[];self.robots=[];self.title=[];self.headings=0
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=="a" and a.get("href"):self.links.append(a["href"])
  if tag=="img" and a.get("src"):self.images.append(a["src"])
  if tag=="h1":self.headings+=1
  if tag=="link" and a.get("rel")=="canonical":self.canonical.append(a.get("href"))
  if tag=="meta" and a.get("name")=="robots":self.robots.append(a.get("content",""))
def check(condition,msg):
 if not condition:raise AssertionError(msg)

with tempfile.TemporaryDirectory() as temp:
 output=Path(temp)/"release"
 subprocess.run([sys.executable,str(ROOT/"scripts/build_release.py"),
                 "--base-url",BASE,"--out",str(output),"--publish"],check=True,
                 stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 tree=ET.parse(output/"sitemap.xml")
 ns={"s":"http://www.sitemaps.org/schemas/sitemap/0.9"}
 urls=[x.text for x in tree.findall("s:url/s:loc",ns)]
 check(len(urls)==25 and len(set(urls))==25,"Production sitemap must list 25 unique pages")
 check((output/"robots.txt").read_text(encoding="utf-8").find("Allow: /")>=0,"Robots not published")
 check((output/".nojekyll").exists(),"GitHub Pages nojekyll missing")
 for url in urls:
  check(url.startswith(BASE),f"Invalid new domain in sitemap: {url}")
  name=url[len(BASE):] or "index.html"
  page=output/name
  check(page.is_file(),f"Missing page {name}")
  src=page.read_text(encoding="utf-8")
  check("https://hangildin.github.io/bis-site/" not in src,f"Old main-site URLs remain: {name}")
  p=Links();p.feed(src)
  check(p.canonical==[url],f"Canonical mismatch on {name}")
  check(p.headings==1,f"Wrong H1 count on {name}")
  check(not any("noindex" in v.lower() for v in p.robots),f"Page incorrectly noindexed: {name}")
  for link in p.links+p.images:
   parsed=urlsplit(link)
   if parsed.scheme in ("https","http","mailto","tel") or link.startswith("#"):continue
   check(not parsed.netloc and parsed.path,f"Unexpected local link: {link} at {name}")
   check((output/unquote(parsed.path)).is_file(),f"Broken internal link: {link} from {name}")
  if name.startswith("journal-"):
   matched=re.findall(r'<script type="application/ld\+json">(.*?)</script>',src,re.S)
   check(len(matched)==1,"Article structured data missing on "+name)
   data=json.loads(matched[0])
   check(data["mainEntityOfPage"]==url,"Incorrect Article URL for "+name)
 check((output/"assets/bis-journal.css").is_file(),"Journal CSS not packaged")
 # Ads are drafts only, but review their technical fields before human moderation.
 with (ROOT/"ads/BIS_DIRECT_KEYWORDS.csv").open(encoding="utf-8-sig",newline="") as f:
  keywords=list(csv.DictReader(f,delimiter=";"))
 with (ROOT/"ads/BIS_DIRECT_ADS.csv").open(encoding="utf-8-sig",newline="") as f:
  ads=list(csv.DictReader(f,delimiter=";"))
 check(len(keywords)>=60 and len(ads)>=12,"Incomplete ad campaign seed")
 valid={u[len(BASE):] or "index.html" for u in urls}
 for r in keywords:
  check(r["Посадочная (относительный путь)"] in valid,"Missing keyword landing")
  check(r["Частотность Wordstat 22.09–22.10.2026: все регионы"].strip()=="" or
        r["Тип цифры"].startswith("Из 5 исходных CSV"),"Unverified Wordstat frequency present")
 for r in ads:
  title=r["Заголовок"];body=r["Текст объявления"]
  check(len(title)<=56 and len(body)<=81,f"Yandex ad exceeds character limit: {title}")
  check(all(len(word)<=22 for word in title.split()),f"Yandex title word limit: {title}")
  check(all(len(word)<=23 for word in body.split()),f"Yandex body word limit: {body}")
  check(r["Посадочная страница"] in valid,"Missing ad landing")
 print(f"BIS V2 RELEASE PASS: {len(urls)} working static pages, noindex removed, canonical/sitemap rewritten, {len(keywords)} ad phrases, {len(ads)} draft ads.")
