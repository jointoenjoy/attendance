# -*- coding: utf-8 -*-
"""併 Wix（正取／候補／請假）+ Google 現場報到表（報到）-> pipeline/part_events.json
只留本頁三家：UCG（拆子公司）、先勢集團、台北博報堂 HTM。其餘集團公司與外部人員一律排除。

- 報到數改抓 part_summary.json 的 ev_att，與總表同源，各場加總 = 總表人次。
- 網域一律合併到 subsidiary_map.GROUPS 的名字（手 key 的 .com.tw／拼字變體不再各自成列）。
- 輸出只有網域名字，不含帳號或姓名。
"""
import json, os, re
from collections import defaultdict

from subsidiary_map import GROUP_BY_KEY, PAGE_CATS, group_of, cat_of

HERE = os.path.dirname(os.path.abspath(__file__))
wix = json.load(open(os.path.join(HERE, "wix_states.json"), encoding="utf-8"))
SUM = json.load(open(os.path.join(HERE, "part_summary.json"), encoding="utf-8"))
EV_ATT = SUM["ev_att"]

SHEET_EV = {"2026-03-20": "0320", "2026-03-27": "0327", "2026-04-17": "0417",
            "2026-05-22": "0522", "2026-07-17": "0717", "2026-07-30": "0730"}
EXCLUDE_DATES = {"2026-06-04", "2026-06-05"}      # 小滿茶席（延後／測試，1 人）

# 2025 名冊矩陣的日期 -> Wix 場次日期（試算表把聖誕場記成 12/21，Wix 是 12/19）
SHEET2WIX = {"2025-12-21": "2025-12-19"}


def match_2025(w):
    """把 Wix 的 2025 場次對到名冊矩陣的那一欄。"""
    for e in SUM.get("ev2025", []):
        if SHEET2WIX.get(e["date"], e["date"]) != w["date"]:
            continue
        # 同一天兩場（11/21 上午／下午）再用時段字樣分辨
        for slot in ("上午", "下午"):
            if slot in e["label"]:
                if slot in w["title"]:
                    return e
                break
        else:
            return e
    return None


def sheet_ev(date, title):
    if date in SHEET_EV:
        return SHEET_EV[date]
    if date == "2026-07-31":
        return "0731聲波" if "聲波" in title else "0731苔球"
    return None


def clean_title(t):
    return re.sub(r"^\s*\d{1,2}/\d{1,2}\s*[（(]?[一二三四五六日]?[)）]?\s*", "", t).strip()


out_events = []
dropped = defaultdict(int)

# 2025 名冊一欄只能給一個 Wix 場次。Wix 偶爾同一天有重複場（例：6/13 場次一是空的），
# 這時把報到給報名數較多的那一場，另一場算 0，避免重複計算。
WIX25 = [w for w in wix if w["guests"] and w["date"] not in EXCLUDE_DATES
         and w["date"] < "2026-02-01"]
claim = {}
for e in SUM.get("ev2025", []):
    cand = [w for w in WIX25 if match_2025(w) is e]
    if cand:
        best = max(cand, key=lambda w: sum(d["att"] + d["wait"] + d["leave"]
                                           for d in w["domains"]))
        claim[id(best)] = e["cats"]

for w in wix:
    if w["guests"] == 0 or w["date"] in EXCLUDE_DATES:
        continue
    is25 = w["date"] < "2026-02-01"        # 1/16 那場歸 2025
    if is25:
        # 2025 的報到只有「公司」層級（現場名冊沒有 email）→ 明細列以公司為單位
        att = claim.get(id(w), {})
        keyfn, catfn = cat_of, (lambda x: x)
    else:
        ev = sheet_ev(w["date"], w["title"])
        att = EV_ATT.get(ev, {}) if ev else {}
        keyfn, catfn = group_of, (lambda k: GROUP_BY_KEY[k]["cat"])

    rmap = defaultdict(lambda: {"y": 0, "w": 0, "l": 0, "c": 0})
    for dd in w["domains"]:
        cat = cat_of(dd["d"])
        if cat not in PAGE_CATS:
            dropped[dd["d"]] += dd["att"] + dd["wait"] + dd["leave"]
            continue
        k = keyfn(dd["d"])
        rmap[k]["y"] += dd["att"]
        rmap[k]["w"] += dd["wait"]
        rmap[k]["l"] += dd["leave"]
    for k, c in att.items():
        rmap[k]["c"] += c

    rows = [{"d": k, "cat": catfn(k), **v} for k, v in rmap.items()]
    if not rows:
        continue
    rows.sort(key=lambda x: (-(x["y"] + x["w"] + x["l"]), -x["c"], x["d"]))
    tot = {k: sum(x[k] for x in rows) for k in ("y", "w", "l", "c")}
    if not any(tot.values()):        # 本頁三家完全沒人的場次（含 Wix 的空重複場）不列
        continue
    out_events.append({"date": w["date"], "year": w["year"], "title": clean_title(w["title"]),
                       "has_checkin": bool(att) or (not is25 and ev is not None),
                       "rowkind": "cat" if is25 else "domain",
                       "totals": tot, "domains": rows})

out_events.sort(key=lambda e: e["date"], reverse=True)
json.dump(out_events, open(os.path.join(HERE, "part_events.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

print("輸出場次：", len(out_events))
print("\n=== 被排除的網域（非本頁三家；請確認沒漏掉 UCG／先勢／HTM 的公司）===")
for dom, n in sorted(dropped.items(), key=lambda x: -x[1]):
    print("  %5d  %s" % (n, dom))
print("\n日期        正取 候補 請假 報到  活動")
for e in out_events:
    t = e["totals"]
    print("%-10s %4d %4d %4d %4s  %s" % (e["date"], t["y"], t["w"], t["l"],
                                         t["c"] if e["has_checkin"] else "—", e["title"][:22]))
for lab, pick, want in (
        ("2026", lambda e: e["date"] >= "2026-02-01", sum(sum(v.values()) for v in EV_ATT.values())),
        ("2025", lambda e: e["date"] < "2026-02-01",
         sum(sum(x["cats"].values()) for x in SUM.get("ev2025", [])))):
    got = sum(e["totals"]["c"] for e in out_events if pick(e))
    print("\n%s 報到加總 %d  /  總表 %d  →  %s"
          % (lab, got, want, "✅ 對得起來" if got == want else "❌ 對不起來"))
print("已寫出 part_events.json")
