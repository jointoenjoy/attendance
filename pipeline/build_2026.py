# -*- coding: utf-8 -*-
"""產出 /2026（博報堂集團 2026 參與報告）的資料檔與下載檔。

收 Wix 報名表「所屬企業/集團」有選博報堂集團六家（MDCG／UCG／HTM／PILOT／KY-POST／INTERPLAN）的報名；
沒選企業的（多半是候補，候補表單不問公司）改看 email 網域，是集團信箱就照網域歸到該公司（2026-10-01 決策者定）。
私人信箱又沒選企業、選「練息之友」、選「非集團員工」的不納入。

輸出（全部含姓名與 email → 都在 .gitignore 裡、不進 git，只在 /2026 密碼後面提供）：
  site/2026/data.json            頁面資料
  site/2026/files/*.xlsx         全集團明細、全集團人員彙總、各公司明細（跟頁面同步：1/16 也列、暖灰底註明屬 2025 合約範圍）
頁面本身 site/2026/index.html 是空殼（不含個資），打開後才去抓 data.json。
"""
import json, os
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from wix2026 import year_events, load_events, has_checkin, today, HAKUHODO, YEAR_START, EXCLUDE_DATES
from subsidiary_map import UCG_SUBS, cat_of

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(os.path.dirname(HERE), "site", "2026")
FILES = os.path.join(SITE, "files")
NAMES = {"MDCG": "米蘭 MDCG", "UCG": "聯廣 UCG", "HTM": "台北博報堂 HTM", "PILOT": "先勢集團 PILOT",
         "KY-POST": "光洋波斯特 KY-POST", "INTERPLAN": "安益 INTERPLAN"}
CAT_CODE = dict({c: "UCG" for c in UCG_SUBS}, **{"先勢集團": "PILOT", "台北博報堂 HTM": "HTM",
                "米蘭 MDCG": "MDCG", "光洋波斯特": "KY-POST", "安益": "INTERPLAN"})


PREV_FILL = PatternFill("solid", fgColor="F3EADB")   # 跟頁面 1/16 場次同一個暖灰底
HEAD_FILL = PatternFill("solid", fgColor="004D89")
PREV_NOTE = "暖灰底＝1/16《動態靜心》，屬 2025 練息場合約範圍；其餘屬 2026 合約範圍（3/20 起）。是否計入請自行判斷。"


