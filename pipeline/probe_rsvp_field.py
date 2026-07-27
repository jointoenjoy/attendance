# -*- coding: utf-8 -*-
# 找出 RSVP 狀態（YES/NO/WAITING）到底存在 guest 的哪個鍵。不印 email/姓名。
import json, urllib.request
from collections import Counter
from probe_events import BASE, HEADERS

def call(method, path, body=None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers=HEADERS, method=method)
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))

def get_events():
    body = {"fields": ["REGISTRATION"], "includeDrafts": False,
            "query": {"filter": {}, "paging": {"limit": 100}}}
    return call("POST", "events/v3/events/query", body).get("events", [])

# 挑 3/20（101 人）
ev = None
for e in get_events():
    if (e.get("dateAndTimeSettings", {}) or {}).get("startDate", "").startswith("2026-03-20"):
        ev = e; break
print("樣本：", ev["title"][:20])

def get_guests(eid, fields):
    body = {"fields": fields,
            "query": {"filter": {"guestType": "RSVP", "eventId": eid},
                      "paging": {"limit": 100}}}
    return call("POST", "events/v2/guests/query", body).get("guests", []) or []

gs = get_guests(ev["id"], ["GUEST_DETAILS", "GUEST_TOTAL"])
print("訪客數：", len(gs))
if gs:
    g = gs[0]
    print("guest 頂層鍵：", sorted(g.keys()))
    # 找任何值 == YES/NO/WAITING 的鍵路徑
    def scan(o, path=""):
        found = []
        if isinstance(o, dict):
            for k, v in o.items():
                found += scan(v, path + "/" + k)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                found += scan(v, path + "[]")
        elif isinstance(o, str) and o in ("YES", "NO", "WAITING", "ATTENDING", "NOT_ATTENDING"):
            found.append((path, o))
        return found
    hits = Counter()
    for g in gs:
        for p, v in scan(g):
            hits[(p, v)] += 1
    print("狀態值出現的鍵路徑分佈：")
    for (p, v), n in hits.most_common(20):
        print("  %4d  %s = %s" % (n, p, v))
    # 也印一筆 guest 的鍵結構（去個資：只印鍵，不印值）
    def shape(o):
        if isinstance(o, dict):
            return {k: shape(v) for k, v in o.items()}
        if isinstance(o, list):
            return [shape(o[0])] if o else []
        return type(o).__name__
    print("\n單筆 guest 結構（鍵→型別）：")
    print(json.dumps(shape(gs[0]), ensure_ascii=False, indent=1)[:1500])
