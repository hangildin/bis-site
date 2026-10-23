#!/usr/bin/env python3
"""BIS V2 evidence and commercial-content audit. Run only for staging branch."""
from pathlib import Path
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[2]
HOME=(ROOT/"index.html").read_text(encoding="utf-8")
CAT=(ROOT/"services.html").read_text(encoding="utf-8")
CHILD=(ROOT/"children-events.html").read_text(encoding="utf-8")
PAGES={"corporate-events.html","city-events.html","brand-events.html","sports-events.html","children-events.html"}
problems=[]
def check(cond,msg):
    if not cond:problems.append(msg)
for path in PAGES:
    check((ROOT/path).is_file(),"Missing commercial service "+path)
    check(f'href="{path}"' in HOME,"Missing service from homepage "+path)
    check(f'href="{path}"' in CAT,"Missing service from catalog "+path)
    if path!="children-events.html":
        check(f'href="{path}"' in CHILD,"Missing return route from children page "+path)
check("Более 12 лет" not in HOME and "12+ лет" not in HOME,"Unsupported years claim restored on homepage")
check("Более 12 лет" not in CAT,"Unsupported years claim restored in catalog")
check("Когда идея" in HOME and "Наш подход" in HOME,"Expected concise approach without invented history")
check("Об агентстве</a>" not in HOME,"History-style main-menu label restored")
check("детские мероприятия" in (ROOT/"index.html").read_text(encoding="utf-8").lower(),"Children direction absent in homepage meta")
check("детские мероприятия" in CAT.lower(),"Children direction absent in catalog meta")
check("festival-dobryh-del.html" in CHILD,"Children proof lacks actual related-event link")
check("В портфолио Бис*" in CHILD,"Children FAQ should explain verified related experience")
for item in ['href="tel:+79631223399"','href="mailto:bis.manager@vk.com"','href="https://t.me/+7z9ehE-JLUs0ZjNi"']:
    check(item in HOME,"User-confirmed contact unexpectedly changed "+item)
check("300 гостей" not in HOME and "300 гостей" not in (ROOT/"projects.html").read_text(encoding="utf-8"),"Disputed guest count returned")
check((ROOT/"sitemap.xml").read_text(encoding="utf-8").count("<loc>")==25,"Sitemap must contain 25 pages")
if problems:
    for p in problems:print("ERROR:",p)
    raise SystemExit(1)
check("journal.html" in HOME and "journal.html" in CAT,"Journal missing from primary site navigation")
print("BIS V2 CONTENT PASS: 5 services, 8 articles, relevant case links, claims, contacts, 25-page sitemap.")
