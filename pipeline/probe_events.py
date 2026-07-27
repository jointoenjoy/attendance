# -*- coding: utf-8 -*-
import json, os, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
env = {}
with open(os.path.join(HERE, "keys.env"), encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()

AUTH = env["WIX_API_AUTHORIZATION"]
SITE = env["WIX_API_SITE_ID"]
BASE = env["WIX_API_BASE_URL"].rstrip("/") + "/"

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": AUTH,
    "wix-site-id": SITE,
}

def post(path, body):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode("utf-8"),
                                 headers=HEADERS, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))

body = {
    "fields": ["REGISTRATION"],
    "includeDrafts": False,
    "query": {
        "filter": {},
        "paging": {"limit": 100},
        "sort": [{"fieldName": "createdDate", "order": "ASC"}],
    },
}

try:
    res = post("events/v3/events/query", body)
except urllib.error.HTTPError as e:
    print("HTTP", e.code, e.read().decode("utf-8")[:500])
    raise SystemExit(1)

events = res.get("events", [])
print("活動總數：", len(events))
# print a few structural samples (no PII in events)
for ev in events[:3]:
    print("---")
    print("keys:", list(ev.keys()))
    print(json.dumps({k: ev.get(k) for k in ("id", "title", "status")}, ensure_ascii=False))
    # find date-ish fields
    for dk in ("dateAndTimeSettings", "scheduling", "dateAndTime", "created", "createdDate"):
        if dk in ev:
            print(dk, "=>", json.dumps(ev[dk], ensure_ascii=False)[:300])
