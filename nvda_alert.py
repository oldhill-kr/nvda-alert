import os, json, re, html, urllib.request, urllib.parse
import xml.etree.ElementTree as ET
Q = '"Jensen Huang" (fired OR ousted OR removed OR "step down" OR resign OR "board" OR 해임)'
URLS = [f"https://news.google.com/rss/search?q={urllib.parse.quote(Q)}&hl={h}&gl={g}&ceid={g}:{l}&when:1d"
        for h, g, l in [("en-US","US","en"),("ko","KR","ko")]]
KW = re.compile(r"fire[ds]?|ous?ted|remov|step(s|ping)? down|resign|replace|해임|퇴출|사임|경질|교체", re.I)
HAN = re.compile(r"[가-힣]")
def ko(t):
    if not t or HAN.search(t): return t
    try:
        u = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=ko&dt=t&q=" + urllib.parse.quote(t)
        return "".join(x[0] for x in json.loads(urllib.request.urlopen(u, timeout=20).read())[0])
    except Exception as e:
        print("translate fail", e); return t
def summ(it, title):
    d = html.unescape(re.sub(r"<[^>]+>", " ", it.findtext("description", "")))
    d = re.sub(r"\s+", " ", d).strip()
    src = it.findtext("source", "")
    for x in (title, src):
        d = d.replace(x, "").strip(" -–|")
    return ko(d)[:100] if len(d) > 15 else ""
SEEN = "seen.json"
seen = set(json.load(open(SEEN))) if os.path.exists(SEEN) else set()
new = []
for u in URLS:
    try:
        root = ET.fromstring(urllib.request.urlopen(u, timeout=20).read())
    except Exception as e:
        print("fetch fail", e); continue
    for it in root.iter("item"):
        t, l = it.findtext("title", ""), it.findtext("link", "")
        if l and l not in seen and KW.search(t):
            new.append((t, l, summ(it, t))); seen.add(l)
if new and os.environ.get("TELEGRAM_TOKEN"):
    msg = "🚨 젠슨황 해임 관련 새 뉴스\n\n" + "\n\n".join(f"• {ko(t)}\n{s}\n{l}".replace("\n\n","\n") for t, l, s in new[:8])
    data = urllib.parse.urlencode({"chat_id": os.environ["TELEGRAM_CHAT_ID"].strip(), "text": msg[:4000]}).encode()
    try:
        urllib.request.urlopen(f"https://api.telegram.org/bot{os.environ['TELEGRAM_TOKEN'].strip()}/sendMessage", data, timeout=20)
    except urllib.error.HTTPError as e:
        print("TELEGRAM ERROR", e.code, e.read().decode()); raise
json.dump(sorted(seen)[-500:], open(SEEN, "w"))
print(f"new={len(new)}")
