# -*- coding: utf-8 -*-
"""各 email 網域的公司查證（2026-11-05 網路查證，給集團人資確認用；不含個資，可進 git）。

VERIFY：網域 → (公司全名, 歸屬代碼, 把握程度, 來源, 備註)。代碼空字串＝查無。
ALIAS：報名時打錯字／寫法變體的網域 → 正確網域（照正確網域那一列查證）。
"""
VERIFY = {
    "ua.com.tw": ("聯廣廣告 United Advertising", "UCG", "高", "https://www.ucgroup.com.tw/", "聯廣集團官網子公司列表直接連到此網域"),
    "unismart.com.tw": ("聯眾廣告", "UCG", "高", "https://www.ucgroup.com.tw/", "聯廣集團官網子公司列表直接連到此網域"),
    "unisurf.com.tw": ("聯樂數位行銷 UNISURF", "UCG", "高", "https://www.ucgroup.com.tw/", "集團官網連的是 unisurf.tw，名稱一致"),
    "2008-media.com": ("2008傳媒行銷 2008 Media", "UCG", "高", "https://www.ucgroup.com.tw/", "聯廣集團官網子公司列表直接連到此網域"),
    "unisincere.com.tw": ("聯勤公關", "UCG", "高", "https://www.ucgroup.com.tw/", "聯廣集團官網子公司列表直接連到此網域"),
    "ace-taipei.com": ("艾斯傳媒行銷 ACE Communications", "UCG", "中", "https://ace-taipei.com", "官網說原屬聯廣，職缺掛在聯廣徵才頁"),
    "medialand.tw": ("米蘭營銷策劃 Medialand", "MDCG", "高", "https://www.medialand.tw/", "MDCG＝米蘭數位傳播集團"),
    "meshplus.com.tw": ("洰和 MESh+", "MDCG", "高", "https://www.meshplus.com.tw", "官網自稱 MDCG 集團旗下"),
    "mxdigi.com": ("創意思境 MX Digi", "MDCG", "中", "https://www.medialand.tw/", "米蘭官網連的是 mx-digi.com（有連字號）"),
    "mdcg.tw": ("米蘭數位傳播集團", "MDCG", "中", "https://www.yourator.co/companies/medialand", "網站連不上，網域與集團縮寫一致"),
    "hakuhodotm.com.tw": ("（網路查無）", "HTM", "低", "https://www.hakuhodo.com.tw/", "網路查無；但報名者本人幾乎都選台北博報堂 HTM"),
    "dvibemedia.com": ("迪維數位智造 d.vibe", "HTM", "低", "https://www.dvibemedia.com", "只有官網頁尾連到台灣博報堂；對照表原歸聯廣，待確認"),
    "pilotpr.com.tw": ("先勢公關 Pilot PR", "PILOT", "中", "https://pilothakuhodo.com/", "網站連不上，靠集團子公司英文名比對"),
    "grandpr.com.tw": ("天擎公關 Grand PR", "PILOT", "中", "https://pilothakuhodo.com/", "網站連不上，靠集團子公司英文名比對"),
    "planetpr.com.tw": ("先擎公關 Planet PR", "PILOT", "中", "https://pilothakuhodo.com/", "網站連不上，靠集團子公司英文名比對"),
    "prestigepr.com.tw": ("鈞勢國際公關 Prestige PR", "PILOT", "中", "https://pilothakuhodo.com/", "網站連不上，靠集團子公司英文名比對"),
    "unistyle.com.tw": ("聯太國際公關 Uni-Style PR", "PILOT", "高", "https://pilothakuhodo.com/", "決策者 2026-11-05 查證：屬先勢集團"),
    "charismomo.com": ("（網路查無）", "", "低", "", "網路查無，待集團確認"),
    "ky-post.com": ("光洋波斯特 KY-Post Design", "KY-POST", "高", "https://www.ky-post.com", "官網寫明加入博報堂"),
    "interplan.com.tw": ("安益國際 Interplan", "INTERPLAN", "高", "https://www.hakuhodo-global.com/network/interplan-group.html", "網域已轉到 interplan.group"),
    "leader-ac.com.tw": ("利達空調", "", "中", "https://www.leader-ac.com.tw", "空調公司，非博報堂集團；報名者自選米蘭 MDCG"),
}
ALIAS = {
    "mxdogi.com": "mxdigi.com", "planetpe.com.tw": "planetpr.com.tw", "hakuhodoti.com.tw": "hakuhodotm.com.tw",
    "ace.taipei.com": "ace-taipei.com", "unisurf.com": "unisurf.com.tw", "ua.com": "ua.com.tw",
    "medialnad.tw": "medialand.tw", "medialand.com": "medialand.tw", "mediand.tw": "medialand.tw",
}
