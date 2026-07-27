# -*- coding: utf-8 -*-
# 逐場稽核明細：每場活動 → email「@之後的網域」分佈（人次/去重人數）。
# 只輸出網域，不輸出任何完整 email / 姓名 / 個資。輸出 event_domains_2025.json 給頁面稽核區用。
import json, os, hashlib, urllib.request
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
YEAR = "2025"

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
    guests, offset = [], 0
    while True:
        body = {"fields": ["GUEST_DETAILS"],
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

out_events = []
grand_visits = defaultdict(int)
grand_people = defaultdict(set)

for ev in y_events:
    eid = ev["id"]
    date = (ev.get("dateAndTimeSettings", {}) or {}).get("startDate", "")[:10]
    title = ev.get("title", "") or ""
    status = ev.get("status", "")
    if status == "CANCELED":
        out_events.append({"date": date, "title": title, "status": "CANCELED",
                           "total_visits": 0, "total_people": 0, "domains": []})
        continue
    guests = get_guests(eid)
    dv = defaultdict(int)          # domain -> 人次
    dp = defaultdict(set)          # domain -> 去重人數(雜湊)
    no_email = 0
    for g in guests:
        gd = g.get("guestDetails", {}) or {}
        email = (gd.get("email", "") or "").strip().lower()
        if "@" in email:
            dom = "@" + email.split("@")[-1]
            dv[dom] += 1
            dp[dom].add(hemail(email))
            grand_visits[dom] += 1
            grand_people[dom].add(hemail(email))
        else:
            no_email += 1
    doms = sorted(
        [{"domain": d, "visits": dv[d], "people": len(dp[d])} for d in dv],
        key=lambda x: (-x["people"], -x["visits"], x["domain"])
    )
    out_events.append({
        "date": date, "title": title, "status": status,
        "total_visits": sum(dv.values()) + no_email,
        "total_people": sum(len(s) for s in dp.values()),
        "no_email": no_email,
        "domains": doms,
    })

# 全年網域總表（跨場去重）
grand = sorted(
    [{"domain": d, "visits": grand_visits[d], "people": len(grand_people[d])} for d in grand_visits],
    key=lambda x: (-x["people"], -x["visits"], x["domain"])
)

result = {
    "pulled_year": YEAR,
    "event_count": len(y_events),
    "events": out_events,
    "grand_domains": grand,
}
out_path = os.path.join(HERE, "event_domains_2025.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("場次：", len(y_events))
for e in out_events:
    print(f"  {e['date']} {e.get('status','')[:4]:4s} 人次{e['total_visits']:>3} 人數{e['total_people']:>3}  網域{len(e['domains'])}種")
print("\n全年不同網域：", len(grand))
print("已寫出（只有網域，無個資）：", out_path)
