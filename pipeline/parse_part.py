# -*- coding: utf-8 -*-
"""讀原始 Google 試算表匯出（pipeline/_private/sheet_2026.txt，含姓名與完整 email，不進 git），
產出去識別化的 pipeline/part_summary.json 給 /part 頁使用。

輸出只含：子公司層級數字、email「@ 之後的網域（已合併變體）」、以及需要人工確認的歸戶例外（帳號已遮罩）。

【網域合併】現場是手 key 的，.com.tw / .com 與拼字常有誤，
所以一律以 subsidiary_map.GROUPS 的 key 為單位合併後再呈現。
"""
import json, os, re
from collections import defaultdict

from subsidiary_map import (GROUPS, GROUP_BY_KEY, UCG_SUBS, PAGE_CATS, OTHER_CATS,
                            group_of, cat_of, label2cat)

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "_private", "sheet_2026.txt")
LINES = open(RAW, encoding="utf-8").read().splitlines()

# 試算表「所屬企業/集團」欄的代碼 -> 我們的分類家族（用來抓歸戶衝突）
CODE_FAMILY = {
    "UCG": set(UCG_SUBS),
    "HTM": {"台北博報堂 HTM"},
    "PILOT": {"先勢集團"},
    "MDCG": {"米蘭 MDCG"},
    "KY-POST": {"光洋波斯特"}, "KYPOST": {"光洋波斯特"},
    "INTERPLAN": {"安益"},
}
HELD = ["0320", "0327", "0417", "0522", "0717"]          # 截至 7/17 已辦
FUTURE = ["0730", "0731苔球", "0731聲波"]                 # 尚未舉辦


def cells(line):
    if not line.strip().startswith("|"):
        return None
    return [c.strip() for c in line.strip().strip("|").split("|")]


def mask(email):
    user, _, dom = email.partition("@")
    return (user[:2] if len(user) > 2 else user[:1]) + "***@" + dom


# ============ 2025：現場報到頻度表（姓名｜公司｜次數）============
y2025 = defaultdict(lambda: {"visits": 0, "people": 0})
in_freq = False
for ln in LINES:
    c = cells(ln)
    if not c:
        continue
    if len(c) >= 3 and c[0] == "姓名" and c[1] == "公司":
        in_freq = True
        continue
    if not in_freq:
        continue
    if len(c) >= 3 and c[0] and c[1] and re.fullmatch(r"\d+", c[2] or ""):
        if c[0] == "總計":
            continue
        cat = label2cat(c[1])
        if cat:
            y2025[cat]["visits"] += int(c[2])
            y2025[cat]["people"] += 1
    if len(c) >= 2 and "2025上半年活動" in (c[1] if len(c) > 1 else ""):
        break

# ============ 2025：逐場現場名冊矩陣（每場一組「姓名｜公司」）============
# 用來把 2025 各場的報到拆出來；加總會等於上面頻度表的人次。
ev2025 = []
hi = None
for i, ln in enumerate(LINES):
    c = cells(ln)
    if c and len(c) > 2 and (c[1] or "").startswith("2025/2/21"):
        hi = i
        break
if hi is not None:
    hdr, sub = cells(LINES[hi]), cells(LINES[hi + 1])
    cols = []
    for j in range(1, len(hdr), 2):
        if re.fullmatch(r"20\d\d/\d+/\d+", hdr[j] or ""):
            y, m, d = hdr[j].split("/")
            cols.append((j, "%s-%02d-%02d" % (y, int(m), int(d)),
                         sub[j] if j < len(sub) else ""))
    tally = {k: defaultdict(int) for k in range(len(cols))}
    for ln in LINES[hi + 2:]:
        c = cells(ln)
        if not c or c[0]:            # c[0] 有字＝已經到下面的統計列，名冊結束
            break
        for k, (j, _date, _lbl) in enumerate(cols):
            if j + 1 < len(c) and c[j] and c[j + 1]:
                cat = label2cat(c[j + 1])
                if cat in PAGE_CATS:
                    tally[k][cat] += 1
    ev2025 = [{"date": d, "label": lbl, "cats": dict(tally[k])}
              for k, (_j, d, lbl) in enumerate(cols)]

# ============ 2026：逐筆名單（活動｜Email｜報名｜報到｜所屬企業）============
mode = None
rows = []
for ln in LINES:
    c = cells(ln)
    if not c:
        continue
    if len(c) >= 4 and c[0] == "活動" and c[1] == "Email" and c[3] == "報到":
        # 兩張表：第一張是「首筆保留」去重表，第二張才是完整名單
        mode = "dedup" if (len(c) >= 6 and "重複" in c[5]) else "full"
        continue
    if mode != "full" or len(c) < 5 or "@" not in c[1]:
        continue
    email = c[1].lower().replace("\\", "")
    rows.append({"ev": c[0], "email": email, "dom": email.split("@")[-1],
                 "reg": c[2].strip(), "att": c[3].strip(),
                 "code": c[4].strip().upper()})

y2026 = defaultdict(lambda: {"att": 0, "uniq": set(), "reg": 0, "reg_uniq": set()})
grp_stat = defaultdict(lambda: {"rows": 0, "att": 0, "seen": set()})
ev_att = defaultdict(lambda: defaultdict(int))     # {場次: {group: 報到人次}}
exceptions = []          # 歸戶待確認
seen_exc = set()

