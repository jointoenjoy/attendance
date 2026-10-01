# -*- coding: utf-8 -*-
"""2026 場次的共用規則（parse_part / merge_part_events / build_all_2026 / build_2026 共用）。

資料來源：pull_2026_guests.py 拉下來的 _private/wix_2026_guests.json（含姓名 email，不進 git）。
報到＝Wix 後台的「報到勾選」。7/31 以前的場次已跟 Google 現場報到表逐場對過，人數完全一致。
"""
import json, os
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
GUESTS = os.path.join(HERE, "_private", "wix_2026_guests.json")

YEAR_START = "2026-02-01"                      # 1/16 那場依慣例歸 2025
EXCLUDE_DATES = {"2026-06-04", "2026-06-05"}   # 小滿茶席（延後／測試，1 人）
HAKUHODO = ["MDCG", "UCG", "HTM", "PILOT", "KY-POST", "INTERPLAN"]   # Wix 下拉＝博報堂集團六家
REG = {"正取": "Yes", "候補": "Waiting", "請假": "No"}


def today():
    return (datetime.now(timezone.utc) + timedelta(hours=8)).strftime("%Y-%m-%d")


def ev_key(date, title):
    """場次代碼：日期＋原始標題（同一天兩場也分得開）。"""
    return date + "|" + title.strip()


def load_events():
    return json.load(open(GUESTS, encoding="utf-8"))


def year_events(include_future=True):
    """2026 年度（2/1 起）的有效場次，排除茶席測試場與已取消場。"""
    t = today()
    out = []
    for e in load_events():
        if e["date"] < YEAR_START or e["date"] in EXCLUDE_DATES or e["status"] == "CANCELED":
            continue
        if not include_future and e["date"] > t:
            continue
        out.append(e)
    return out


def has_checkin(e):
    """這場有沒有在 Wix 做報到。已辦但一個勾都沒有＝現場只用紙本簽到、還沒回填 Wix。"""
    return any(g["wix_checked_in"] for g in e["guests"])