def write_xlsx(name, head, rows, prev_col=None, widths=None, prev_cols=()):
    """寫 Excel 下載檔。prev_col＝第幾欄（0 起算）標示 2025 合約範圍，那幾列整列上暖灰底；
    prev_cols＝整欄都屬 2025 合約範圍的欄位（人員彙總的 1/16 欄），整欄上暖灰底。
    姓名、活動名稱等文字一律存成純文字（data_type="s"），開頭是 = 也不會被當公式執行。"""
    os.makedirs(FILES, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = "明細"
    ws.append([PREV_NOTE])
    ws["A1"].font = Font(name="Arial", size=10, color="7A5A2E")
    ws.append(head)
    for c in ws[2]:
        c.font = Font(name="Arial", bold=True, color="FFFFFF")
        c.fill = HEAD_FILL
        c.alignment = Alignment(vertical="center")
    for r in rows:
        ws.append(r)
        prev = prev_col is not None and str(r[prev_col]).startswith("2025")
        for c in ws[ws.max_row]:
            if isinstance(c.value, str):
                c.data_type = "s"
            c.font = Font(name="Arial")
            if prev or c.column - 1 in prev_cols:
                c.fill = PREV_FILL
    for i, w in enumerate(widths or [], 1):
        ws.column_dimensions[ws.cell(2, i).column_letter].width = w
    ws.freeze_panes = "A3"
    ws.auto_filter.ref = "A2:%s%d" % (ws.cell(2, len(head)).column_letter, ws.max_row)
    wb.save(os.path.join(FILES, name))
    return {"name": name, "url": "/2026/files/" + name, "rows": len(rows),
            "kb": max(1, round(os.path.getsize(os.path.join(FILES, name)) / 1024))}


T = today()
events = year_events()   # 已報名但還沒辦的場次也列（2026-11-03 決策者要求），報到欄標「尚未舉辦」
# 1/16 那場屬 2025 報價單：照樣列名單給人看（頁面換底色註明），但不算進任何統計與下載檔（2026-11-03 決策者要求）
prev = [e for e in load_events() if "2026-01-01" <= e["date"] < YEAR_START
        and e["date"] not in EXCLUDE_DATES and e["status"] != "CANCELED"]
skipped = Counter()
skipped_st = Counter()   # 未納入的報名狀態，讓頁面能加回成 Wix 全部報名（＝年中報告的報名／候補／請假）
by_mail = Counter()
evs, recs = [], []
for e in prev + events:
    pv = e["date"] < YEAR_START
    up = e["date"] > T
    rec = has_checkin(e)
    gs = []
    for g in e["guests"]:
        code, src = (g["company"] or "").upper(), "報名選填"
        if not g["company"]:
            code, src = CAT_CODE.get(cat_of(g["email"].split("@")[-1]), ""), "依 email 判斷"
        if code not in HAKUHODO:
            if not pv:
                skipped[g["company"] or "（未選企業・私人信箱）"] += 1
                skipped_st[g["status"]] += 1
            continue
        ck = "尚未舉辦" if up else ("已報到" if g["wix_checked_in"] else "未報到") if rec else "報到未登錄"
        gs.append({"n": g["name"], "e": g["email"].lower(), "c": code, "s": g["status"], "k": ck, "m": src != "報名選填"})
        recs.append([e["date"], e["title"], "2025 合約範圍" if pv else "2026 合約範圍", NAMES[code],
                     g["name"], g["email"].lower(), g["status"], ck, src])
        if not pv:
            by_mail[src] += 1
    gs.sort(key=lambda x: (HAKUHODO.index(x["c"]), ["正取", "候補", "請假"].index(x["s"]), x["n"]))
    evs.append({"date": e["date"], "title": e["title"], "recorded": rec, "upcoming": up, "prev": pv, "guests": gs})

# 各公司彙總
comp = {c: {"code": c, "name": NAMES[c], "people": set(), "rows": 0, "正取": 0, "候補": 0, "請假": 0,
            "ck": 0, "ck_people": set()} for c in HAKUHODO}
person = {}
for e in evs:
    if e["prev"]:
        continue
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

# 下載檔跟頁面同步（2026-11-03 決策者要求）：1/16 也列，暖灰底註明屬 2025 合約範圍，由看的人自己判斷要不要算
HEAD = ["日期", "活動名稱", "合約範圍", "所屬企業", "姓名", "email", "報名狀態", "報到", "企業判斷方式"]
W = [12, 44, 14, 18, 14, 32, 10, 12, 14]
pv_g = {}   # 1/16 那場每個人的報名狀態與報到
for e in evs:
    if e["prev"]:
        for g in e["guests"]:
            pv_g[g["e"]] = g
            person.setdefault(g["e"], {"n": g["n"], "c": set(), "reg": 0, "ok": 0, "ck": 0})["c"].add(NAMES[g["c"]])
prow = lambda e, p: [p["n"], e, "、".join(sorted(p["c"])), p["reg"], p["ok"], p["ck"],
                     pv_g[e]["s"] if e in pv_g else "", pv_g[e]["k"] if e in pv_g else ""]
files = {"all": write_xlsx("2026-博報堂全集團-逐筆明細.xlsx", HEAD, recs, 2, W),
         "people": write_xlsx("2026-博報堂全集團-人員彙總.xlsx",
                              ["姓名", "email", "所屬企業", "2026 報名場次", "2026 正取場次", "2026 報到場次",
                               "1/16 報名狀態（2025 合約範圍）", "1/16 報到（2025 合約範圍）"],
                              sorted([prow(e, p) for e, p in person.items()], key=lambda r: (r[2], -r[3], r[0])),
                              widths=[14, 32, 18, 14, 14, 14, 26, 24], prev_cols=(6, 7)),
         "byco": {}}
for c in companies:
    files["byco"][c["code"]] = write_xlsx("2026-%s-逐筆明細.xlsx" % c["code"], HEAD,
                                          [r for r in recs if r[3] == c["name"]], 2, W)

nocheck = [e["date"] for e in evs if not e["recorded"] and not e["upcoming"] and not e["prev"]]
data = {
    "generated": (datetime.now(timezone.utc) + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M"),
    "asof": T, "upcoming": [e["date"] for e in evs if e["upcoming"]], "events": evs, "companies": companies, "files": files,
    "totals": {"events": sum(not e["prev"] for e in evs), "people": sum(p["reg"] > 0 for p in person.values()),
               "rows": sum(r[2].startswith("2026") for r in recs),
               "ok": sum(c["正取"] for c in companies),
               "ck": sum(c["ck"] for c in companies), "ck_people": len({e for e, p in person.items() if p["ck"]})},
    "nocheck": nocheck, "skipped": dict(skipped.most_common()), "skipped_st": dict(skipped_st), "by_mail": by_mail["依 email 判斷"],
}
os.makedirs(SITE, exist_ok=True)
json.dump(data, open(os.path.join(SITE, "data.json"), "w", encoding="utf-8"), ensure_ascii=False,
          separators=(",", ":"))
t = data["totals"]
print("/2026：%d 場｜博報堂 %d 人、%d 筆報名、報到 %d 人次｜各公司 %s"
      % (t["events"], t["people"], t["rows"], t["ck"], ", ".join("%s %d" % (c["code"], c["people"]) for c in companies)))
print("依 email 補進：%d 筆｜未納入：%s｜報到未登錄：%s" % (data["by_mail"], data["skipped"], nocheck))
