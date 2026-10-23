#!/usr/bin/env python3
"""BIS: opt-in read-only Wordstat API collector. NEVER runs without --execute and token.

Yandex documentation: https://yandex.ru/support2/wordstat/en/content/api-structure
For each phrase, /v1/regions consumes two units of Wordstat daily request quota.
No fake impressions, CPC, region names or conversions are produced.
"""
import argparse
import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[2]
SEED=ROOT/".github/seo/keywords-v2.csv"
API="https://api.wordstat.yandex.net/v1"
def call(method, body, token):
    request=Request(API+method, data=json.dumps(body,ensure_ascii=False).encode("utf-8"),
      headers={"Authorization":"Bearer "+token,"Content-Type":"application/json;charset=utf-8"},
      method="POST")
    with urlopen(request,timeout=30) as response:
        return json.load(response)
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--execute",action="store_true",help="Explicitly authorize Wordstat quota use")
    parser.add_argument("--limit",type=int,default=3,help="Max base phrases; limit 1..6")
    args=parser.parse_args()
    if not 1<=args.limit<=6:
        parser.error("--limit must be 1..6. Region API costs two daily quota units per phrase")
    with SEED.open(encoding="utf-8",newline="") as f:
        rows=list(csv.DictReader(f,delimiter=";"))
    phrases=list(dict.fromkeys(
        row["Фраза с модификатором"] for row in rows
        if row["Категория региона"]=="Россия"
    ))
    phrases=phrases[:args.limit]
    print(f"Selected {len(phrases)} national base phrases. Region endpoint costs {2*len(phrases)} quota units.")
    for p in phrases:
        print(" -",p)
    if not args.execute:
        print("DRY RUN ONLY: no API calls. To collect REAL data supply --execute and WORDSTAT_OAUTH_TOKEN.")
        return
    token=os.environ.get("WORDSTAT_OAUTH_TOKEN","").strip()
    if not token:
        parser.error("WORDSTAT_OAUTH_TOKEN is required. Do not commit or print tokens.")
    stamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    out=ROOT/".github/seo/results"
    out.mkdir(parents=True,exist_ok=True)
    results=[]
    for phrase in phrases:
        print("Requesting cities distribution for:",phrase)
        data=call("/regions",{"phrase":phrase,"regionType":"cities","devices":["all"]},token)
        if not isinstance(data,dict) or not isinstance(data.get("regions"),list):
            raise ValueError("Wordstat response missing 'regions' list for "+phrase)
        results.append({"phrase":phrase,"retrieved_utc":stamp,"region_type":"cities","source":"Yandex Wordstat API /v1/regions","response":data})
    # Store raw results with original regionId to prevent guessing city names.
    dest=out/("wordstat-regions-"+stamp+".json")
    dest.write_text(json.dumps({"queries":results},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Saved actual API response:",dest.relative_to(ROOT))
    print("Regional names are not inferred: map regionId through /v1/getRegionsTree before reporting.")
if __name__=="__main__":
    try:main()
    except (HTTPError,URLError) as e:raise SystemExit("Wordstat request failed (token, access, quota or network). HTTP/network error: "+str(e))