for r in rows:
    g = group_of(r["dom"])
    cat = cat_of(r["dom"])
    fam = CODE_FAMILY.get(r["code"])
    if cat:
        grp_stat[g]["rows"] += 1
        grp_stat[g]["seen"].add(r["dom"])
        y2026[cat]["reg"] += 1
        y2026[cat]["reg_uniq"].add(r["email"])
        if r["att"] == "1":
            grp_stat[g]["att"] += 1
            y2026[cat]["att"] += 1
            y2026[cat]["uniq"].add(r["email"])
            if cat in PAGE_CATS:                    # 各場明細只列本頁三家
                ev_att[r["ev"]][g] += 1
        # 網域歸戶 vs 試算表「所屬企業」欄 打架（已定案的群組不再詢問）
        if fam and cat not in fam and not GROUP_BY_KEY[g].get("settled"):
            k = ("conflict", r["email"], r["code"])
            if k not in seen_exc:
                seen_exc.add(k)
                exceptions.append({"kind": "conflict", "email": mask(r["email"]),
                                   "dom": r["dom"], "ours": cat, "sheet": r["code"]})
    elif fam:
        # 私人信箱等：試算表認得、我們的網域表認不得 → 這頁會漏算
        k = ("unmapped", r["email"], r["code"])
        if k not in seen_exc:
            seen_exc.add(k)
            exceptions.append({"kind": "unmapped", "email": mask(r["email"]),
                               "dom": r["dom"], "ours": None, "sheet": r["code"]})

out = {
    "ucg_subs": UCG_SUBS,
    "page_cats": PAGE_CATS,
    "y2025": {c: dict(y2025[c]) for c in PAGE_CATS + OTHER_CATS},
    "y2026": {c: {"att": y2026[c]["att"], "att_uniq": len(y2026[c]["uniq"]),
                  "reg": y2026[c]["reg"], "reg_uniq": len(y2026[c]["reg_uniq"])}
              for c in PAGE_CATS + OTHER_CATS},
    # 歸戶對照：一個名字一列，變體已合併
    "groups": [{"key": g["key"], "cat": g["cat"], "note": g["note"],
                "confirmed": g["conf"],
                "seen": sorted(grp_stat[g["key"]]["seen"]),
                "rows": grp_stat[g["key"]]["rows"], "att": grp_stat[g["key"]]["att"]}
               for g in GROUPS if g["cat"] in PAGE_CATS],
    # 各場報到：與總表同源，讓明細加總 = 總表
    "ev_att": {ev: dict(d) for ev, d in ev_att.items()},
    "ev2025": ev2025,
    "exceptions": [e for e in exceptions
                   if (e["ours"] in PAGE_CATS) or (e["sheet"] in ("UCG", "HTM", "PILOT"))],
    "held": HELD, "future": FUTURE,
}
json.dump(out, open(os.path.join(HERE, "part_summary.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# ---- 對帳輸出 ----
print("=== 2025 全年報到（含 2026/1/16 場）===")
for c in PAGE_CATS:
    print("  %-14s 人次%4d  人數%4d" % (c, y2025[c]["visits"], y2025[c]["people"]))
print("  %-14s 人次%4d  人數%4d" % ("本頁合計",
      sum(y2025[c]["visits"] for c in PAGE_CATS), sum(y2025[c]["people"] for c in PAGE_CATS)))
print("\n=== 2026 報到（截至 7/17 已辦）===")
for c in PAGE_CATS:
    print("  %-14s 人次%4d  人數%4d   (報名人次%4d 報名人數%4d)"
          % (c, y2026[c]["att"], len(y2026[c]["uniq"]), y2026[c]["reg"], len(y2026[c]["reg_uniq"])))
tot_att = sum(y2026[c]["att"] for c in PAGE_CATS)
print("  %-14s 人次%4d  人數%4d" % ("本頁合計", tot_att,
      sum(len(y2026[c]["uniq"]) for c in PAGE_CATS)))
print("\n=== 各場報到（本頁三家；合計應等於上面的人次 %d）===" % tot_att)
chk = 0
for ev in HELD + FUTURE:
    n = sum(ev_att.get(ev, {}).values())
    chk += n
    print("  %-10s %3d" % (ev, n))
print("  各場加總 %d  →  %s" % (chk, "✅ 對得起來" if chk == tot_att else "❌ 對不起來"))
v25 = sum(y2025[c]["visits"] for c in PAGE_CATS)
print("\n=== 2025 各場報到（本頁三家；合計應等於 2025 人次 %d，1/10 那場不在名冊矩陣裡）===" % v25)
c25 = 0
for e in ev2025:
    n = sum(e["cats"].values())
    c25 += n
    print("  %-12s %-16s %3d" % (e["date"], e["label"], n))
print("  各場加總 %d  →  %s" % (c25, "✅ 對得起來" if c25 == v25 else "❌ 對不起來"))
print("\n=== 歸戶待確認 ===")
for e in out["exceptions"]:
    print("  [%s] %-34s 我們判%s / 試算表標%s" % (e["kind"], e["email"], e["ours"], e["sheet"]))
print("\n已寫出 part_summary.json")
