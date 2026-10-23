#!/usr/bin/env python3
"""Guard BIS v2 24-keyword regional pilot against invented frequencies and bad URLs."""
import csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PILOT=ROOT/".github/seo/topvisor_v2_import_24.csv"
EVIDENCE=ROOT/".github/seo/keyword_pilot_evidence_24.csv"
CURATED=ROOT/".github/seo/BIS_05_ACTUAL_WORDSTAT_QUERIES.csv"
with PILOT.open(encoding="utf-8-sig",newline="") as f:p=list(csv.DictReader(f,delimiter=";"))
with EVIDENCE.open(encoding="utf-8-sig",newline="") as f:e=list(csv.DictReader(f,delimiter=";"))
with CURATED.open(encoding="utf-8-sig",newline="") as f:c=list(csv.DictReader(f,delimiter=";"))
assert len(p)==len(e)==24, f"Expected 24 monitoring rows, got {len(p)}/{len(e)}"
assert len({v["name"] for v in p})==24, "Duplicate pilot queries"
source=ROOT/".github/seo/wordstat_confirmed_18.csv"
with source.open(encoding="utf-8-sig",newline="") as f:
    confirmed=list(csv.DictReader(f,delimiter=";"))
assert len(confirmed)==18, "Expected 18 original Wordstat source records"
original={r["Фраза"]:str(r["Число запросов"]) for r in confirmed}
old={r["Фраза из Wordstat"]:r["Запросы за период"] for r in c}
for phrase,value in original.items():
    if phrase in old:
        assert value==old[phrase],f"Conflicting Wordstat sources for {phrase}"
ev={r["Фраза"]:r for r in e}
measured=hypotheses=0
for row in p:
 phrase=row["name"];record=ev[phrase]
 assert row["target"]=="https://hangildin.github.io/bis-site/"+record["Посадочная"], phrase
 assert (ROOT/record["Посадочная"]).is_file(),phrase
 raw=record["Показы Wordstat за 22.09–22.10.2026 (все регионы)"]
 if raw:
  measured+=1
  assert raw==original.get(phrase),f"Original CSV evidence mismatch for {phrase}: {raw} != {original.get(phrase)}"
  assert "Все регионы" in record["Тип данных"] or "все регионы" in record["Тип данных"].lower(),phrase
 else:
  hypotheses+=1
  assert "Гипотеза" in record["Тип данных"],f"Unmarked unmeasured pilot: {phrase}"
 assert row["group_name"], phrase
assert (measured,hypotheses)==(18,6),(measured,hypotheses)
print("BIS V2 PILOT PASS: 24 SEO phrases; 18 copied exactly from actual all-region Wordstat exports, 6 explicitly unmeasured, correct target URLs.")
