#!/usr/bin/env python3
"""BIS V2 semantic content / regional research audit, no external access required."""
import csv
from html.parser import HTMLParser
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PAGES=["corporate-events.html","city-events.html","brand-events.html","sports-events.html","children-events.html"]
LANDINGS=set(PAGES+["services.html"])
issues=[]
class Inspect(HTMLParser):
 def __init__(self):
  super().__init__(convert_charrefs=True)
  self.h1=0;self.h2=0;self.qa=0;self.anchor=set();self.section=0;self.form=0
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=="h1":self.h1+=1
  if tag=="h2":self.h2+=1
  if tag=="form":self.form+=1
  if tag=="section" and "bis-seo-guide" in a.get("class","").split():self.section+=1
  if tag=="article" and "bis-seo-question" in a.get("class","").split():self.qa+=1
  if tag=="a" and a.get("href"):self.anchor.add(a["href"])
for name in PAGES:
 src=(ROOT/name).read_text(encoding="utf-8")
 html=Inspect();html.feed(src)
 if html.section!=1 or html.qa!=4:issues.append(f"{name}: expected SEO planning section + 4 unique answers")
 if html.h1!=1 or html.h2<3:issues.append(f"{name}: content headings incomplete")
 if html.form:issues.append(f"{name}: unexpected PII-collecting form")
 if not {"projects.html","index.html#contacts"}.issubset(html.anchor):
  issues.append(f"{name}: missing case/contact navigation")
 if src.count('id="bis-seo-guide-heading"')!=1:issues.append(f"{name}: duplicate guide heading")
 if src.count("<meta name=\"description\"")!=1:issues.append(f"{name}: meta description count")
corporate=(ROOT/"corporate-events.html").read_text(encoding="utf-8")
if 'id="new-year-corporate"' not in corporate or 'Организация новогоднего' not in corporate:
 issues.append("Seasonal corporate coverage absent despite measured queries")
css=(ROOT/"assets/bis-services.css").read_text(encoding="utf-8")
if ".bis-seo-questions" not in css or "max-width:760px" not in css:
 issues.append("Missing responsive stylesheet for editorial content")
path=ROOT/".github/seo/keywords-v2.csv"
with path.open(encoding="utf-8",newline="") as f:
 rows=list(csv.DictReader(f,delimiter=";"))
if len(rows)!=72:issues.append(f"Expected 72 seed rows, got {len(rows)}")
unique=set()
for index,row in enumerate(rows,2):
 key=(row["Регион в исходной гипотезе"],row["Фраза с модификатором"])
 if key in unique:issues.append(f"Duplicate region/query: line {index}")
 unique.add(key)
 if row["Посадочная страница BIS V2"] not in LANDINGS:
  issues.append(f"Missing landing mapping: line {index}")
 if any(row[col].strip() for col in ("Wordstat частота (не получена)","Яндекс Директ CPC (не получен)","Дата реальных данных")):
  issues.append(f"Unproven search metrics present: line {index}")
if issues:
 for item in issues:print("ERROR:",item)
 raise SystemExit(1)
print("BIS V2 SEO PASS: 5 unique service guides, 20 questions, 72 regional seed pairs, zero fabricated figures.")
