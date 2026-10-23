#!/usr/bin/env python3
"""BIS V2: import official Wordstat Top Queries CSV exports without double counting.

Usage:
  python3 .github/scripts/import_wordstat_export.py \
    --out output.csv "wordstat_top_queries.csv" "wordstat_top_queries (1).csv"

IMPORTANT: Top queries overlap. Never SUM their wordstat values to estimate total
people or market size. Phrase with city-name is NOT a city-region filtered result.
Automated intent flags are rough screening, not verified classification.
No network, advertising, API calls, secrets or external dependencies.
"""
import argparse
import csv
import re
from collections import Counter
from pathlib import Path

HEADER = "Запросы со словами"
META = re.compile(r"Топ частотных запросов «(?P<seed>.*?)», (?P<start>\d{2}\.\d{2}\.\d{4})\s*[—–-]\s*(?P<end>\d{2}\.\d{2}\.\d{4}),\s*(?P<region>.*?),\s*(?P<device>.+)")
FIELDS = ["Запрос", "Число запросов", "Класс намерения (автоматически)",
          "Посадочная (гипотеза)", "Период начала", "Период окончания",
          "Географический фильтр", "Устройства", "Исходные CSV", "Ручная проверка"]
CITIES = re.compile(r"казан|москв|петербург|спб|самар|уфе|уфа|екатеринбург|красноярск|новосибирск|краснодар|сочи", re.I)

def flag(query):
    q = query.lower()
    if re.search(r"порно|секс|эроти|трах|ебут", q):
        return "Посторонний контент", "", "Исключить из коммерческого ядра"
    if re.search(r"детск|ребенк|ребёнк|аниматор", q):
        return "B2C детские (не утверждено)", "", "Нет подтвержденного BIS-кейса; не создавать услугу автоматически"
    if "корпоратив" in q or "корпоратива" in q or "корпоративов" in q:
        if ("организац" in q or "под ключ" in q):
            cls = "B2B прямой"
        elif re.search(r"заказать|стоимость|сколько стоит", q):
            cls = "B2B / площадка: проверить"
        elif re.search(r"где |ресторан|аренд|лофт|банкетн", q):
            cls = "Площадка / ресторан"
        elif re.search(r"как |иде[ия]|сценари|конкурс|своими руками", q):
            cls = "Информационный"
        else:
            cls = "Широкий / смешанный"
        warn = "Проверить намерение в выдаче перед покупкой рекламы"
        if CITIES.search(q):
            warn += "; топоним в запросе НЕ является региональным фильтром"
        return cls, "corporate-events.html", warn
    return "Другой / требуется разбор", "", "Не создавать страницу по алгоритмической классификации"

def read_file(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = csv.reader(f, delimiter=";")
        header = next(rows, None)
        if not header or len(header) < 3 or header[0] != HEADER or header[1] != "Число запросов":
            raise ValueError(f"{path}: not a Wordstat top queries CSV")
        match = META.search(header[2])
        if not match:
            raise ValueError(f"{path}: could not verify period/geography from header")
        meta = match.groupdict()
        for no, row in enumerate(rows, 2):
            if not row or all(not x.strip() for x in row):
                continue
            if len(row) < 2 or not row[1].strip().isdigit():
                raise ValueError(f"{path}:{no}: query count must be an integer")
            query = row[0].strip()
            if not query:
                raise ValueError(f"{path}:{no}: empty phrase")
            yield query, int(row[1]), meta

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    unique = {}
    total = 0
    for path in args.files:
        if not path.is_file():
            parser.error("Missing source file: " + str(path))
        for query, count, meta in read_file(path):
            total += 1
            key = (query, meta["start"], meta["end"], meta["region"], meta["device"])
            previous = unique.get(key)
            if previous:
                if previous["Число запросов"] != count:
                    raise ValueError(f"Conflicting values for {query}: {previous['Число запросов']} vs {count}")
                previous["sources"].add(path.name)
            else:
                cls, landing, note = flag(query)
                unique[key] = {"Запрос": query, "Число запросов": count,
                               "Класс намерения (автоматически)": cls,
                               "Посадочная (гипотеза)": landing,
                               "Период начала": meta["start"], "Период окончания": meta["end"],
                               "Географический фильтр": meta["region"], "Устройства": meta["device"],
                               "sources": {path.name}, "Ручная проверка": note}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for row in sorted(unique.values(), key=lambda x: (-x["Число запросов"], x["Запрос"])):
            record = dict(row)
            record["Исходные CSV"] = ", ".join(sorted(record.pop("sources")))
            for field in ("Запрос", "Класс намерения (автоматически)", "Ручная проверка"):
                if record[field].startswith(("=", "+", "-", "@")):
                    record[field] = "'" + record[field]  # defend Excel against CSV-formula injection
            writer.writerow(record)
    counts = Counter(r["Класс намерения (автоматически)"] for r in unique.values())
    print(f"Wordstat CSV import OK: {total} rows; {len(unique)} distinct queries; {total-len(unique)} duplicate rows.")
    print("All periods and filters preserved; no query frequencies summed.")
    print("Review automated intent classifications manually:", dict(counts))
    print("Output:", args.out)

if __name__ == "__main__":
    main()
