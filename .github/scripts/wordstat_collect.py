#!/usr/bin/env python3
"""Read-only Yandex Search API / Wordstat v2 collector.

SAFE DEFAULT: dry-run, zero web requests. Execution is always opt-in.
Credentials in environment only: YANDEX_CLOUD_FOLDER_ID, YANDEX_SEARCH_API_KEY.
No scheduled paid requests, no commits of API keys.
Documentation: https://aistudio.yandex.ru/ru/docs/search-api/operations/wordstat-getregionsdistribution
"""
import argparse
import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
SEED = ROOT / ".github/seo/keywords-v2.csv"
API = "https://searchapi.api.cloud.yandex.net/v2/wordstat"
ENDPOINTS = {"regions": "/regions", "top": "/topRequests"}

def request(path, payload, token):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = Request(
        API + path, data=body, method="POST",
        headers={"Authorization": "Api-Key " + token, "Content-Type": "application/json"}
    )
    with urlopen(req, timeout=45) as resp:
        result = json.load(resp)
        if not isinstance(result, dict):
            raise ValueError("Unexpected JSON response: object required")
        return result

def main():
    ap = argparse.ArgumentParser(description="Yandex Cloud Wordstat v2 research; dry-run by default")
    ap.add_argument("--execute", action="store_true", help="Authorize actual billed API requests")
    ap.add_argument("--mode", choices=tuple(ENDPOINTS), default="regions",
                    help="regions: cities distribution; top: queries for one city")
    ap.add_argument("--region-id", default="43", help="Top-only: Yandex Wordstat region ID, e.g. 43 = Kazan")
    ap.add_argument("--limit", type=int, default=3, help="Max 1..6 seed phrases per run")
    args = ap.parse_args()
    if not 1 <= args.limit <= 6:
        ap.error("--limit must be between 1 and 6")
    if args.mode == "top" and not (args.region_id.isascii() and args.region_id.isdecimal()):
        ap.error("--region-id must be a numeric Wordstat region ID")
    with SEED.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file, delimiter=";"))
    phrases = list(dict.fromkeys(
        x["Фраза с модификатором"] for x in rows
        if x["Категория региона"] == "Россия"
    ))[:args.limit]
    if not phrases:
        raise ValueError("No national base phrases found in keywords-v2.csv")
    plans = []
    for phrase in phrases:
        payload = {"phrase": phrase, "devices": ["DEVICE_ALL"]}
        if args.mode == "regions":
            payload["region"] = "REGION_CITIES"
        else:
            payload["regions"] = [args.region_id]
        plans.append(payload)

    print("WORDSTAT V2 / Yandex Search API")
    print("Mode:", args.mode, "| phrases:", len(plans), "| endpoint:", ENDPOINTS[args.mode])
    print("This API is billable. Script never runs against the network without --execute.")
    for payload in plans:
        print("  -", payload["phrase"])

    if not args.execute:
        print("DRY RUN: zero API calls. No statistics obtained; no expense incurred.")
        return

    token = os.environ.get("YANDEX_SEARCH_API_KEY", "").strip()
    folder = os.environ.get("YANDEX_CLOUD_FOLDER_ID", "").strip()
    if not token or not folder:
        ap.error("Set YANDEX_SEARCH_API_KEY and YANDEX_CLOUD_FOLDER_ID locally; never store them in files or chat.")
    if len(folder) > 50:
        ap.error("Invalid folder ID length")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    directory = ROOT / ".github/seo/results"
    directory.mkdir(parents=True, exist_ok=True)
    output = directory / f"wordstat-{args.mode}-{timestamp}.json"
    results = []
    try:
        for payload in plans:
            body = {**payload, "folderId": folder}
            result = request(ENDPOINTS[args.mode], body, token)
            if not isinstance(result.get("results"), list):
                raise ValueError("Response has no 'results' array")
            record = {"phrase": payload["phrase"], "scope": args.mode,
                      "region_id": args.region_id if args.mode == "top" else None,
                      "fetched_utc": timestamp, "source": "Yandex Search API Wordstat v2",
                      "data": result}
            results.append(record)
    except (HTTPError, URLError, ValueError) as exc:
        # Save valid responses if a later request failed; never write credentials.
        if results:
            output.write_text(json.dumps({"records": results, "partial": True},
                                         ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raise SystemExit("Wordstat API request/response error: " + str(exc))
    output.write_text(json.dumps({"records": results, "partial": False},
                                 ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Saved real Wordstat API responses:", output.relative_to(ROOT))
    print("To name cities, fetch and use the official GetRegionsTree; don't guess labels.")

if __name__ == "__main__":
    main()
