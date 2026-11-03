#!/usr/bin/env python3
"""Print honest Lighthouse metrics and actionable opportunities; don't invent scores."""
import json,sys
from pathlib import Path
folder=Path(sys.argv[1])
files=sorted(folder.glob("*.json"))
if len(files)!=4:raise SystemExit(f"Expected 4 reports, got {len(files)}")
rows=[]
for path in files:
 d=json.loads(path.read_text(encoding="utf-8"))
 cats=d["categories"];audit=d["audits"]
 scores={name:round(cats[name]["score"]*100) if cats[name]["score"] is not None else None
         for name in ("performance","accessibility","best-practices","seo")}
 lcp=audit.get("largest-contentful-paint",{}).get("numericValue")
 cls=audit.get("cumulative-layout-shift",{}).get("numericValue")
 opportunities=[]
 for name,item in audit.items():
  if item.get("score") is not None and item["score"]<.9 and item.get("details",{}).get("type")=="opportunity":
   opportunities.append((round(item["details"].get("overallSavingsMs",0)),item.get("title",name)))
 opportunities=sorted(opportunities,reverse=True)[:8]
 rows.append((path.name,scores,lcp,cls,opportunities))
 print(f"{path.name}: {scores}; lab LCP {lcp/1000:.2f}s" if isinstance(lcp,(float,int)) else str(scores),
       f"; CLS {cls:.3f}" if isinstance(cls,(float,int)) else "")
 for ms,name in opportunities:print(f"  opportunity: ~{ms} ms | {name}")
print("\nNote: lab scores are not real-user CWV and do not prove conversion or SEO rankings.")
md=["## BIS V2 mobile Lighthouse audit","","| Page | Performance | Accessibility | Best practices | SEO | Lab LCP | Lab CLS |","|---|---:|---:|---:|---:|---:|---:|"]
for name,s,lcp,cls,opp in rows:
 md.append(f"| {name} | {s['performance']} | {s['accessibility']} | {s['best-practices']} | {s['seo']} | {lcp/1000:.2f}s | {cls:.3f} |")
md+=["","Lab-based snapshot only; not live audience data. Full JSON artifacts attached to the workflow."]
print("\n".join(md))
try:
 import os
 summary=os.environ.get("GITHUB_STEP_SUMMARY")
 if summary:
  with open(summary,"a",encoding="utf-8") as f:f.write("\n".join(md)+"\n")
except OSError:pass
# Any category <60 or one failed measurement is a serious regression.
if any(v is None or v<60 for _,score,_,_,_ in rows for v in score.values()):
 raise SystemExit("Lighthouse category below 60: fix before promoting release")
