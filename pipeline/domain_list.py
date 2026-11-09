# -*- coding: utf-8 -*-
"""集團官方 email 網域清單（EIP 登入網域清單）——網域歸戶的最終依據。

來源：決策者 2026-11-09 提供的《公司網域清單.docx》，原檔存在 reference/公司網域清單.docx。
不含個資，可進 git。subsidiary_map.py 與 domain_verify.py 都要跟這份一致；有衝突以這份為準。

OFFICIAL：網域 → (集團代碼, 公司名稱)。集團代碼跟 Wix「所屬企業」下拉一致。
"""
OFFICIAL = {
    # 台北博報堂集團（HTM）
    "hakuhodotm.com.tw": ("HTM", "台北博報堂管理顧問"),
    "hakuhodoti.com.tw": ("HTM", "台北博報堂投資"),
    # 聯廣傳播集團（UCG）
    "ua.com.tw": ("UCG", "聯廣廣告"),
    "dvibemedia.com": ("UCG", "迪維數位智造"),
    "2008-media.com": ("UCG", "二零零八傳媒行銷"),
    "ace-taipei.com": ("UCG", "艾斯傳媒行銷"),
    "unismart.com.tw": ("UCG", "聯樂數位行銷"),
    "unisurf.com.tw": ("UCG", "聯眾廣告"),
    "unisincere.com.tw": ("UCG", "聯勤公關顧問"),
    # 先勢博報堂集團（Pilot）
    "pilotpr.com.tw": ("PILOT", "先勢公關顧問"),
    "pilotcomms.com.tw": ("PILOT", "先勢溝通行銷"),
    "cubicism.com": ("PILOT", "立方體數位管理顧問"),
    "charismomo.com": ("PILOT", "桃花娛樂國際整合行銷"),
    "planetpr.com.tw": ("PILOT", "天擎公關顧問"),
    "prestigepr.com.tw": ("PILOT", "先擎公關顧問"),
    "grandpr.com.tw": ("PILOT", "鈞勢國際公關顧問"),
    "unistyle.com.tw": ("PILOT", "聯太國際公關顧問"),
    "pilotgp.com": ("PILOT", "先勢行銷傳播集團"),
    "pilothakuhodo.com": ("PILOT", "先勢博報堂集團"),
    "newspie.com.tw": ("PILOT", "News Pie 新聞派"),
    # 米蘭數位傳播集團（MDCG）
    "mdcg.tw": ("MDCG", "米蘭營銷策劃"),
    "medialand.tw": ("MDCG", "米蘭營銷策劃"),
    "mxdigi.com": ("MDCG", "創意思境"),
    "meshplus.com.tw": ("MDCG", "洰和"),
    "jointoenjoy.com": ("MDCG", "練息場"),
    # 安益國際集團（INTERPLAN）
    "messetaoyuan.com": ("INTERPLAN", "桃園會展中心"),
    "intercon.com.tw": ("INTERPLAN", "茵康國際會議顧問"),
    "kecc.com.tw": ("INTERPLAN", "高雄展覽館"),
    "interplan.com.tw": ("INTERPLAN", "安益國際展覽"),
    # 光洋波斯特國際集團（KY-POST）
    "ky-post.com": ("KY-POST", "光洋波斯特國際展覽"),
}


def official_of(domain):
    """網域（含打錯字的變體，先經 domain_verify.ALIAS 轉正）→ (集團代碼, 公司名稱)；不在清單上回 None。"""
    from domain_verify import ALIAS
    d = (domain or "").strip().lower()
    return OFFICIAL.get(ALIAS.get(d, d))
