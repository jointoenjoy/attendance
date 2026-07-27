# -*- coding: utf-8 -*-
"""
把 /all 頁「原始數據」做成可下載的檔案，輸出到 site/all/data/。

為什麼安全：pipeline 產出的 JSON 全部已經去識別化——只留 email「@ 之後的網域」
與各種計數，沒有姓名、沒有完整信箱。含真名的原始匯出（pipeline/_private/）
不會、也不該被複製到這裡。這支腳本會在寫檔前逐一檢查，抓到疑似完整信箱就中止。

/all 整區已被 site/functions/_middleware.js 密碼保護，所以 /all/data/ 底下的檔案
也一起被擋，外面的人拿不到。

用法：
    python3 build_all_downloads.py
"""

import csv
import io
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "site", "all", "data")

TPE = timezone(timedelta(hours=8))

# 完整信箱長這樣：本地帳號 + @ + 網域。我們的資料只該有 "@網域" 或 "網域"，
# 所以 @ 前面只要黏著英數就是漏了個資 → 直接中止。
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")


def load(name):
    with io.open(os.path.join(HERE, name), encoding="utf-8") as f:
        return json.load(f)


def guard(text, label):
    """寫檔前的個資防呆：抓到完整信箱就整支中止，不留半成品。"""
    hit = EMAIL_RE.search(text)
    if hit:
        sys.exit(f"❌ 中止：{label} 疑似含完整信箱「{hit.group(0)}」，不可放上網頁。")


def write_json(name, obj, label):
    text = json.dumps(obj, ensure_ascii=False, indent=1)
    guard(text, name)
    with io.open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(text)
    return {"file": name, "label": label, "kind": "JSON", "bytes": len(text.encode("utf-8"))}


def write_csv(name, header, rows, label):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    w.writerows(rows)
    text = buf.getvalue()
    guard(text, name)
    with io.open(os.path.join(OUT, name), "w", encoding="utf-8-sig") as f:  # BOM 讓 Excel 不亂碼
        f.write(text)
    return {"file": name, "label": label, "kind": "CSV", "rows": len(rows),
            "bytes": len(text.encode("utf-8-sig"))}


def main():
    os.makedirs(OUT, exist_ok=True)

    ed25 = load("event_domains_2025.json")
    ed26 = load("event_domains.json")
    states = load("wix_states.json")
    merged = load("page_events.json")
    summary = load("attendance_data.json")

    groups = []

    # ── 一、Wix 報名（逐場 × email 網域）──────────────────────────
    wix_files = []
    for tag, src in (("2025", ed25), ("2026", ed26)):
        rows = []
        for e in src["events"]:
            for d in e["domains"]:
                rows.append([tag, e["date"], e["title"], e["status"],
                             d["domain"], d["visits"], d["people"]])
        wix_files.append(write_csv(
            f"wix-{tag}-報名逐場.csv",
            ["年度", "日期", "活動名稱", "場次狀態", "email網域", "報名人次", "報名人數"],
            rows, f"{tag} 每一場、每個 email 網域的報名人次與人數"))
        wix_files.append(write_json(
            f"wix-{tag}-報名逐場.json", src,
            f"{tag} 同上，JSON 原檔（另含全年網域總表 grand_domains）"))

    groups.append({
        "title": "Wix 報名原始數據",
        "note": "直接用 Wix Events API 逐場撈下來的報名紀錄，"
                "已把每個人的信箱切成「@ 之後的網域」再彙總。"
                "人次＝報名筆數，人數＝該網域不重複的報名者。"
                "場次狀態 ENDED＝已結束、UPCOMING＝尚未舉辦、CANCELED＝已取消。",
        "files": wix_files,
    })

    # ── 二、Wix 報名狀態（正取／候補／請假）──────────────────────
    st_rows = []
    for e in states:
        for d in e["domains"]:
            st_rows.append([e["year"], e["date"], e["title"], e["status"],
                            "@" + d["d"], d["att"], d["wait"], d["leave"]])
    groups.append({
        "title": "Wix 報名狀態（正取／候補／請假）",
        "note": "同一批 Wix 資料，但拆出每個人當初的報名狀態。"
                "正取＝取得名額（Wix 的 ATTENDING）、候補＝額滿排補（IN_WAITLIST）、"
                "請假＝報名後取消（NOT_ATTENDING）。這是「報名」不是「到場」。",
        "files": [
            write_csv("wix-報名狀態逐場.csv",
                      ["年度", "日期", "活動名稱", "場次狀態", "email網域", "正取", "候補", "請假"],
                      st_rows, "2025＋2026 每一場、每個網域的正取／候補／請假人數"),
            write_json("wix-報名狀態逐場.json", states, "同上，JSON 原檔（含每場總計 totals）"),
        ],
    })

    # ── 三、併檔後（報名 ＋ 現場報到）────────────────────────────
    mg_rows = []
    for e in merged:
        for d in e["domains"]:
            mg_rows.append([e["year"], e["date"], e["title"],
                            "有" if e.get("has_checkin") else "無",
                            "@" + d["d"], d.get("cat", ""),
                            d.get("y", 0), d.get("w", 0), d.get("l", 0), d.get("c", 0)])
    groups.append({
        "title": "併檔後：報名 ＋ 現場報到",
        "note": "把上面的 Wix 報名，跟 Google 現場報到表對起來之後的結果，"
                "也就是這一頁與 /part 真正拿來算數字的那一份。"
                "「報到」只有實際簽到才算；沒有報到表的場次（欄位『報到表＝無』）"
                "報到一律是 0，不代表沒人來。",
        "files": [
            write_csv("併檔-報名與報到逐場.csv",
                      ["年度", "日期", "活動名稱", "報到表", "email網域", "歸屬公司",
                       "正取", "候補", "請假", "報到"],
                      mg_rows, "每一場、每個網域的正取／候補／請假／報到，含歸屬公司"),
            write_json("併檔-報名與報到逐場.json", merged, "同上，JSON 原檔"),
            write_json("彙總-各公司兩年度.json", summary,
                       "各公司 2025／2026 的人次與人數彙總（這一頁表格的來源）"),
        ],
    })

    manifest = {
        "built": datetime.now(TPE).strftime("%Y-%m-%d %H:%M"),
        "groups": groups,
        "privacy": "以上檔案全部只含 email「@ 之後的網域」與計數，沒有姓名、沒有完整信箱。"
                   "含真名的原始匯出只留在本機，不進 git、也不會上傳。",
    }
    text = json.dumps(manifest, ensure_ascii=False, indent=1)
    guard(text, "manifest.json")
    with io.open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
        f.write(text)

    n = sum(len(g["files"]) for g in groups)
    total = sum(f["bytes"] for g in groups for f in g["files"])
    print(f"✅ 已輸出 {n} 個檔案（{total/1024:.0f} KB）到 site/all/data/")
    for g in groups:
        print(f"   ▸ {g['title']}")
        for f in g["files"]:
            print(f"      - {f['file']}  {f['bytes']/1024:.0f} KB")
    print("✅ 個資防呆通過：沒有任何檔案含完整信箱")


if __name__ == "__main__":
    main()
