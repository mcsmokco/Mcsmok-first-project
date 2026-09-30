import json, re, html, time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT='https://news.google.com/rss/search?q='
QUERIES={
 'news':['كرة القدم أخبار','football latest news','كرة القدم المغرب','دوري أبطال أوروبا'],
 'raja':['الرجاء الرياضي','Raja Casablanca']
}

def fetch(q):
    url=ROOT+quote(q)+'&hl=ar&gl=MA&ceid=MA:ar'
    req=Request(url,headers={'User-Agent':'Mozilla/5.0'})
    with urlopen(req,timeout=20) as r: data=r.read()
    return ET.fromstring(data)

def clean(s):
    s=html.unescape(re.sub('<[^>]+>',' ',s or ''))
    return re.sub(r'\s+',' ',s).strip()

def parse_date(s):
    try: return parsedate_to_datetime(s).astimezone(timezone.utc).isoformat()
    except Exception: return ''

def collect(queries,limit=100):
    items=[]; seen=set()
    for q in queries:
        try: root=fetch(q)
        except Exception as e: print('feed error',q,e); continue
        for x in root.findall('./channel/item'):
            title=clean(x.findtext('title',''))
            link=x.findtext('link','')
            desc=clean(x.findtext('description',''))
            date=parse_date(x.findtext('pubDate',''))
            if not title or not link: continue
            key=re.sub(r'\W','',title.lower())
            if key in seen: continue
            seen.add(key)
            source=x.findtext('{http://search.yahoo.com/mrss/}source') or x.findtext('source') or ''
            source=clean(source)
            if ' - ' in title and not source:
                title,source=title.rsplit(' - ',1)
            items.append({'title':title,'source':source,'date':date,'url':link,'summary':desc})
    items.sort(key=lambda x:x.get('date',''),reverse=True)
    return items[:limit]

def write(path,items):
    obj={'updated_at':datetime.now(timezone.utc).isoformat(),'count':len(items),'items':items}
    with open(path,'w',encoding='utf-8') as f: json.dump(obj,f,ensure_ascii=False,indent=2)

write('data/news.json',collect(QUERIES['news'],100))
write('data/raja-news.json',collect(QUERIES['raja'],60))
print('news updated')
