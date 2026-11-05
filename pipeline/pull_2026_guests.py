# -*- coding: utf-8 -*-
"""從 Wix 拉 2026 每場活動的報名名單 → _private/wix_2026_guests.json（含姓名與 email，不進 git）。

只取：姓名、email、手機、所屬企業/集團（下拉）、報名狀態、Wix 報到勾選。
手機只拿來交叉比對「是不是同一人」（2026-11-05 決策者要求：姓名＋集團＋手機），只存在 _private、不上任何頁面與下載檔。
表單裡的身分證、生日、身高體重等欄位一律不讀、不存。
"""
import json, os, re, urllib.request
from probe_events import BASE, HEADERS

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "_private", "wix_2026_guests.json")
STATE = {"ATTENDING": "正取", "IN_WAITLIST": "候補", "NOT_ATTENDING": "請假"}


def clean_name(name):
    """報名者常把電話／分機打進姓名欄（例如 02-2758xxxx#523王小明），畫面只留人名。"""
    name = re.sub(r"[(（][^)）]*[)）]?", "", name)          # 括號備註
    name = re.sub(r"[0-9０-９#＃*＊/／,，\-－_]+", " ", name)  # 電話、分機與符號
    name = re.sub(r"(?i)\b(ext|tel|mobile|phone)\b\.?|分機|手機|電話", " ", name)
    name = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", name)  # 中文字中間不留空白
    return re.sub(r"\s+", " ", name).strip()


def phone_of(*texts):
    """從姓名欄或電話欄抓台灣手機，統一成 09xxxxxxxx；抓不到回空字串。"""
    for t in texts:
        d = re.sub(r"[^0-9０-９+]", "", t or "").translate(str.maketrans("０１２３４５６７８９", "0123456789"))
        d = re.sub(r"^\+?886", "0", d)
        m = re.search(r"09\d{8}", d)
        if m:
            return m.group(0)
    return ""


def call(m, p, b=None):
    d = json.dumps(b).encode("utf-8") if b is not None else None
    req = urllib.request.Request(BASE + p, data=d, headers=HEADERS, method=m)
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))


def get_events():
    out, off = [], 0
    while True:
        body = {"fields": ["REGISTRATION"], "includeDrafts": False,
                "query": {"filter": {}, "paging": {"limit": 100, "offset": off}}}
        b = call("POST", "events/v3/events/query", body).get("events", []) or []
        out += b; off += len(b)
        if len(b) < 100:
            return out


def form_ids(eid):
    """回傳 (所屬企業欄 id, 電話欄 id)。"""
    res = call("GET", "events/v1/events/%s/form" % eid)
    cs = (res.get("form", {}) or {}).get("controls", []) or []
    return ({c.get("id") for c in cs if "所屬企業/集團" in (c.get("label") or "")},
            {c.get("id") for c in cs if re.search("電話|手機", c.get("label") or "") and c.get("id") != "name"})


def get_guests(eid):
    out, off = [], 0
    while True:
        body = {"fields": ["GUEST_DETAILS"],
                "query": {"filter": {"guestType": "RSVP", "eventId": eid},
                          "paging": {"limit": 100, "offset": off}}}
        b = call("POST", "events/v2/guests/query", body).get("guests", []) or []
        out += b; off += len(b)
        if len(b) < 100:
            return out


def main():
    evs = [e for e in get_events()
           if (e.get("dateAndTimeSettings", {}) or {}).get("startDate", "")[:4] == "2026"]
    evs.sort(key=lambda e: e["dateAndTimeSettings"]["startDate"])
    out = []
    for e in evs:
        canceled = e.get("status") == "CANCELED"     # 取消場只留場次資訊給 /all 資料稽核
        cids, pids = (set(), set()) if canceled else form_ids(e["id"])
        rows = []
        for g in ([] if canceled else get_guests(e["id"])):
            st = STATE.get(g.get("attendanceStatus", ""))
            if st is None:
                continue
            gd = g.get("guestDetails", {}) or {}
            comp, ptxt = "", ""
            for iv in (gd.get("formResponse", {}) or {}).get("inputValues", []) or []:
                if iv.get("inputName") in cids:
                    comp = (iv.get("value") or (iv.get("values") or [""])[0] or "").strip()
                if iv.get("inputName") in pids:
                    ptxt = iv.get("value") or ""
            name = ((gd.get("lastName") or "") + (gd.get("firstName") or "")).strip() \
                if not (gd.get("firstName") or "").isascii() else \
                " ".join(x for x in (gd.get("firstName"), gd.get("lastName")) if x).strip()
            rows.append({"name": clean_name(name), "email": (gd.get("email") or "").strip().lower(),
                         "phone": phone_of(name, ptxt), "company": comp, "status": st, "wix_checked_in": bool(gd.get("checkedIn"))})
        # Wix 的 startDate 是 UTC，換成台北日期
        from datetime import datetime, timedelta
        d = (datetime.fromisoformat(e["dateAndTimeSettings"]["startDate"].replace("Z", "+00:00"))
             + timedelta(hours=8)).strftime("%Y-%m-%d")
        out.append({"date": d, "title": e.get("title", "").strip(), "status": e.get("status", ""),
                    "has_company_field": bool(cids), "guests": rows})
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for ev in out:
        gs = ev["guests"]
        print(ev["date"], ev["status"][:5], "公司欄" if ev["has_company_field"] else "無公司欄",
              "報名", len(gs), "有選企業", sum(1 for g in gs if g["company"]),
              "Wix報到", sum(g["wix_checked_in"] for g in gs), "|", ev["title"][:28])


if __name__ == "__main__":
    main()
