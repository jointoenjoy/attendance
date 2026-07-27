# -*- coding: utf-8 -*-
# 去識別化拉取 2026：只輸出「公司 -> 人數(不重複)/人次(含重複)」，全程不寫入任何 email/姓名。
# 穩健比對：公司答案用「下拉選項字典」比對，不綁欄位 id（表單改版過、id 會變）。
import json, os, hashlib, urllib.request, urllib.error
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
env = {}
with open(os.path.join(HERE, "keys.env"), encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()

AUTH = env["WIX_API_AUTHORIZATION"]; SITE = env["WIX_API_SITE_ID"]
BASE = env["WIX_API_BASE_URL"].rstrip("/") + "/"
HEADERS = {"Content-Type": "application/json", "Authorization": AUTH, "wix-site-id": SITE}
YEAR = "2026"

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

def form_company_options(event_id):
    """回傳該場表單『所屬企業/集團』下拉的選項集合。"""
    res = call("GET", "events/v1/events/%s/form" % event_id)
    opts = set()
    for c in (res.get("form", {}) or {}).get("controls", []) or []:
        if "所屬企業/集團" in (c.get("label") or ""):
            for inp in (c.get("inputs") or []):
                for o in (inp.get("options") or []):
                    if isinstance(o, str) and o.strip():
                        opts.add(o.strip())
    return opts

def get_guests(event_id):
    guests, offset = [], 0
    while True:
        body = {"fields": ["GUEST_DETAILS", "GUEST_TOTAL"],
                "query": {"filter": {"guestType": "RSVP", "eventId": event_id},
                          "paging": {"limit": 100, "offset": offset},
                          "sort": [{"fieldName": "createdDate", "order": "ASC"}]}}
        res = call("POST", "events/v2/guests/query", body)
        batch = res.get("guests", []) or []
        guests.extend(batch)
        offset += len(batch)
        if not batch or len(batch) < 100:
            break
    return guests

def hemail(e):
    return hashlib.sha256(e.strip().lower().encode("utf-8")).hexdigest() if e else ""

events_all = get_events()
y_events = [e for e in events_all
            if (e.get("dateAndTimeSettings", {}) or {}).get("startDate", "").startswith(YEAR)]

# 全域公司字典（union 各場下拉選項）
VOCAB = set()
form_opts = {}
for ev in y_events:
    o = form_company_options(ev["id"])
    form_opts[ev["id"]] = o
    VOCAB |= o
print("2026 場次：", len(y_events), " 公司字典：", sorted(VOCAB))

def guest_company(guest, vocab):
    ivs = (((guest.get("guestDetails", {}) or {}).get("formResponse", {}) or {}).get("inputValues", []) or [])
    # 掃所有欄位，值落在字典裡就是公司（不綁 inputName）
    for iv in ivs:
        cand = (iv.get("value") or "").strip()
        if cand in vocab:
            return cand
        for v in (iv.get("values") or []):
            if isinstance(v, str) and v.strip() in vocab:
                return v.strip()
    return ""

visits = defaultdict(int)          # 人次（含重複）
people = defaultdict(set)          # 人數（雜湊 email 去重）
blank = 0
per_event = []

for ev in y_events:
    eid = ev["id"]
    if ev.get("status") == "CANCELED":
        per_event.append((ev.get("dateAndTimeSettings",{}).get("startDate","")[:10], "CANCELED", 0, 0))
        continue
    vocab = form_opts[eid] or VOCAB
    guests = get_guests(eid)
    matched = 0
    for g in guests:
        gd = g.get("guestDetails", {}) or {}
        email = (gd.get("email", "") or "").strip().lower()
        comp = guest_company(g, vocab)
        if not comp:
            # 沒點下拉 → 用 email 網域當企業帳號，交給下方歸戶區指派集團
            if "@" in email:
                comp = "@" + email.split("@")[-1]
            else:
                comp = "（無 email 無企業）"
            blank += 1
        else:
            matched += 1
        visits[comp] += 1
        if email:
            people[comp].add(hemail(email))
    per_event.append((ev.get("dateAndTimeSettings",{}).get("startDate","")[:10],
                      ev.get("status","")[:4], len(guests), matched))

print("\n=== 各場：日期 status 報名數 已歸戶數 ===")
for d, s, n, mt in per_event:
    print("  %s %-4s 報名 %3d  歸戶 %3d" % (d, s, n, mt))

rows = []
for comp in sorted(visits, key=lambda c: (-len(people[c]), -visits[c])):
    rows.append({"company": comp, "people": len(people[comp]), "visits": visits[comp]})

print("\n=== 2026 公司彙總（人數 / 人次）===")
for r in rows:
    print("  %-18s 人數 %3d   人次 %3d" % (r["company"], r["people"], r["visits"]))
print("\n未填企業人次：", blank)

out = os.path.join(HERE, "data2026.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(rows, f, ensure_ascii=False, indent=2)
print("已寫出（僅公司層級數字，無個資）:", out)
