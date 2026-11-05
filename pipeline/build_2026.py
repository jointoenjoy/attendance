# -*- coding: utf-8 -*-
"""產出 /2026（博報堂集團 2026 參與報告）的資料檔與下載檔。

收 Wix 報名表「所屬企業/集團」有選博報堂集團六家（MDCG／UCG／HTM／PILOT／KY-POST／INTERPLAN）的報名；
沒選企業的（多半是候補，候補表單不問公司）依序判斷（2026-11-05 決策者定，取代 10-01 的「只看網域」）：
  1. 本人在其他場次選過的公司（同一人不會一下 A 一下 B）
  2. 同網域其他人報名時選得最多的公司
  3. 都沒有才看 subsidiary_map 的網域對照表
私人信箱又沒選企業、選「練息之友」、選「非集團員工」的不納入。

同一人怎麼認（2026-11-05 決策者定）：email 相同，或「手機＋姓名＋集團」三者都相同（換信箱、email 打錯字）。
手機相同但姓名不同的不合併（多半是幫同事報名）。手機只拿來比對，不出現在頁面與下載檔。

輸出（全部含姓名與 email → 都在 .gitignore 裡、不進 git，只在 /2026 密碼後面提供）：
  site/2026/data.json            頁面資料
  site/2026/files/*.xlsx         全集團明細、全集團人員彙總、各公司明細（跟頁面同步：1/16 也列、暖灰底註明屬 2025 合約範圍）
頁面本身 site/2026/index.html 是空殼（不含個資），打開後才去抓 data.json。
"""
import json, os, re
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from wix2026 import year_events, load_events, has_checkin, today, HAKUHODO, YEAR_START, EXCLUDE_DATES
from subsidiary_map import UCG_SUBS, cat_of
from domain_verify import VERIFY, ALIAS

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


# 私人／公用信箱：同網域的人各自屬不同公司，不能拿來推
FREE_MAIL = {"gmail.com", "hotmail.com", "yahoo.com.tw", "yahoo.com", "msn.com", "outlook.com", "icloud.com",
             "jointoenjoy.com"}
CH = lambda n: re.sub(r"[^\u4e00-\u9fff]", "", n)


def same_name(a, b):
    """中文名字至少兩個字相同（容許打錯一字、英文名在前後、姓名順序顛倒）；沒有中文就比英文。"""
    ca, cb = CH(a), CH(b)
    if ca and cb:
        return len(set(ca) & set(cb)) >= min(2, len(ca), len(cb))
    return a.lower().replace(" ", "") == b.lower().replace(" ", "")


ALL = [g for e in load_events() for g in e["guests"]]
for g in ALL:
    g["email"] = g["email"].lower().strip()
    g["company"] = (g["company"] or "").upper() if (g["company"] or "").upper() in HAKUHODO else g["company"]

# 同一人：email 相同，或手機＋姓名＋集團相同 → 併成一個人（pid＝報名最多次的那個 email）
par = {}
def root(x):
    par.setdefault(x, x)
    while par[x] != x:
        par[x] = par[par[x]]; x = par[x]
    return x
picks = defaultdict(set)   # 每個 email 自己選過的博報堂公司
for g in ALL:
    root(g["email"])
    if g["company"] in HAKUHODO:
        picks[g["email"]].add(g["company"])
by_phone = defaultdict(list)
for g in ALL:
    if g["phone"]:
        by_phone[g["phone"]].append(g)
not_merged = []   # 手機相同、姓名不同 → 不合併，列進查核報告
for ph, gs in by_phone.items():
    for i, a in enumerate(gs):
        for b in gs[i + 1:]:
            if root(a["email"]) == root(b["email"]):
                continue
            ca = set().union(*(picks[x] for x in par if root(x) == root(a["email"])))
            cb = set().union(*(picks[x] for x in par if root(x) == root(b["email"])))
            if not same_name(a["name"], b["name"]):
                not_merged.append((a, b))
            elif not (ca and cb and not ca & cb):   # 集團也要一致（沒選過的不算衝突）
                par[root(a["email"])] = root(b["email"])
n_reg = Counter(g["email"] for g in ALL)
members = defaultdict(set)
for x in par:
    members[root(x)].add(x)
PID = {x: max(members[root(x)], key=lambda m: (n_reg[m], m)) for x in par}

own, dom_pick = defaultdict(Counter), defaultdict(Counter)
for g in ALL:
    if g["company"] in HAKUHODO:
        em = g["email"]
        own[PID[em]][g["company"]] += 1
        if em.split("@")[-1] not in FREE_MAIL:
            dom_pick[em.split("@")[-1]][g["company"]] += 1


def guess(email):
    """沒選公司的人歸哪家，回傳 (公司代碼, 判斷方式)。"""
    em = email.lower().strip()
    d = em.split("@")[-1]
    if own[PID[em]]:
        return own[PID[em]].most_common(1)[0][0], "依本人其他場次"
    if dom_pick[d]:
        return dom_pick[d].most_common(1)[0][0], "依同網域多數人所選"
    return CAT_CODE.get(cat_of(d), ""), "依 email 網域"


