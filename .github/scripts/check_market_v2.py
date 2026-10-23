#!/usr/bin/env python3
"""BIS 05: audit evidence matrix and avoid manufactured Wordstat metrics."""
import csv
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
file=ROOT/".github/seo/competitor_matrix_v2_2026-10-23.csv"
with file.open("r",encoding="utf-8-sig",newline="") as f:
    rows=list(csv.DictReader(f,delimiter=";"))
seed=ROOT/".github/seo/keywords-v2.csv"
with seed.open("r",encoding="utf-8-sig",newline="") as f:
    queries=list(csv.DictReader(f,delimiter=";"))
err=[]
def check(ok,message):
    if not ok:err.append(message)
expected={"Казань","Москва","Санкт-Петербург","Уфа","Самара","Екатеринбург",
          "Нижний Новгород","Сочи","Новосибирск","Краснодар","Красноярск"}
cities={r["Город"] for r in rows}
check(len(rows)==23,"23 verified competitor entries required, got "+str(len(rows)))
check(cities==expected,"City coverage mismatch: "+str(cities^expected))
names=set()
for i,r in enumerate(rows,2):
    key=(r["Город"],r["Агентство"])
    check(key not in names,f"Duplicate competitor at {i}")
    names.add(key)
    check(r["Официальный сайт (источник)"].startswith("https://"),f"Missing primary HTTPS source at {i}")
    check(r["SEO-позиция / видимость"]=="не измерена",f"Unverified ranking at {i}")
    check(r["Wordstat частота"]=="не получена",f"Unverified demand at {i}")
check(len(queries)==72,"Keyword hypothesis count unexpectedly changed")
collector=(ROOT/".github/scripts/wordstat_collect.py").read_text(encoding="utf-8")
check("searchapi.api.cloud.yandex.net/v2/wordstat" in collector,"Wordstat v2 endpoint missing")
check("api.wordstat.yandex.net/v1" not in collector,"Obsolete Wordstat v1 collector detected")
check("if not args.execute:" in collector,"Cost-guarding dry-run required")
check("--execute" in collector,"Manual enable flag missing")
report=(ROOT/".github/seo/BIS_05_MARKET_RESEARCH.md").read_text(encoding="utf-8")
check("рейтинг позиций" in report.lower() and "не** рейтинг" in report.lower(),"Research disclaimer missing")
if err:
    for e in err:print("ERROR:",e)
    raise SystemExit(1)
print("BIS 05 market evidence PASS: 23 agencies, 11 cities, 72 seed hypotheses, no false demand figures, v2 API guarded.")
