# -*- coding: utf-8 -*-
# 統計「未填企業」者的 email 網域分佈（只看網域、不輸出個別信箱），評估能否用網域補回歸戶。
import json, urllib.request
from collections import Counter, defaultdict
from probe_events import BASE, HEADERS

def call(method, path, body=None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers=HEADERS, method=method)
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))

def get_events():
    body = {"fields":["REGISTRATION"],"includeDrafts":False,
            "query":{"filter":{},"paging":{"limit":100}}}
    return call("POST","events/v3/events/query",body).get("events",[])

def company_opts(eid):
    res=call("GET","events/v1/events/%s/form"%eid); s=set()
    for c in (res.get("form",{}) or {}).get("controls",[]) or []:
        if "所屬企業/集團" in (c.get("label") or ""):
            for inp in c.get("inputs") or []:
                for o in inp.get("options") or []:
                    if isinstance(o,str): s.add(o.strip())
    return s

def guests(eid):
    out,off=[],0
    while True:
        res=call("POST","events/v2/guests/query",
                 {"fields":["GUEST_DETAILS"],"query":{"filter":{"guestType":"RSVP","eventId":eid},
                  "paging":{"limit":100,"offset":off}}})
        b=res.get("guests",[]) or []; out+=b; off+=len(b)
        if not b or len(b)<100: break
    return out

def gcompany(g,vocab):
    ivs=(((g.get("guestDetails",{}) or {}).get("formResponse",{}) or {}).get("inputValues",[]) or [])
    for iv in ivs:
        for v in ([iv.get("value")] + (iv.get("values") or [])):
            if isinstance(v,str) and v.strip() in vocab: return v.strip()
    return ""

events=[e for e in get_events()
        if (e.get("dateAndTimeSettings",{}) or {}).get("startDate","").startswith("2026")
        and e.get("status")!="CANCELED"]

dom_unfilled=Counter()     # 未填企業者的網域
dom_people=defaultdict(set)
for ev in events:
    vocab=company_opts(ev["id"])
    for g in guests(ev["id"]):
        gd=g.get("guestDetails",{}) or {}
        email=(gd.get("email","") or "").strip().lower()
        if gcompany(g,vocab): continue          # 已歸戶跳過
        dom=email.split("@")[-1] if "@" in email else "(無email)"
        dom_unfilled[dom]+=1
        if email: dom_people[dom].add(email)

print("未填企業者 email 網域分佈（人次 / 不重複人數）：")
for dom,c in dom_unfilled.most_common(40):
    print(f"  {c:3d} 人次 / {len(dom_people[dom]):3d} 人   {dom}")
