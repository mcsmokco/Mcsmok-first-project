import json, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
import re

QUERIES = [
    ("كرة القدم", "ar"), ("الدوري الإنجليزي كرة القدم", "ar"),
    ("الدوري الإسباني كرة القدم", "ar"), ("الدوري الإيطالي كرة القدم", "ar"),
    ("الدوري الألماني كرة القدم", "ar"), ("الدوري الفرنسي كرة القدم", "ar"),
    ("كرة القدم المغرب", "ar"), ("football transfer news", "en"),
]

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read()

items, seen = [], set()
for query, lang in QUERIES:
    hl, gl, ceid = ("ar", "MA", "MA:ar") if lang == "ar" else ("en-US", "US", "US:en")
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": query, "hl": hl, "gl": gl, "ceid": ceid})
    try:
        root = ET.fromstring(get(url))
        for node in root.findall("./channel/item")[:15]:
            title = (node.findtext("title") or "").strip(); link = (node.findtext("link") or "").strip()
            pub = (node.findtext("pubDate") or "").strip(); source_el = node.find("source")
            source = (source_el.text or "Google News") if source_el is not None else "Google News"
            desc = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", node.findtext("description") or "")).strip()
            key = title.lower()
            if title and key not in seen:
                seen.add(key); items.append({"title": title, "source": source, "date": pub, "url": link, "summary": desc[:220] + ("..." if len(desc) > 220 else "")})
    except Exception as e:
        print("News feed error:", query, e)

# Public ESPN scoreboard feed: today's football events, scores and status.
# It requires no API key and is refreshed every 30 minutes by GitHub Actions.
def get_matches():
    date = datetime.now(timezone.utc).strftime("%Y%m%d")
    url = "https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard?dates=" + date
    events = json.loads(get(url)).get("events", [])
    matches = []
    for ev in events:
        comp = (ev.get("competitions") or [{}])[0]
        competitors = comp.get("competitors") or []
        if len(competitors) < 2: continue
        teams = []
        for c in competitors:
            team = c.get("team") or {}
            teams.append({"name": team.get("displayName", ""), "short": team.get("shortDisplayName", ""), "logo": team.get("logo", ""), "score": c.get("score", "")})
        status = (comp.get("status") or ev.get("status") or {}).get("type", {})
        matches.append({
            "id": ev.get("id"), "league": (ev.get("league") or {}).get("name", "Football"),
            "name": ev.get("name", ""), "date": ev.get("date", ""),
            "state": status.get("state", "pre"), "status": status.get("shortDetail", status.get("detail", "")),
            "teams": teams,
            "venue": ((comp.get("venue") or {}).get("fullName") or ""),
        })
    return matches

try:
    matches = get_matches()
except Exception as e:
    print("Match feed error:", e); matches = []

now = datetime.now(timezone.utc).isoformat()
Path("data").mkdir(exist_ok=True)
Path("data/news.json").write_text(json.dumps({"updated_at": now, "count": len(items[:100]), "items": items[:100]}, ensure_ascii=False, indent=2), encoding="utf-8")
Path("data/matches.json").write_text(json.dumps({"updated_at": now, "count": len(matches), "items": matches}, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Wrote {len(items[:100])} news items and {len(matches)} matches")
