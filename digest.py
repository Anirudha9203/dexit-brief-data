"""Builds data/digest.md: a compact (about 50 KB) version of data/latest.md so a scheduled run can read it in one fetch.
Keeps status, publishers, all keyword-search and tender sections, and only the page/RSS/carry-over headlines that match DEXIT-relevant words."""
import re
t = open("data/latest.md", encoding="utf-8").read()
secs = re.split(r"\n(?=## )", t)
KEY = re.compile(r"cbt|computer[- ]based|proctor|on-screen|onscreen|osm|evaluat|vendor|agency|tender|bid\b|blacklist|leak|glitch|exam centre|exam center|nta\b|\bssc\b|rrb|ibps|upsc|psc\b|bssc|bpssc|neet|cuet|\bjee\b|ugc|tcs|tcs ion|aptech|sify|excelsoft|mettl|iamneo|eduquity|coempt|meritt|sanskriti|prometric|pearson|inspera|upgrad|unacademy|physicswallah|byju|testbook|adda247|embibe|edtech|aicte|nilekani|exam reform|assessment |invigilat", re.I)
seen=set()
out = [secs[0] + " (compact digest; full file: data/latest.md)"]
for s in secs[1:]:
    head = s.split("\n")[0]
    keep_all = head.startswith(("## Fetch status", "## Publishers", "## TenderDetail", "## SEAB", "## NTA"))
    if keep_all:
        out.append(s)
        continue
    lines = s.split("\n")
    body=[]
    for l in lines[1:]:
        if not (l.startswith("- ") and KEY.search(l)): continue
        m=re.search(r"\((https?://[^)\s]+)\)",l); k=m.group(1) if m else l
        if k in seen: continue
        seen.add(k)
        l=re.sub(r"\(https://news\.google\.com/[^)]*\)","",l)
        body.append(l)
    if head.startswith("## News search"): body=body[:12]
    if body:
        out.append("\n".join([head] + [l[:300] for l in body]))
open("data/digest.md", "w", encoding="utf-8").write("\n\n".join(out) + "\n")
