# -*- coding: utf-8 -*-
# 抓每場 2026 活動「所屬企業/集團」下拉的完整選項字典（union）。表單無個資。
import json, urllib.request
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

events = [e for e in get_events()
          if (e.get("dateAndTimeSettings",{}) or {}).get("startDate","").startswith("2026")]

vocab = set()
company_ids = set()
for e in events:
    res = call("GET", "events/v1/events/%s/form" % e["id"])
    for c in (res.get("form", {}) or {}).get("controls", []) or []:
        if "所屬企業/集團" in (c.get("label") or ""):
            company_ids.add(c.get("id",""))
            # dump 一次完整結構看選項在哪個鍵
            if "OPTS_DUMPED" not in globals():
                print("=== 下拉控制完整結構（樣本）===")
                print(json.dumps(c, ensure_ascii=False)[:1500])
                globals()["OPTS_DUMPED"] = True
            for k in ("options",):
                for opt in (c.get(k) or []):
                    if isinstance(opt, str): vocab.add(opt)
                    elif isinstance(opt, dict):
                        vocab.add(opt.get("label") or opt.get("value") or "")

print("\n公司控制 id 們：", company_ids)
print("選項字典（union）：", sorted(x for x in vocab if x))
