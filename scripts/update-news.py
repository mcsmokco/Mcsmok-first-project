import json, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

QUERIES = [
    ("كرة القدم", "ar"),
    ("الدوري الإنجليزي كرة القدم", "ar"),
    ("الدوري الإسباني كرة القدم", "ar"),
    ("الدوري الإيطالي كرة القدم", "ar"),
    ("الدوري الألماني كرة القدم", "ar"),
    ("الدوري الفرنسي كرة القدم", "ar"),
    ("كرة القدم المغرب", "ar"),
    ("football transfer news", "en"),
]

items = []
seen = set()

for query, lang in QUERIES:
    if lang == "ar":
        hl, gl, ceid = "ar", "MA", "MA:ar"
    else:
        hl, gl, ceid = "en-US", "US", "US:en"
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": query, "hl": hl, "gl": gl, "ceid": ceid})
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            root = ET.fromstring(r.read())
        for node in root.findall("./channel/item")[:12]:
            title = (node.findtext("title") or "").strip()
            link = (node.findtext("link") or "").strip()
            pub = (node.findtext("pubDate") or "").strip()
            source_el = node.find("source")
            source = (source_el.text or "Google News") if source_el is not None else "Google News"
            desc = (node.findtext("description") or "").strip()
            key = title.lower()
            if title and key not in seen:
                seen.add(key)
                # Keep a short source-provided snippet; the site links to the original article.
                import re
                desc = re.sub(r"<[^>]+>", " ", desc)
                desc = re.sub(r"\s+", " ", desc).strip()
                if len(desc) > 220:
                    desc = desc[:217] + "..."
                items.append({"title": title, "source": source, "date": pub, "url": link, "summary": desc})
    except Exception as e:
        print("Feed error:", query, e)

items = items[:80]
out = {
    "updated_at": datetime.now(timezone.utc).isoformat(),
    "count": len(items),
    "items": items,
}
path = Path("data/news.json")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Wrote {len(items)} news items")
