# -*- coding: utf-8 -*-
# 診斷：公司下拉答案存在哪個鍵。不印任何姓名/信箱/身分證，只看結構與公司值的分佈。
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

def company_id(event_id):
    res = call("GET", "events/v1/events/%s/form" % event_id)
    for c in (res.get("form", {}) or {}).get("controls", []) or []:
        if "所屬企業/集團" in (c.get("label") or ""):
            return c.get("id", "")
    return ""

def guests(event_id):
    out, off = [], 0
    while True:
        body = {"fields": ["GUEST_DETAILS","GUEST_TOTAL"],
                "query": {"filter": {"guestType":"RSVP","eventId":event_id},
                          "paging": {"limit":100,"offset":off}}}
        res = call("POST","events/v2/guests/query",body)
        b = res.get("guests",[]) or []
        out += b; off += len(b)
        if not b or len(b) < 100: break
    return out

events = [e for e in get_events()
          if (e.get("dateAndTimeSettings",{}) or {}).get("startDate","").startswith("2026")
          and e.get("status") != "CANCELED"]

# 只拿一場高人數的來看鍵結構
sample = None
for e in events:
    if e.get("dateAndTimeSettings",{}).get("startDate","").startswith("2026-03-20"):
        sample = e; break

cid = company_id(sample["id"])
gs = guests(sample["id"])
print("樣本場：3/20，公司控制 id =", cid, "，訪客數 =", len(gs))
key_use = Counter()      # 該 inputName 底下出現的鍵
sample_company_vals = Counter()
for g in gs:
    ivs = (((g.get("guestDetails",{}) or {}).get("formResponse",{}) or {}).get("inputValues",[]) or [])
    for iv in ivs:
        if iv.get("inputName") == cid:
            keys = tuple(sorted(k for k in iv.keys() if k != "inputName"))
            key_use[keys] += 1
            # 公司名不算敏感個資，可看分佈
            v = iv.get("value","")
            vs = iv.get("values", [])
            comp = v or (vs[0] if vs else "")
            sample_company_vals[comp or "(空)"] += 1
print("公司欄位出現的鍵組合分佈：", dict(key_use))
print("公司值分佈（前）:")
for k,n in sample_company_vals.most_common():
    print(f"   {n:3d}  {k}")
