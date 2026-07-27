# -*- coding: utf-8 -*-
# 診斷：Wix 能否取得「全部活動（2025-2026）」的報名(YES)/請假(NO)/候補(WAITING) 數。
# 只印：日期、活動名、狀態計數。不印任何 email/姓名。
import json, os, urllib.request
from collections import Counter
from probe_events import BASE, HEADERS

def call(method, path, body=None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers=HEADERS, method=method)
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))

def get_events():
    body = {"fields": ["REGISTRATION"], "includeDrafts": False,
            "query": {"filter": {}, "paging": {"limit": 100},
                      "sort": [{"fieldName": "createdDate", "order": "ASC"}]}}
    return call("POST", "events/v3/events/query", body).get("events", [])

def get_guests(event_id):
    out, off = [], 0
    while True:
        body = {"fields": ["GUEST_DETAILS", "GUEST_TOTAL"],
                "query": {"filter": {"guestType": "RSVP", "eventId": event_id},
                          "paging": {"limit": 100, "offset": off}}}
        res = call("POST", "events/v2/guests/query", body)
        b = res.get("guests", []) or []
        out += b; off += len(b)
        if not b or len(b) < 100:
            break
    return out

events = get_events()
print("活動總數：", len(events))
# 先看單一 guest 的頂層鍵，確認 rsvpStatus 存在
if events:
    g0 = get_guests(events[0]["id"])
    if g0:
        print("guest 頂層鍵：", sorted(g0[0].keys()))

def yr(e):
    return (e.get("dateAndTimeSettings", {}) or {}).get("startDate", "")[:4]

rows = []
for e in sorted(events, key=lambda x: (x.get("dateAndTimeSettings", {}) or {}).get("startDate", "")):
    d = (e.get("dateAndTimeSettings", {}) or {}).get("startDate", "")[:10]
    if not (d.startswith("2025") or d.startswith("2026")):
        continue
    status = e.get("status", "")
    gs = get_guests(e["id"]) if status != "CANCELED" else []
    c = Counter((g.get("rsvpStatus") or g.get("status") or "?") for g in gs)
    rows.append((d, status[:6], e.get("title", "")[:26], c))

print("\n=== 各場 RSVP 狀態計數（YES=報名 / NO=請假 / WAITING=候補）===")
print("日期        狀態    YES  NO  WAIT  其他   活動")
tot = Counter()
for d, st, title, c in rows:
    other = sum(v for k, v in c.items() if k not in ("YES", "NO", "WAITING"))
    tot.update(c)
    print("%-10s %-6s %4d %4d %5d %5d   %s" % (
        d, st, c.get("YES", 0), c.get("NO", 0), c.get("WAITING", 0), other, title))
print("\n合計：", dict(tot))
