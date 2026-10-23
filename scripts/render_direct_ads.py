#!/usr/bin/env python3
"""Generate Yandex Direct draft table with correct destination URLs and UTM parameters.

Uses the new, separate public website URL. Does not connect to or launch Yandex Direct.
Never sends requests. Review with campaign manager before importing.
"""
import argparse,csv
from pathlib import Path
from urllib.parse import urlsplit,urlencode
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"ads/BIS_DIRECT_ADS.csv"
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--base-url",required=True,help="Public separate BIS V2 URL")
 ap.add_argument("--out",type=Path,required=True)
 args=ap.parse_args()
 base=args.base_url.rstrip("/")+"/"
 parsed=urlsplit(base)
 if parsed.scheme!="https" or not parsed.netloc or parsed.query or parsed.fragment:
  ap.error("Require an HTTPS origin/path")
 with SOURCE.open(encoding="utf-8-sig",newline="") as f:
  ads=list(csv.DictReader(f,delimiter=";"))
 if len(ads)<12:raise ValueError("Ad variants incomplete")
 args.out.parent.mkdir(parents=True,exist_ok=True)
 columns=["Кампания","Группа","Заголовок","Текст","Ссылка с UTM","Статус"]
 with args.out.open("w",encoding="utf-8-sig",newline="") as f:
  w=csv.writer(f,delimiter=";",quoting=csv.QUOTE_MINIMAL)
  w.writerow(columns)
  for r in ads:
   landing=r["Посадочная страница"]
   if not (ROOT/landing).is_file():raise ValueError("Missing ad destination: "+landing)
   utm=urlencode({"utm_source":"yandex","utm_medium":"cpc",
                  "utm_campaign":r["UTM-кампания"],"utm_content":r["UTM-контент"]})
   dest=base+landing+"?"+utm
   w.writerow([r["Кампания (черновик)"],r["Группа"],r["Заголовок"],
               r["Текст объявления"],dest,
               "ЧЕРНОВИК: перед загрузкой проверить кампанию, таргетинг, модерацию и бюджет"])
 print("BIS V2 Direct draft:",len(ads),"ads for",base,"saved to",args.out)
if __name__=="__main__":main()
