# -*- coding: utf-8 -*-
# 從 Wix 拉「每場 × 每網域」的 正取(ATTENDING)/候補(IN_WAITLIST)/請假(NOT_ATTENDING)。
# 只輸出網域與計數，絕不寫入 email 帳號或姓名。輸出 wix_states.json。
import json, os, urllib.request
from collections import defaultdict
from probe_events import BASE, HEADERS

HERE = os.path.dirname(os.path.abspath(__file__))

def call(m, p, b=None):
    d = json.dumps(b).encode("utf-8") if b is not None else None
    req = urllib.request.Request(BASE + p, data=d, headers=HEADERS, method=m)
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))

def get_events():
    body = {"fields": ["REGISTRATION"], "includeDrafts": False,
            "query": {"filter": {}, "paging": {"limit": 100}}}
    return call("POST", "events/v3/events/query", body).get("events", [])

def get_guests(eid):
    out, off = [], 0
    while True:
        body = {"fields": ["GUEST_DETAILS", "GUEST_TOTAL"],
                "query": {"filter": {"guestType": "RSVP", "eventId": eid},
                          "paging": {"limit": 100, "offset": off}}}
        b = call("POST", "events/v2/guests/query", body).get("guests", []) or []
        out += b; off += len(b)
        if len(b) < 100:
            break
    return out

STATE = {"ATTENDING": "att", "IN_WAITLIST": "wait", "NOT_ATTENDING": "leave"}

evs = [e for e in get_events()
       if (e.get("dateAndTimeSettings", {}) or {}).get("startDate", "")[:4] in ("2025", "2026")
       and e.get("status") != "CANCELED"]
evs.sort(key=lambda e: e["dateAndTimeSettings"]["startDate"])

out = []
for e in evs:
    d = e["dateAndTimeSettings"]["startDate"][:10]
    gs = get_guests(e["id"])
    dom = defaultdict(lambda: {"att": 0, "wait": 0, "leave": 0})
    tot = {"att": 0, "wait": 0, "leave": 0}
    for g in gs:
        email = ((g.get("guestDetails", {}) or {}).get("email", "") or "").strip().lower()
        domain = email.split("@")[-1] if "@" in email else "(無email)"
        st = STATE.get(g.get("attendanceStatus", ""), None)
        if st is None:
            continue
        dom[domain][st] += 1
        tot[st] += 1
    out.append({
        "date": d, "year": d[:4], "title": e.get("title", "").strip(),
        "status": e.get("status", ""), "guests": len(gs), "totals": tot,
        "domains": sorted(
            [{"d": k, **v} for k, v in dom.items()],
            key=lambda x: (-(x["att"] + x["wait"] + x["leave"]), x["d"]))
    })

json.dump(out, open(os.path.join(HERE, "wix_states.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

print("場次數：", len(out))
print("\n日期        正取 候補 請假  guests  活動")
for r in out:
    t = r["totals"]
    print("%-10s %4d %4d %4d %6d   %s" % (
        r["date"], t["att"], t["wait"], t["leave"], r["guests"], r["title"][:22]))
print("\n已寫出 wix_states.json（只含網域與計數）")
