# -*- coding: utf-8 -*-
# 全 2025-2026 場：完整分布。不印 email/姓名，只印計數。
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

def rsvp(g):
    return ((g.get("guestDetails", {}) or {}).get("additionalDetails", {}) or {}).get("rsvpStatus") \
        or g.get("additionalDetails", {}).get("rsvpStatus") if isinstance(g.get("additionalDetails"), dict) else \
        ((g.get("guestDetails", {}) or {}).get("additionalDetails", {}) or {}).get("rsvpStatus")

evs = [e for e in get_events()
       if (e.get("dateAndTimeSettings", {}) or {}).get("startDate", "")[:4] in ("2025", "2026")]
evs.sort(key=lambda e: e["dateAndTimeSettings"]["startDate"])

print("日期        場數狀態  Guests  rsvp:YES/NO/WAIT/none    attend:ATT/NOTATT/NOTPRE/none  checkedIn")
TY = TN = TW = TNone = TG = TCI = 0
for e in evs:
    d = e["dateAndTimeSettings"]["startDate"][:10]
    if e.get("status") == "CANCELED":
        continue
    gs = get_guests(e["id"])
    r = Counter()
    a = Counter()
    ci = 0
    for g in gs:
        rv = ((g.get("guestDetails", {}) or {}).get("additionalDetails") or {}).get("rsvpStatus") or "none"
        r[rv] += 1
        a[g.get("attendanceStatus") or "none"] += 1
        if (g.get("guestDetails", {}) or {}).get("checkedIn"):
            ci += 1
    TY += r["YES"]; TN += r["NO"]; TW += r["WAITING"]; TNone += r["none"]; TG += len(gs); TCI += ci
    print("%-10s %-8s %4d    %3d/%2d/%2d/%3d           %3d/%3d/%3d/%3d          %3d   %s" % (
        d, (e.get("status") or "")[:7], len(gs),
        r["YES"], r["NO"], r["WAITING"], r["none"],
        a["ATTENDING"], a["NOT_ATTENDING"], a["NOT_PRESENT"], a["none"], ci,
        e.get("title", "")[:20]))
print("\n合計 Guests=%d  YES=%d NO=%d WAIT=%d none=%d  checkedIn=%d" % (TG, TY, TN, TW, TNone, TCI))
