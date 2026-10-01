# -*- coding: utf-8 -*-
"""用最新 Wix 名單重算 /all 頁的 2026 數字，直接改寫 site/all/index.html 裡的資料區塊：
DATA_2026（各企業帳號人數／人次）、DATA_2026_VER、PEOPLE_2026（逐人去重表）、EVENT_AUDIT["2026"]，
以及「數據說明」裡跟場次數有關的幾句話。

輸出到頁面的只有帳號（下拉選項或 @網域）與人數，沒有姓名、沒有完整信箱。
"""
import json, os, re, zlib
from collections import defaultdict, Counter
from wix2026 import load_events, year_events, today

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(os.path.dirname(HERE), "site", "all", "index.html")


def md(d):
    return "%d/%d" % (int(d[5:7]), int(d[8:10]))


def acct(g):
    """有選「所屬企業/集團」就用選項當帳號；沒選（例如候補不會被問）就用 @網域。"""
    return g["company"] or "@" + g["email"].split("@")[-1]


held = year_events(include_future=False)
acc = defaultdict(lambda: {"h": set(), "v": 0})
ppl = defaultdict(set)
wait_rows = wait_blank = 0
for e in held:
    for g in e["guests"]:
        if "@" not in g["email"]:
            continue
        a = acct(g)
        acc[a]["h"].add(g["email"]); acc[a]["v"] += 1
        ppl[g["email"]].add(a)
        if g["status"] == "候補":
            wait_rows += 1
            wait_blank += not g["company"]

data = sorted(({"c": k, "h": len(v["h"]), "v": v["v"]} for k, v in acc.items()),
              key=lambda r: (-r["h"], -r["v"], r["c"]))
people = Counter(tuple(sorted(s, key=lambda x: (not x.startswith("@"), x))) for s in ppl.values())
people = sorted(people.items(), key=lambda kv: (-kv[1], kv[0]))
multi = sum(n for k, n in people if len(k) > 1)
no_field = sum(1 for e in held if not e["has_company_field"])

# 資料稽核：2026 全部場次（含 1/16、茶席、已取消），逐場 × 網域
evs, grand_v, grand_h = [], Counter(), defaultdict(set)
for e in load_events():
    dv, dh = Counter(), defaultdict(set)
    for g in e["guests"]:
        if "@" not in g["email"]:
            continue
        d = "@" + g["email"].split("@")[-1]
        dv[d] += 1; dh[d].add(g["email"]); grand_v[d] += 1; grand_h[d].add(g["email"])
    doms = sorted(([d, dv[d], len(dh[d])] for d in dv), key=lambda x: (-x[1], x[0]))
    status = e["status"] if e["status"] in ("ENDED", "CANCELED") else \
        ("UPCOMING" if e["date"] > today() else "ENDED")
    evs.append([e["date"], e["title"], status, sum(dv.values()),
                len({g["email"] for g in e["guests"] if "@" in g["email"]}), doms])
grand = sorted(([d, grand_v[d], len(grand_h[d])] for d in grand_v), key=lambda x: (-x[2], -x[1], x[0]))
audit26 = {"count": len(evs), "events": evs, "grand": grand}

blob = json.dumps([data, people], ensure_ascii=False, sort_keys=True)
ver = zlib.crc32(blob.encode("utf-8")) % 900000 + 100000      # 資料一變版本號就變，雲端舊陣列自動被換掉

s = open(PAGE, encoding="utf-8").read()
orig = s


def sub(pat, rep, flags=re.S):
    global s
    s2, n = re.subn(pat, lambda m: rep, s, count=1, flags=flags)
    if n != 1:
        raise SystemExit("❌ 找不到要替換的區塊：" + pat[:60])
    s = s2


rows = ",".join('{c:%s,h:%d,v:%d}' % (json.dumps(r["c"], ensure_ascii=False), r["h"], r["v"]) for r in data)
sub(r"const DATA_2026 = \[.*?\n\];", "const DATA_2026 = [\n " + rows + "\n];")
sub(r"const DATA_2026_VER = \d+;", "const DATA_2026_VER = %d;" % ver)
prow = ",\n ".join("[%s,%d]" % (json.dumps(list(k), ensure_ascii=False), n) for k, n in people)
sub(r"const PEOPLE_2026 = \[.*?\n\];", "const PEOPLE_2026 = [\n " + prow + "\n];")

m = re.search(r"const EVENT_AUDIT = (\{.*?\});\n", s)
audit = json.loads(m.group(1))
audit["2026"] = audit26
s = s[:m.start(1)] + json.dumps(audit, ensure_ascii=False, separators=(",", ":")) + s[m.end(1):]

span = "%s～%s" % (md(held[0]["date"]), md(held[-1]["date"]))
sub(r"// 2026[ （][^\n]*— 由[^\n]*名單逐筆產出[^\n]*",
    "// 2026（%s 已舉辦 %d 場）— 由 Wix 報名名單逐筆產出（build_all_2026.py 每週自動更新）。" % (span, len(held)))
sub(r"相加就會把一個人算成兩個（2026[^）]*）。", "相加就會把一個人算成兩個（2026 有 %d 人是這種情形）。" % multi)
sub(r"Wix API 直接撈好、烤進頁面（[^）]*）", "Wix API 直接撈好、烤進頁面（2026 已舉辦 %d 場、每週三自動更新）" % len(held))
sub(r"<p><b>2026</b> 為<b>[^<]*</b>（與對外 /part 頁同一批場次，",
    "<p><b>2026</b> 為<b>%s 已舉辦的 %d 場</b>（與對外 /part 頁同一批場次，" % (span, len(held)))
sub(r"「所屬企業」（\d+ 筆候補有 \d+ 筆空白），\s*\n\s*[^\n]*",
    "「所屬企業」（%d 筆候補有 %d 筆空白），\n       %s" % (
        wait_rows, wait_blank,
        "另有 %d 場活動整場未收集此欄位。同一個人因此可能同時出現在「下拉帳號」與「網域帳號」兩個桶裡，" % no_field
        if no_field else "同一個人因此可能同時出現在「下拉帳號」與「網域帳號」兩個桶裡，"))
sub(r"相加會把一個人算成兩個（[^）]*）。本頁", "相加會把一個人算成兩個（2026 有 %d 人是這種情形）。本頁" % multi)

if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}", s) and \
        not re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}", orig):
    raise SystemExit("❌ 頁面出現完整 email，中止不寫檔")
open(PAGE, "w", encoding="utf-8").write(s)
# 下載區用的 2026 逐場網域檔（格式沿用舊版 event_domains.json）
ed = {"pulled_year": 2026, "event_count": len(evs), "events": [
    {"date": d, "title": t, "status": st, "total_visits": v, "total_people": u, "no_email": 0,
     "domains": [{"domain": x[0], "visits": x[1], "people": x[2]} for x in doms]}
    for d, t, st, v, u, doms in evs],
    "grand_domains": [{"domain": x[0], "visits": x[1], "people": x[2]} for x in grand]}
json.dump(ed, open(os.path.join(HERE, "event_domains.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print("2026 已舉辦 %d 場（%s）｜帳號 %d 個｜不重複 %d 人｜跨帳號 %d 人｜DATA_2026_VER=%d"
      % (len(held), span, len(data), len(ppl), multi, ver))
print("資料稽核 2026：%d 場、%d 種網域" % (audit26["count"], len(grand)))