T = today()
events = year_events()   # 已報名但還沒辦的場次也列（2026-11-03 決策者要求），報到欄標「尚未舉辦」
# 1/16 那場屬 2025 報價單：照樣列名單給人看（頁面換底色註明），但不算進任何統計與下載檔（2026-11-03 決策者要求）
prev = [e for e in load_events() if "2026-01-01" <= e["date"] < YEAR_START
        and e["date"] not in EXCLUDE_DATES and e["status"] != "CANCELED"]
skipped = Counter()
skipped_st = Counter()   # 未納入的報名狀態，讓頁面能加回成 Wix 全部報名（＝年中報告的報名／候補／請假）
by_mail = Counter()
dom_rows = defaultdict(list)   # 網域歸戶表用
evs, recs = [], []
for e in prev + events:
    pv = e["date"] < YEAR_START
    up = e["date"] > T
    rec = has_checkin(e)
    gs = []
    for g in e["guests"]:
        code, src = (g["company"] or "").upper(), "報名選填"
        if not g["company"]:
            code, src = guess(g["email"])
        if code not in HAKUHODO:
            if not pv:
                skipped[g["company"] or "（未選企業・私人信箱）"] += 1
                skipped_st[g["status"]] += 1
            continue
        ck = "尚未舉辦" if up else ("已報到" if g["wix_checked_in"] else "未報到") if rec else "報到未登錄"
        gs.append({"n": g["name"], "e": g["email"].lower(), "p": PID[g["email"].lower().strip()], "c": code, "s": g["status"],
                   "k": ck, "m": src != "報名選填", "src": src})
        recs.append([e["date"], e["title"], "2025 合約範圍" if pv else "2026 合約範圍", NAMES[code],
                     g["name"], g["email"].lower(), g["status"], ck, src])
        if not pv:
            by_mail[src] += 1
            dom_rows[g["email"].lower().split("@")[-1]].append((e["date"], gs[-1], code, src))
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
        s["people"].add(g["p"]); s["rows"] += 1; s[g["s"]] += 1
        if g["k"] == "已報到":
            s["ck"] += 1; s["ck_people"].add(g["p"])
        p = person.setdefault(g["p"], {"n": g["n"], "c": set(), "reg": 0, "ok": 0, "ck": 0, "em": set()})
        p["em"].add(g["e"])
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
            pv_g[g["p"]] = g
            p = person.setdefault(g["p"], {"n": g["n"], "c": set(), "reg": 0, "ok": 0, "ck": 0, "em": set()})
            p["c"].add(NAMES[g["c"]]); p["em"].add(g["e"])
