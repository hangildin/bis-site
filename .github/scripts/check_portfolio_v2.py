#!/usr/bin/env python3
"""BIS 03 V2-only QA: 7 case cards, real service relationships, safe links and claims."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[2]
CASES={
 "zelenodolsk.html":"city-events.html",
 "himfest.html":"corporate-events.html",
 "kastamonu.html":"brand-events.html",
 "spartakiada.html":"sports-events.html",
 "festival-dobryh-del.html":"city-events.html",
 "phuket-wedding.html":"services.html",
 "plehanov-reu.html":"corporate-events.html",
}
class Links(HTMLParser):
 def __init__(self):
  super().__init__(convert_charrefs=True)
  self.refs=[];self.images=[];self.anchor_depth=0;self.nested_anchors=0;self.cards=[];self.service_links=[];self.nav_links=[];self.css=[];self.h1=0
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=="h1":self.h1+=1
  if tag=="a":
   if self.anchor_depth:self.nested_anchors+=1
   self.anchor_depth+=1
   self.refs.append(a.get("href",""))
   cls=a.get("class","").split()
   if "card" in cls:self.cards.append(a.get("href"))
   if "case-service-link" in cls:self.service_links.append(a.get("href"))
  if tag=="img":self.images.append(a)
  if tag=="link" and a.get("rel")=="stylesheet":self.css.append(a.get("href",""))
 def handle_endtag(self,tag):
  if tag=="a":self.anchor_depth=max(0,self.anchor_depth-1)
def read(path):
 f=ROOT/path
 parser=Links()
 parser.feed(f.read_text(encoding="utf-8"))
 return parser
issues=[]
def check(ok,message):
 if not ok:issues.append(message)
portfolio=read("projects.html")
homepage=(ROOT/"index.html").read_text(encoding="utf-8")
project_src=(ROOT/"projects.html").read_text(encoding="utf-8")
kastamonu_src=(ROOT/"kastamonu.html").read_text(encoding="utf-8")
check(len(portfolio.cards)==7,"Expect 7 genuine project cards")
check(set(portfolio.cards)==set(CASES),"Project roster differs from approved set")
check(len(portfolio.service_links)==7,"Every project card needs an adjacent service link")
check(portfolio.service_links==list(CASES.values()),"Adjacent service links don't match case order")
check(project_src.count('class="case-listing"')==7,"Case wrappers missing")
check(portfolio.h1==1,"Portfolio H1 missing/duplicate")
check(portfolio.nested_anchors==0,"Nested anchors break separate service navigation")
check("assets/bis-portfolio-v2.css" in portfolio.css,"Portfolio stylesheet missing")
check((ROOT/"assets/bis-portfolio-v2.css").is_file(),"Portfolio stylesheet file missing")
check("300 гостей" not in homepage,"Unverified Kastamonu guest count on homepage")
check("300 гостей" not in project_src,"Unverified Kastamonu guest count in project list")
check("300 гостей" not in kastamonu_src and ">300<" not in kastamonu_src,
      "Unverified Kastamonu guest count on case detail")
check("106 элементов для Доски почёта" in project_src,"Zelenodolsk element context not matched")
check("106 элементов для Доски почёта" in (ROOT/"zelenodolsk.html").read_text(encoding="utf-8"),
      "Zelenodolsk detail claim mismatch")
def test_local_links(parser,path):
 for href in parser.refs:
  if not href:continue
  url=urlsplit(href)
  if url.scheme or url.netloc or not url.path:continue
  file=(ROOT/url.path).resolve()
  check(file.is_relative_to(ROOT) and file.is_file(),f"{path}: missing/unsafe link {href}")
 for img in parser.images:
  check("alt" in img,f"{path}: image missing alt text")
  src=img.get("src","")
  if src and not urlsplit(src).scheme:
   file=(ROOT/src).resolve()
   check(file.is_relative_to(ROOT) and file.is_file(),f"{path}: missing/unsafe image {src}")
test_local_links(portfolio,"projects.html")
for name,service in CASES.items():
 parser=read(name)
 source=(ROOT/name).read_text(encoding="utf-8")
 check(parser.h1==1,f"{name}: missing H1")
 check("assets/bis-portfolio-v2.css" in parser.css,f"{name}: styles missing")
 check('class="bis-v2-case-nav"' in source,f"{name}: contextual links missing")
 for href in [service,"projects.html","index.html#contacts"]:
  check(href in parser.refs,f"{name}: missing link {href}")
 check(parser.nested_anchors==0,f"{name}: nested anchors")
 test_local_links(parser,name)
for error in issues:print("ERROR:",error)
if issues:raise SystemExit(1)
print("BIS 03 V2 PASS: 7 projects, 7 service routes, internal links, media and fact flags checked.")
