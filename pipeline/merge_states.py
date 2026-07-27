# -*- coding: utf-8 -*-
# 併 Wix(正取/候補/請假) + Google Sheet(報到) -> page_events.json
# 只集團成員網域；印出被排除(非集團)網域讓人工核對，避免漏算。
import json, os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = os.path.dirname(HERE)
wix = json.load(open(os.path.join(HERE, "wix_states.json"), encoding="utf-8"))
sheet = json.load(open(os.path.join(SCRATCH, "attendance_data.json"), encoding="utf-8"))

# 集團網域 -> 子公司（與 parse_attendance.py 一致）
DOMAIN_CAT = {
    "ua.com.tw": "聯廣 UCG", "ua.com": "聯廣 UCG",
    "unismart.com.tw": "聯廣 UCG", "unisurf.com.tw": "聯廣 UCG", "unisurf.com": "聯廣 UCG",
    "unisincere.com.tw": "聯廣 UCG", "unistyle.com.tw": "聯廣 UCG", "unisincere.com": "聯廣 UCG",
    "ace-taipei.com": "艾斯", "ace.taipei.com": "艾斯",
    "2008-media.com": "2008傳媒", "dvibemedia.com": "迪維", "divibemedia.com": "迪維",
    "medialand.tw": "米蘭 MDCG", "medialnad.tw": "米蘭 MDCG", "mediand.tw": "米蘭 MDCG",
    "medialand.com": "米蘭 MDCG",
    "mdcg.tw": "米蘭 MDCG", "mxdigi.com": "米蘭 MDCG", "mxdogi.com": "米蘭 MDCG",
    "meshplus.com.tw": "米蘭 MDCG", "meshplus.con.tw": "米蘭 MDCG",
    "pilotpr.com.tw": "先勢集團", "grandpr.com.tw": "先勢集團", "prestigepr.com.tw": "先勢集團",
    "planetpr.com.tw": "先勢集團", "planetpe.com.tw": "先勢集團",
    "ky-post.com": "光洋波斯特", "interplan.com.tw": "安益",
    "hakuhodotm.com.tw": "台北博報堂 HTM", "hakuhodoti.com.tw": "台北博報堂 HTM",
}

# 2026 場：Wix date(+title) -> sheet ev code；報到(att) 由 sheet 逐網域併入
def sheet_ev(date, title):
    m = {"2026-03-20": "0320", "2026-03-27": "0327", "2026-04-17": "0417",
         "2026-05-22": "0522", "2026-07-17": "0717", "2026-07-30": "0730"}
    if date in m:
        return m[date]
    if date == "2026-07-31":
        return "0731聲波" if "聲波" in title else "0731苔球"
    return None

sheet_by_ev = {e["ev"]: e for e in sheet["events2026"]}

def clean_title(t):
    # 去掉開頭日期/星期，保留活動名
    import re
    return re.sub(r"^\s*\d{1,2}/\d{1,2}\s*[（(]?[一二三四五六日]?[)）]?\s*", "", t).strip()

EXCLUDE = {("2026-06-04", None), ("2026-06-05", None)}  # 小滿茶席（延後/測試，1人）

excluded_domains = defaultdict(int)
out_events = []
for w in wix:
    if w["guests"] == 0:
        continue
    if any(w["date"] == d for d, _ in EXCLUDE):
        continue
    ev = sheet_ev(w["date"], w["title"])
    sh = sheet_by_ev.get(ev)
    sh_att = {d["d"]: d["att"] for d in sh["domains"]} if sh else {}

    dmap = defaultdict(lambda: {"y": 0, "w": 0, "l": 0, "c": 0})
    for dd in w["domains"]:
        dom = dd["d"]
        cat = DOMAIN_CAT.get(dom)
        if not cat:
            excluded_domains[dom] += dd["att"] + dd["wait"] + dd["leave"]
            continue
        dmap[dom]["y"] += dd["att"]      # 正取
        dmap[dom]["w"] += dd["wait"]     # 候補
        dmap[dom]["l"] += dd["leave"]    # 請假
    # 併入 sheet 報到
    for dom, c in sh_att.items():
        if DOMAIN_CAT.get(dom):
            dmap[dom]["c"] += c
    # 若 sheet 有網域但 Wix 沒有（少見），也保留
    domains = [{"d": k, "cat": DOMAIN_CAT[k], **v} for k, v in dmap.items()]
    domains.sort(key=lambda x: (-(x["y"] + x["w"] + x["l"]), -x["c"], x["d"]))
    tot = {"y": sum(x["y"] for x in domains), "w": sum(x["w"] for x in domains),
           "l": sum(x["l"] for x in domains), "c": sum(x["c"] for x in domains)}
    done_att = (ev is not None)  # 2026 已辦且 sheet 有報到
    out_events.append({
        "date": w["date"], "year": w["year"], "title": clean_title(w["title"]),
        "has_checkin": bool(sh),  # 是否有 sheet 報到（2026 已辦場）
        "totals": tot, "domains": domains,
    })

out_events.sort(key=lambda e: e["date"], reverse=True)  # 新到舊
json.dump(out_events, open(os.path.join(SCRATCH, "page_events.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

print("輸出場次：", len(out_events))
print("\n=== 被排除的『非集團』網域（人次合計；請人工確認沒有漏掉集團公司）===")
for dom, n in sorted(excluded_domains.items(), key=lambda x: -x[1]):
    print("  %5d  %s" % (n, dom))
print("\n=== 各場（集團）正取/候補/請假/報到 ===")
print("日期        正取 候補 請假 報到  活動")
for e in out_events:
    t = e["totals"]
    ci = t["c"] if e["has_checkin"] else "—"
    print("%-10s %4d %4d %4d %4s  %s" % (e["date"], t["y"], t["w"], t["l"], str(ci), e["title"][:20]))
print("\n已寫出 page_events.json")
