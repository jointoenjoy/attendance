# -*- coding: utf-8 -*-
"""產出 /2026（博報堂集團 2026 參與報告）的資料檔與下載檔。

只收 Wix 報名表「所屬企業/集團」有選博報堂集團六家（MDCG／UCG／HTM／PILOT／KY-POST／INTERPLAN）的報名；
沒選企業、選「練息之友」、選「非集團員工」的一律不納入。

輸出（全部含姓名與 email → 都在 .gitignore 裡、不進 git，只在 /2026 密碼後面提供）：
  site/2026/data.json            頁面資料
  site/2026/files/*.csv          全集團明細、全集團人員彙總、各公司明細（UTF-8 BOM，Excel 直接開不亂碼）
頁面本身 site/2026/index.html 是空殼（不含個資），打開後才去抓 data.json。
"""
import csv, io, json, os
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from wix2026 import year_events, has_checkin, today, HAKUHODO

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(os.path.dirname(HERE), "site", "2026")
FILES = os.path.join(SITE, "files")
NAMES = {"MDCG": "米蘭 MDCG", "UCG": "聯廣 UCG", "HTM": "台北博報堂 HTM", "PILOT": "先勢集團 PILOT",
         "KY-POST": "光洋波斯特 KY-POST", "INTERPLAN": "安益 INTERPLAN"}


def safe(v):
    """擋 Excel 公式注入：開頭是 = + - @ 的欄位前面補 '。"""
    v = "" if v is None else str(v)
    return "'" + v if v[:1] in ("=", "+", "-", "@") else v


def write_csv(name, head, rows):
    os.makedirs(FILES, exist_ok=True)
    with io.open(os.path.join(FILES, name), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(head)
        w.writerows([[safe(c) for c in r] for r in rows])
    return {"name": name, "url": "/2026/files/" + name, "rows": len(rows),
            "kb": max(1, round(os.path.getsize(os.path.join(FILES, name)) / 1024))}


T = today()
events = [e for e in year_events() if e["date"] <= T]
skipped = Counter()
evs, recs = [], []
for e in events:
    rec = has_checkin(e)
    gs = []
    for g in e["guests"]:
        code = (g["company"] or "").upper()
        if code not in HAKUHODO:
            skipped[g["company"] or "（未選企業）"] += 1
            continue
        ck = ("已報到" if g["wix_checked_in"] else "未報到") if rec else "報到未登錄"
        gs.append({"n": g["name"], "e": g["email"].lower(), "c": code, "s": g["status"], "k": ck})
        recs.append([e["date"], e["title"], NAMES[code], g["name"], g["email"].lower(), g["status"], ck])
    gs.sort(key=lambda x: (HAKUHODO.index(x["c"]), ["正取", "候補", "請假"].index(x["s"]), x["n"]))
    evs.append({"date": e["date"], "title": e["title"], "recorded": rec, "guests": gs})

# 各公司彙總
comp = {c: {"code": c, "name": NAMES[c], "people": set(), "rows": 0, "正取": 0, "候補": 0, "請假": 0,
            "ck": 0, "ck_people": set()} for c in HAKUHODO}
person = {}
for e in evs:
    for g in e["guests"]:
        s = comp[g["c"]]
        s["people"].add(g["e"]); s["rows"] += 1; s[g["s"]] += 1
        if g["k"] == "已報到":
            s["ck"] += 1; s["ck_people"].add(g["e"])
        p = person.setdefault(g["e"], {"n": g["n"], "c": set(), "reg": 0, "ok": 0, "ck": 0})
        p["c"].add(NAMES[g["c"]]); p["reg"] += 1; p["ok"] += g["s"] == "正取"; p["ck"] += g["k"] == "已報到"
companies = [dict(s, people=len(s["people"]), ck_people=len(s["ck_people"])) for s in comp.values()]
companies = [c for c in companies if c["rows"]]
companies.sort(key=lambda c: (-c["people"], -c["rows"]))

HEAD = ["日期", "活動名稱", "所屬企業", "姓名", "email", "報名狀態", "報到"]
files = {"all": write_csv("2026-博報堂全集團-逐筆明細.csv", HEAD, recs),
         "people": write_csv("2026-博報堂全集團-人員彙總.csv",
                             ["姓名", "email", "所屬企業", "報名場次", "正取場次", "報到場次"],
                             sorted([[p["n"], e, "、".join(sorted(p["c"])), p["reg"], p["ok"], p["ck"]]
                                     for e, p in person.items()], key=lambda r: (r[2], -r[3], r[0]))),
         "byco": {}}
for c in companies:
    files["byco"][c["code"]] = write_csv("2026-%s-逐筆明細.csv" % c["code"], HEAD,
                                         [r for r in recs if r[2] == c["name"]])

nocheck = [e["date"] for e in evs if not e["recorded"]]
data = {
    "generated": (datetime.now(timezone.utc) + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M"),
    "asof": T, "events": evs, "companies": companies, "files": files,
    "totals": {"events": len(evs), "people": len(person), "rows": len(recs),
               "ok": sum(c["正取"] for c in companies),
               "ck": sum(c["ck"] for c in companies), "ck_people": len({e for e, p in person.items() if p["ck"]})},
    "nocheck": nocheck, "skipped": dict(skipped.most_common()),
}
os.makedirs(SITE, exist_ok=True)
json.dump(data, open(os.path.join(SITE, "data.json"), "w", encoding="utf-8"), ensure_ascii=False,
          separators=(",", ":"))
t = data["totals"]
print("/2026：%d 場｜博報堂 %d 人、%d 筆報名、報到 %d 人次｜各公司 %s"
      % (t["events"], t["people"], t["rows"], t["ck"], ", ".join("%s %d" % (c["code"], c["people"]) for c in companies)))
print("未納入：%s｜報到未登錄：%s" % (data["skipped"], nocheck))
