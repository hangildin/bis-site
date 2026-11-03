#!/usr/bin/env python3
"""BIS V2: offline regression tests for Wordstat CSV importer and sourced research."""
import csv
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
APP=ROOT/".github/scripts/import_wordstat_export.py"
REPORT=ROOT/".github/seo/BIS_05_WORDSTAT_USER_EXPORTS_ANALYSIS.md"
CURATED=ROOT/".github/seo/BIS_05_ACTUAL_WORDSTAT_QUERIES.csv"
assert REPORT.is_file() and CURATED.is_file()
report=REPORT.read_text(encoding="utf-8")
for term in ["4 743", "4 719", "24 повторяющиеся", "все регионы", "22.09.2026"]:
    assert term in report, f"Report missing grounded detail: {term}"
with CURATED.open(encoding="utf-8-sig",newline="") as f:
    curated=list(csv.DictReader(f,delimiter=";"))
assert len(curated)==40, f"Expected curated evidence of 40 rows, got {len(curated)}"
assert {r["Регион Wordstat"] for r in curated}=={"Все регионы"}
assert {r["Устройства"] for r in curated}=={"Все устройства"}
core={(r["Фраза из Wordstat"],r["Запросы за период"]) for r in curated}
assert ("организация корпоративных мероприятий","1548") in core
assert ("организация корпоративных мероприятий казань","8") in core
assert ("организация корпоратива","2184") in core
assert ("детский день рождения под ключ","723") in core

with tempfile.TemporaryDirectory() as temp:
    root=Path(temp)
    header="Запросы со словами;Число запросов;Топ частотных запросов «корпоратив», 22.09.2026 — 22.10.2026, все регионы, все устройства\r\n"
    one=root/"wordstat_a.csv"
    two=root/"wordstat_b.csv"
    one.write_text(header+"организация корпоратива;2184;\r\nгде провести корпоратив;5270;\r\n",encoding="utf-8-sig")
    two.write_text(header+"где провести корпоратив;5270;\r\nдетский день рождения под ключ;723;\r\n",encoding="utf-8-sig")
    output=root/"results.csv"
    result=subprocess.run([sys.executable,str(APP),"--out",str(output),str(one),str(two)],
                         capture_output=True,text=True,check=True)
    assert "4 rows; 3 distinct queries; 1 duplicate rows" in result.stdout
    with output.open(encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f,delimiter=";"))
    assert len(rows)==3
    seen={r["Запрос"]:r for r in rows}
    assert seen["где провести корпоратив"]["Число запросов"]=="5270"
    assert "wordstat_a.csv" in seen["где провести корпоратив"]["Исходные CSV"]
    assert "wordstat_b.csv" in seen["где провести корпоратив"]["Исходные CSV"]
    assert seen["детский день рождения под ключ"]["Класс намерения (автоматически)"].startswith("B2C")
    assert seen["организация корпоратива"]["Класс намерения (автоматически)"]=="B2B прямой"
    assert seen["организация корпоратива"]["Географический фильтр"]=="все регионы"
print("BIS V2 Wordstat regression PASS: user counts, provenance, deduplication, intent flags, no summed volumes.")