prow = lambda e, p: [p["n"], "、".join(sorted(p["em"])), "、".join(sorted(p["c"])), p["reg"], p["ok"], p["ck"],
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

# ── 統計查核報告（頁面彈出視窗）與網域歸戶表 ──
mask = lambda em: em[:2] + "***@" + em.split("@")[-1]
in26 = {g["p"] for e in evs if not e["prev"] for g in e["guests"]}
merged = []
for pid in sorted(in26):
    ems = sorted(members[root(pid)])
    if len(ems) > 1:
        gs = [g for e in evs if not e["prev"] for g in e["guests"] if g["p"] == pid]
        merged.append({"n": person[pid]["n"], "c": NAMES[gs[0]["c"]], "emails": [mask(x) for x in ems],
                       "why": "手機、姓名、集團都相同"})
nm = []
for a, b in not_merged:
    k = {a["email"], b["email"]}
    if (PID[a["email"]] in in26 or PID[b["email"]] in in26) and all(set(x["emails"]) != {mask(y) for y in k} for x in nm):
        nm.append({"names": [a["name"], b["name"]], "emails": [mask(a["email"]), mask(b["email"])]})
shared = []   # 同一個 email 報了不同姓名的人（可能是幫別人報名），目前算一人
for em in {g["e"] for e in evs if not e["prev"] for g in e["guests"]}:
    ns = sorted({g["name"] for g in ALL if g["email"] == em})
    if any(not same_name(x, y) and len(CH(x)) >= 2 and len(CH(y)) >= 2 for x in ns for y in ns):
        shared.append({"names": ns, "email": mask(em)})
audit = {
    "fixes": [   # 2026-11-05 這一波修正（集團人資回報同一人歸到兩家公司）
        {"what": "1 人 3 筆（unistyle 網域：3/20、11/5、11/6）", "from": "聯廣 UCG", "to": "先勢集團 PILOT",
         "why": "聯太國際公關屬先勢集團，網域對照表更正"},
        {"what": "1 人 1 筆（ua.com.tw 網域：3/20 候補）", "from": "聯廣 UCG", "to": "台北博報堂 HTM",
         "why": "本人其他場次都選台北博報堂，改依本人"},
        {"what": "1 人 1 筆（私人信箱：7/30 正取、已報到）", "from": "未納入", "to": "米蘭 MDCG",
         "why": "本人其他場次選米蘭，原本漏算，補進來"},
    ],
    "email_people": len({g["e"] for e in evs if not e["prev"] for g in e["guests"]}),
    "merged": merged, "not_merged": nm, "shared": shared,
    "methods": [[k, by_mail[k]] for k in ["報名選填", "依本人其他場次", "依同網域多數人所選", "依 email 網域"]],
}
PRIVATE = FREE_MAIL - {"jointoenjoy.com"}
domains = []
for d, rs in dom_rows.items():
    canon = ALIAS.get(d, d)
    v = VERIFY.get(canon)
    co = Counter(c for _, _, c, _ in rs)
    pick = Counter(c for _, _, c, src in rs if src == "報名選填")
    ppl = {g["p"] for _, g, _, _ in rs}
    if d == "jointoenjoy.com":
        st, why = "不適用", "練息場自家信箱，依本人報名時所選"
    elif d in PRIVATE:
        st, why = "不適用", "私人信箱，每個人依自己報名時選的公司"
    elif len(co) > 1:
        st, why = "需確認", "同網域的人分屬不同公司（依各人報名時所選）"
    elif not v:
        st, why = "需確認", "網路查無這個網域屬哪家公司"
    elif not v[1]:
        st, why = "需確認", v[4]
    elif v[1] != next(iter(co)):
        st, why = "需確認", "網路查證結果跟目前歸戶不同"
    elif d != canon:
        st, why = "需確認", "疑似 email 打錯字（應為 %s）" % canon
    elif v[2] == "低":
        st, why = "需確認", "網路查證把握度低"
    else:
        st, why = "一致", "報名自選與網路查證一致"
    domains.append({
        "d": d, "canon": canon if canon != d else "", "co": [[NAMES[c], n] for c, n in co.most_common()],
        "pick": [[NAMES[c], n] for c, n in pick.most_common()], "people": len(ppl), "rows": len(rs),
        "v": {"name": v[0], "code": NAMES.get(v[1], "查無"), "conf": v[2], "src": v[3], "note": v[4]} if v else None,
        "st": st, "why": why,
    })
domains.sort(key=lambda x: ({"需確認": 0, "一致": 1, "不適用": 2}[x["st"]], -x["people"], x["d"]))
# 給集團人資確認的網域表（只有網域與公司，不含個資）
files["domains"] = write_xlsx("2026-email網域歸戶確認表.xlsx",
    ["email 網域", "目前歸戶公司", "人數", "報名筆數", "狀態", "說明", "網路查證公司", "查證歸屬", "把握程度", "查證來源", "人資確認（請填）"],
    [[x["d"], "、".join("%s %d 筆" % (c, n) for c, n in x["co"]), x["people"], x["rows"], x["st"], x["why"],
      x["v"]["name"] if x["v"] else "", x["v"]["code"] if x["v"] else "", x["v"]["conf"] if x["v"] else "",
      x["v"]["src"] if x["v"] else "", ""] for x in domains],
    widths=[22, 30, 8, 10, 10, 34, 28, 18, 10, 40, 22])

nocheck = [e["date"] for e in evs if not e["recorded"] and not e["upcoming"] and not e["prev"]]
data = {
    "generated": (datetime.now(timezone.utc) + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M"),
    "asof": T, "upcoming": [e["date"] for e in evs if e["upcoming"]], "events": evs, "companies": companies, "files": files,
    "totals": {"events": sum(not e["prev"] for e in evs), "people": sum(p["reg"] > 0 for p in person.values()),
               "rows": sum(r[2].startswith("2026") for r in recs),
               "ok": sum(c["正取"] for c in companies),
               "ck": sum(c["ck"] for c in companies), "ck_people": len({e for e, p in person.items() if p["ck"]})},
    "nocheck": nocheck, "skipped": dict(skipped.most_common()), "skipped_st": dict(skipped_st), "by_mail": sum(v for k, v in by_mail.items() if k != "報名選填"),
    "audit": audit, "domains": domains,
}
os.makedirs(SITE, exist_ok=True)
json.dump(data, open(os.path.join(SITE, "data.json"), "w", encoding="utf-8"), ensure_ascii=False,
          separators=(",", ":"))
t = data["totals"]
print("/2026：%d 場｜博報堂 %d 人、%d 筆報名、報到 %d 人次｜各公司 %s"
      % (t["events"], t["people"], t["rows"], t["ck"], ", ".join("%s %d" % (c["code"], c["people"]) for c in companies)))
print("依 email 補進：%d 筆｜未納入：%s｜報到未登錄：%s" % (data["by_mail"], data["skipped"], nocheck))
