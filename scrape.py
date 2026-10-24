"""Daily headline scraper for the DEXIT Morning Brief.
Reads sources.txt, fetches each page, extracts headline links, writes
data/YYYY-MM-DD.json and data/latest.md (with per-source fetch status)."""
import json, re, sys, datetime, urllib.parse
import requests
from bs4 import BeautifulSoup

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
HDR = {"User-Agent": UA, "Accept-Language": "en-IN,en;q=0.9",
       "Accept": "text/html,application/xhtml+xml"}
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
SKIP = re.compile(r"^(home|login|sign in|subscribe|privacy|terms|advertise|about|contact|more|load more|view all|read more)\b", re.I)

def load_sources():
    out = []
    for line in open("sources.txt", encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "|" not in line:
            continue
        n, u = [x.strip() for x in line.split("|", 1)]
        out.append((n, u))
    return out

def extract(html, base):
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        t.decompose()
    seen, items = set(), []
    for a in soup.find_all("a", href=True):
        text = " ".join(a.get_text(" ", strip=True).split())
        if len(text) < 35 or len(text.split()) < 5 or SKIP.match(text):
            continue
        url = urllib.parse.urljoin(base, a["href"]).split("#")[0]
        if not url.startswith("http") or url in seen:
            continue
        seen.add(url)
        # nearby summary text if present
        summ = ""
        par = a.find_parent(["article", "li", "div"])
        if par:
            p = par.find("p")
            if p:
                summ = " ".join(p.get_text(" ", strip=True).split())[:300]
        items.append({"title": text[:300], "url": url, "summary": summ})
        if len(items) >= 60:
            break
    return items

def main():
    now = datetime.datetime.now(IST)
    result = {"scraped_at": now.isoformat(), "sources": []}
    for name, url in load_sources():
        rec = {"name": name, "url": url, "status": None, "error": None, "items": []}
        try:
            r = requests.get(url, headers=HDR, timeout=30)
            rec["status"] = r.status_code
            if r.status_code == 200:
                rec["items"] = extract(r.text, url)
        except Exception as e:
            rec["error"] = str(e)[:200]
        result["sources"].append(rec)
        print(f"{name}: {rec['status'] or rec['error']} ({len(rec['items'])} items)")
    day = now.strftime("%Y-%m-%d")
    with open(f"data/{day}.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    with open("data/latest.md", "w", encoding="utf-8") as f:
        f.write(f"# Scrape {now.strftime('%d %b %Y %H:%M IST')}\n\n## Fetch status\n")
        for s in result["sources"]:
            f.write(f"- {s['name']}: {s['status'] or s['error']} ({len(s['items'])} items)\n")
        for s in result["sources"]:
            if not s["items"]:
                continue
            f.write(f"\n## {s['name']}\n{s['url']}\n")
            for it in s["items"]:
                f.write(f"- [{it['title']}]({it['url']})")
                if it["summary"] and it["summary"] != it["title"]:
                    f.write(f" - {it['summary']}")
                f.write("\n")

if __name__ == "__main__":
    main()
