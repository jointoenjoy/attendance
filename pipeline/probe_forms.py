# -*- coding: utf-8 -*-
# 列出每場 2026 活動的表單欄位（label / type / id），找出「企業」欄位。表單本身無個資。
import json, os, urllib.request
from probe_events import BASE, HEADERS  # reuse env-loaded config

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

events = [e for e in get_events()
          if (e.get("dateAndTimeSettings", {}) or {}).get("startDate", "").startswith("2026")]

for ev in events:
    res = call("GET", "events/v1/events/%s/form" % ev["id"])
    controls = (res.get("form", {}) or {}).get("controls", []) or []
    print("\n===", ev.get("dateAndTimeSettings", {}).get("startDate", "")[:10], ev.get("title","")[:34], "| status", ev.get("status"))
    for c in controls:
        label = c.get("label") or ""
        ctype = c.get("type") or ""
        cid = c.get("id") or ""
        extra = ""
        # dropdown / options 可能藏在不同鍵
        for k in ("options", "inputType", "controlType"):
            if k in c:
                extra += f" {k}={json.dumps(c[k], ensure_ascii=False)[:120]}"
        print(f"  [{ctype:<12}] label={label!r:<22} id={cid}{extra}")
