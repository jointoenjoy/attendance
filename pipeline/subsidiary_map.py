# -*- coding: utf-8 -*-
"""子公司歸戶的單一真相：email 網域 -> 子公司、2025 名冊 label -> 子公司。

/part 這頁只對外呈現三家：UCG（拆到子公司）、先勢集團、台北博報堂 HTM。
米蘭 MDCG／光洋波斯特／安益 仍會被解析（用於稽核與「非本頁」統計），但不上這頁。

【網域合併原則】（大寶 2026-07-27 指示）
現場是手 key 的，`.com.tw` / `.com` 常打錯、字母也會拼錯。
所以歸戶以「@ 後面的名字」為單位（GROUPS 的 key），
同一個名字的所有寫法變體一律先歸戶、再合併成一列呈現。
"""

# ---- 本頁要呈現的子公司順序 ----
UCG_SUBS = ["聯廣", "聯太", "聯樂", "艾斯", "聯眾", "2008傳媒", "迪維", "聯勤"]
PAGE_CATS = UCG_SUBS + ["先勢集團", "台北博報堂 HTM"]
OTHER_CATS = ["米蘭 MDCG", "光洋波斯特", "安益"]   # 解析得到但本頁不顯示

# ---- 網域群組 -> 子公司 ----
# key   : 合併後對外顯示的名字（@ 後面那段的主體）
# cat   : 歸到哪家
# note  : 歸戶區的說明
# conf  : True=已查證，False=待對方確認
# vars  : 實際在資料裡出現過的所有寫法（含打錯的變體），一律併進同一列
GROUPS = [
    # ── UCG 聯廣傳播集團 ──
    dict(key="ua",          cat="聯廣",        conf=True,
         note="UNITED ADVERTISING 聯廣廣告",
         vars=["ua.com.tw", "ua.com"]),
    dict(key="unistyle",    cat="聯太",        conf=True, settled=True,
         note="聯太（聯廣集團旗下）；試算表「所屬企業」欄標為 PILOT，經確認應歸聯太",
         vars=["unistyle.com.tw", "unistyle.com"]),
    dict(key="unisurf",     cat="聯樂",        conf=True,
         note="UNISURF 聯樂數位行銷",
         vars=["unisurf.com.tw", "unisurf.com"]),
    dict(key="ace-taipei",  cat="艾斯",        conf=True,
         note="艾斯",
         vars=["ace-taipei.com", "ace.taipei.com", "ace-taipei.com.tw"]),
    dict(key="unismart",    cat="聯眾",        conf=True,
         note="Uni-Smart 聯眾廣告／UPOINT 聯眾觀點",
         vars=["unismart.com.tw", "unismart.com"]),
    dict(key="2008-media",  cat="2008傳媒",    conf=True,
         note="2008 傳媒行銷",
         vars=["2008-media.com", "2008-media.com.tw"]),
    dict(key="dvibemedia",  cat="迪維",        conf=True,
         note="dvibe 迪維數位智造",
         vars=["dvibemedia.com", "divibemedia.com", "dvibemedia.com.tw"]),
    dict(key="unisincere",  cat="聯勤",        conf=True,
         note="UPR 聯勤公關",
         vars=["unisincere.com.tw", "unisincere.com"]),
    # ── 先勢集團（不拆）──
    dict(key="pilotpr",     cat="先勢集團",    conf=True,
         note="先勢公關",
         vars=["pilotpr.com.tw", "pilotpr.com"]),
    dict(key="grandpr",     cat="先勢集團",    conf=True,
         note="精采公關",
         vars=["grandpr.com.tw", "grandpr.com"]),
    dict(key="prestigepr",  cat="先勢集團",    conf=True,
         note="楷模公關",
         vars=["prestigepr.com.tw", "prestigepr.com"]),
    dict(key="planetpr",    cat="先勢集團",    conf=True,
         note="頤德／星團公關（planetpe 為打錯的變體，已併入）",
         vars=["planetpr.com.tw", "planetpe.com.tw", "planetpr.com"]),
    dict(key="charismomo",  cat="先勢集團",    conf=False,
         note="試算表「所屬企業」欄標 PILOT，但這不是先勢既有網域，請確認是哪家",
         vars=["charismomo.com", "charismomo.com.tw"]),
    # ── 台北博報堂 ──
    dict(key="hakuhodo",    cat="台北博報堂 HTM", conf=True,
         note="台北博報堂（hakuhodotm 與 hakuhodoti 兩組寫法已合併）",
         vars=["hakuhodotm.com.tw", "hakuhodoti.com.tw",
               "hakuhodotm.com", "hakuhodoti.com"]),
    # ── 以下不在本頁呈現，但要正確排除、不要誤混進三家 ──
    dict(key="medialand",   cat="米蘭 MDCG",   conf=True, note="米蘭數位行銷",
         vars=["medialand.tw", "medialnad.tw", "mediand.tw", "medialand.com",
               "medialand.com.tw"]),
    dict(key="mdcg",        cat="米蘭 MDCG",   conf=True, note="MDCG 總部",
         vars=["mdcg.tw", "mdcg.com.tw"]),
    dict(key="mxdigi",      cat="米蘭 MDCG",   conf=True, note="洰和 MX Digital",
         vars=["mxdigi.com", "mxdogi.com", "mxdigi.com.tw"]),
    dict(key="meshplus",    cat="米蘭 MDCG",   conf=True, note="創意思境",
         vars=["meshplus.com.tw", "meshplus.con.tw", "meshplus.com"]),
    dict(key="ky-post",     cat="光洋波斯特",  conf=True,
         note="光洋波斯特（UCG 會展事業，集團另計為 KY-POST）",
         vars=["ky-post.com", "ky-post.com.tw", "kypost.com"]),
    dict(key="interplan",   cat="安益",        conf=True, note="安益國際展覽",
         vars=["interplan.com.tw", "interplan.com"]),
]

# domain -> group key / 子公司 / 說明
DOMAIN_GROUP = {v: g["key"] for g in GROUPS for v in g["vars"]}
DOMAIN_CAT = {v: g["cat"] for g in GROUPS for v in g["vars"]}
GROUP_BY_KEY = {g["key"]: g for g in GROUPS}


def group_of(domain):
    """email 網域 -> 合併後的群組 key（認不得就回 None）。"""
    return DOMAIN_GROUP.get((domain or "").strip().lower())


def cat_of(domain):
    """email 網域 -> 子公司（認不得就回 None）。"""
    return DOMAIN_CAT.get((domain or "").strip().lower())


def label2cat(company):
    """2025 現場報到名冊的『公司』欄 label -> 子公司。"""
    c = (company or "").strip()
    if c.startswith("UCG"):
        inner = c[c.find("(") + 1:c.find(")")] if "(" in c else ""
        if inner in ("2008傳媒", "2008"):
            return "2008傳媒"
        if inner in UCG_SUBS:
            return inner
        return "聯廣"          # 其餘沒標子公司的 UCG → 併聯廣
    if c.startswith("MDCG"):
        return "米蘭 MDCG"
    if c.startswith("HTM"):
        return "台北博報堂 HTM"
    if c.startswith(("先勢", "天擎", "鈞勢")):
        return "先勢集團"
    if c.startswith("光洋"):
        return "光洋波斯特"
    if c.startswith("安益"):
        return "安益"
    return None                # 練息場／民眾／外部廠商
