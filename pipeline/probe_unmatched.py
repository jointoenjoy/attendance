# -*- coding: utf-8 -*-
# 看 3/20 未歸戶者到底填了什麼公司；遮蔽 email/身分證/生日/姓名等個資。
import re, json, urllib.request
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

def company_opts(eid):
    res = call("GET","events/v1/events/%s/form"%eid); s=set()
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

ev = [e for e in get_events()
      if (e.get("dateAndTimeSettings",{}) or {}).get("startDate","").startswith("2026-03-20")][0]
vocab = company_opts(ev["id"])

def looks_pii(s):
    if "@" in s: return True                      # email
    if re.fullmatch(r"[A-Za-z]\d{9}", s): return True  # 身分證
    if re.fullmatch(r"\d{5,}", s): return True    # 生日/長數字
    if re.fullmatch(r"09\d{8}", s): return True   # 手機
    return False

unmatched_vals = Counter()
n_un = 0
for g in guests(ev["id"]):
    ivs=(((g.get("guestDetails",{}) or {}).get("formResponse",{}) or {}).get("inputValues",[]) or [])
    vals=[]
    for iv in ivs:
        for v in ([iv.get("value")] + (iv.get("values") or [])):
            if isinstance(v,str) and v.strip(): vals.append(v.strip())
    if any(v in vocab for v in vals):
        continue
    n_un += 1
    # 收集非個資、非純數字、長度<=14 的短字串（可能是公司）
    for v in vals:
        if not looks_pii(v) and len(v)<=14:
            unmatched_vals[v]+=1

print("3/20 未歸戶人數：", n_un)
print("未歸戶者填入的短字串分佈（疑似公司；已遮個資）：")
for k,c in unmatched_vals.most_common(40):
    print(f"  {c:3d}  {k}")
