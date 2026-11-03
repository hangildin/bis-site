#!/usr/bin/env python3
"""Read-only smoke test against PUBLIC BIS V2. Not a ranking or conversion claim."""
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from urllib.request import Request,urlopen
from urllib.error import URLError, HTTPError
import os,time,xml.etree.ElementTree as ET

BASE=os.environ.get("BIS_PRODUCTION_URL","https://hangildin.github.io/bis-site-v2/").rstrip("/")+"/"
class Page(HTMLParser):
 def __init__(self):
  super().__init__(convert_charrefs=True)
  self.h1=0;self.main=0;self.canonical=[];self.descriptions=[];self.robots=[];self.assets=[];self.links=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=="h1":self.h1+=1
  if tag=="main":self.main+=1
  if tag=="link" and a.get("rel")=="canonical":self.canonical.append(a.get("href"))
  if tag=="meta" and a.get("name")=="description":self.descriptions.append(a.get("content",""))
  if tag=="meta" and a.get("name")=="robots":self.robots.append(a.get("content",""))
  if tag=="img" and a.get("src"):self.assets.append(a["src"])
  if tag=="a" and a.get("href"):self.links.append(a["href"])
def get(path,attempts=3):
 assert path.startswith(BASE),path
 for i in range(attempts):
  try:
   with urlopen(Request(path,headers={"User-Agent":"BIS-Public-Technical-QA/1.0"}),timeout=25) as r:
    assert r.status==200,(path,r.status)
    return r.read(),r.headers.get("Content-Type","")
  except (HTTPError,URLError,TimeoutError):
   if i==attempts-1:raise
   time.sleep(3*(i+1))
def main():
 sitemap,_=get(BASE+"sitemap.xml")
 ns="{http://www.sitemaps.org/schemas/sitemap/0.9}"
 urls=[e.text for e in ET.fromstring(sitemap).findall(ns+"url/"+ns+"loc")]
 assert len(urls)==25 and len(set(urls))==25 and all(x.startswith(BASE) for x in urls)
 robots,_=get(BASE+"robots.txt")
 assert b"Allow: /" in robots and b"Disallow: /" not in robots
 assert ("Sitemap: "+BASE+"sitemap.xml").encode() in robots
 assets=set()
 journal=0
 for url in urls:
  body,ctype=get(url)
  assert "text/html" in ctype.lower(),(url,ctype)
  s=body.decode("utf-8")
  p=Page();p.feed(s)
  assert p.h1==1 and p.main==1,("landmarks",url)
  assert p.canonical==[url],("canonical",url,p.canonical)
  assert len(p.descriptions)==1 and len(p.descriptions[0])>50,("description",url)
  assert not any("noindex" in x for x in p.robots),("noindex",url)
  assert 'class="bis-mobile-contact"' in s,("mobile contact",url)
  assert 'href="tel:+79631223399"' in s,("phone",url)
  assert 'https://t.me/+7z9ehE-JLUs0ZjNi' in s,("telegram",url)
  if BASE!="https://hangildin.github.io/bis-site/":
   assert "https://hangildin.github.io/bis-site/" not in s,("old-site url",url)
  if url.rsplit("/",1)[-1].startswith("journal-"):
   journal+=1
   assert '"@type": "Article"' in s or '"@type":"Article"' in s,("article schema",url)
  for href in p.links:
   linked=urljoin(url,href).split("#")[0].split("?")[0]
   if linked==BASE+"index.html":linked=BASE
   if linked.startswith(BASE) and linked.endswith(".html"):
    assert linked in urls,("internal link not in sitemap",url,linked)
  for src in p.assets[:2]:
   linked=urljoin(url,src)
   if linked.startswith(BASE):assets.add(linked)
 assert journal==8,("journal articles",journal)
 for img in sorted(assets)[:12]:
  body,ctype=get(img,attempts=2)
  assert body and ctype.startswith("image/"),("image",img,ctype)
 for css in ("assets/bis-services.css","assets/bis-journal.css","assets/bis-enhance.css"):
  body,ctype=get(BASE+css,attempts=2)
  assert len(body)>100,("stylesheet",css)
 summary=(f"BIS PUBLIC QA PASS: {len(urls)} real 200 HTML pages, {journal} articles, "
          f"{min(len(assets),12)} image samples, 3 CSS; correct canonical, sitemap, "
          "no noindex, direct mobile contacts. This does NOT prove search ranking or sales.")
 print(summary)
 if os.environ.get("GITHUB_STEP_SUMMARY"):
  with open(os.environ["GITHUB_STEP_SUMMARY"],"a",encoding="utf-8") as f:f.write(summary+"\n")
if __name__=="__main__":main()
