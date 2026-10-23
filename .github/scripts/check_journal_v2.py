#!/usr/bin/env python3
"""BIS V2: validate original, navigable editorial pages and primary SEO links."""
from pathlib import Path
from html.parser import HTMLParser
import json,re
ROOT=Path(__file__).resolve().parents[2]
PAGES=["journal-corporate-brief.html","journal-new-year-corporate.html",
"journal-children-birthday.html","journal-kids-festival-zone.html",
"journal-city-festival.html","journal-brand-launch.html",
"journal-company-spartakiad.html","journal-event-budget.html"]
issues=[]
class Parser(HTMLParser):
 def __init__(self):
  super().__init__(convert_charrefs=True)
  self.h1=0;self.h2=0;self.h3=0;self.links=[];self.images=[];self.title=0;self.cards=0
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=="h1":self.h1+=1
  if tag=="h2":self.h2+=1
  if tag=="h3":self.h3+=1
  if tag=="title":self.title+=1
  if tag=="a" and "href" in a:self.links.append(a["href"])
  if tag=="a" and "journal-card" in a.get("class","").split():self.cards+=1
  if tag=="img":self.images.append(a)
def check(ok,description):
 if not ok:issues.append(description)
hub=(ROOT/"journal.html").read_text(encoding="utf-8")
nav=Parser();nav.feed(hub)
check(nav.h1==1,"Journal must have one H1")
check(nav.cards==len(PAGES),"Journal must link eight article cards")
for name in PAGES:
 check(f'href="{name}"' in hub, "Missing journal hub link: "+name)
 src=(ROOT/name).read_text(encoding="utf-8")
 p=Parser();p.feed(src)
 check(p.h1==1 and p.h2>=4 and p.title==1,name+": headings missing")
 check("journal.html" in p.links and "index.html#contacts" in p.links,
       name+": journal/contact route missing")
 check("journal-single" in src and "journal-content" in src,name+": article styling missing")
 check("https://hangildin.github.io/bis-site/"+name in src,name+": canonical missing")
 check(len(p.images)==1 and p.images[0].get("alt",""),name+": editorial image/alt missing")
 for a in p.links:
  if "://" not in a and not a.startswith(("#","mailto:","tel:")):
   check((ROOT/a.split("#")[0]).is_file(),name+": broken link "+a)
 schema=re.findall(r'<script type="application/ld\+json">([\s\S]*?)</script>',src)
 check(len(schema)==1,name+": unique Article schema missing")
 if schema:
  try:
   data=json.loads(schema[0])
   check(data.get("@type")=="Article" and data.get("mainEntityOfPage","").endswith(name),
         name+": Article schema does not match canonical")
  except ValueError:issues.append(name+": invalid Article JSON")
 text=re.sub(r"<[^>]+>"," ",re.sub(r"<script[\s\S]*?</script>","",src))
 check(len(text.split())>=280,name+": thin article content")
check((ROOT/"assets/bis-journal.css").is_file(),"Missing journal stylesheet")
check((ROOT/"sitemap.xml").read_text(encoding="utf-8").count("<loc>")==25,"Missing 25-URL sitemap")
if issues:
 for e in issues:print("ERROR:",e)
 raise SystemExit(1)
print("BIS V2 JOURNAL PASS: 8 unique articles, 1 hub, original content, links, Article JSON-LD and 25 URLs.")
