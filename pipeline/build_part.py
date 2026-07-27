# -*- coding: utf-8 -*-
"""產生 site/part/index.html：
   UCG（拆七家子公司）＋先勢集團＋台北博報堂 HTM 的報到總表、各場明細、Email 歸戶區。
   這頁是要獨立傳給外部的，所以沒有連到 /all 的分頁按鈕。

   員工總數存在 Cloudflare KV（/api/part-state），任何人開頁都看得到最新值；
   要修改需要編輯碼（見 site/functions/api/part-state.js）。
"""
import json, os

from subsidiary_map import UCG_SUBS, PAGE_CATS

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SUM = json.load(open(os.path.join(HERE, "part_summary.json"), encoding="utf-8"))
EVENTS = json.load(open(os.path.join(HERE, "part_events.json"), encoding="utf-8"))

PAYLOAD = {
    "ucgSubs": UCG_SUBS,
    "cats": PAGE_CATS,
    "y2025": {c: SUM["y2025"][c] for c in PAGE_CATS},
    "y2026": {c: SUM["y2026"][c] for c in PAGE_CATS},
    "domains": SUM["groups"],
    "exceptions": SUM["exceptions"],
}

HTML = r"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>UCG · 先勢 · 台北博報堂 HTM｜練息場活動參與統計</title>
<style>
  :root{ --bg:#f5f3ee; --card:#fffdf9; --ink:#23282a; --muted:#6d7175; --line:#e4e0d6;
    --accent:#2f8f83; --accent-d:#1f6b61; --accent-soft:#dcefeb; --warn:#b06a2c;
    --y25:#8a8f7a; --y26:#2f8f83; --yes:#2f8f83; --wait:#b98a3e; --leave:#a35a52; --checkin:#2f6f8f;
    --shadow:0 1px 2px rgba(40,45,40,.05),0 6px 20px rgba(40,45,40,.06); }
  @media (prefers-color-scheme:dark){ :root{ --bg:#14171a; --card:#1b1f22; --ink:#e9e7e0; --muted:#9aa0a2;
    --line:#2c3236; --accent:#4db8aa; --accent-d:#7fd0c4; --accent-soft:#1e3d39; --warn:#d79a5c;
    --y25:#9aa08a; --y26:#4db8aa; --yes:#4db8aa; --wait:#d9ad63; --leave:#d38a80; --checkin:#6fb4d8;
    --shadow:0 1px 2px rgba(0,0,0,.3),0 8px 24px rgba(0,0,0,.35);} }
  :root[data-theme="dark"]{ --bg:#14171a; --card:#1b1f22; --ink:#e9e7e0; --muted:#9aa0a2; --line:#2c3236;
    --accent:#4db8aa; --accent-d:#7fd0c4; --accent-soft:#1e3d39; --warn:#d79a5c; --y25:#9aa08a; --y26:#4db8aa;
    --yes:#4db8aa; --wait:#d9ad63; --leave:#d38a80; --checkin:#6fb4d8;}
  :root[data-theme="light"]{ --bg:#f5f3ee; --card:#fffdf9; --ink:#23282a; --muted:#6d7175; --line:#e4e0d6;
    --accent:#2f8f83; --accent-d:#1f6b61; --accent-soft:#dcefeb; --warn:#b06a2c; --y25:#8a8f7a; --y26:#2f8f83;
    --yes:#2f8f83; --wait:#b98a3e; --leave:#a35a52; --checkin:#2f6f8f;}

  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);
    font-family:-apple-system,"PingFang TC","Noto Sans TC","Microsoft JhengHei",system-ui,sans-serif;
    line-height:1.6;-webkit-font-smoothing:antialiased;font-variant-numeric:tabular-nums;}
  .wrap{max-width:900px;margin:0 auto;padding:28px 18px 72px;}
  a{color:var(--accent-d)}
  header .eyebrow{font-size:.8rem;letter-spacing:.14em;text-transform:uppercase;color:var(--accent-d);font-weight:700;margin:0 0 6px}
  h1{font-size:1.55rem;line-height:1.3;margin:0 0 8px;text-wrap:balance;font-weight:800;letter-spacing:-.01em}
  .lede{color:var(--muted);margin:0 0 4px;font-size:.98rem}
  .card{background:var(--card);border:1px solid var(--line);border-radius:16px;box-shadow:var(--shadow);padding:20px 20px 16px;margin:20px 0}
  .card h2{font-size:1.12rem;margin:0 0 2px;font-weight:800;letter-spacing:-.01em}
  .pill{display:inline-block;font-size:.72rem;font-weight:700;padding:2px 8px;border-radius:999px;background:var(--accent-soft);color:var(--accent-d);margin-left:6px}
  .pill.warn{background:transparent;color:var(--warn);border:1px solid var(--warn)}
  .scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
  table{border-collapse:collapse;width:100%;min-width:560px;font-size:.92rem}
  th,td{padding:9px 10px;text-align:right;border-bottom:1px solid var(--line);white-space:nowrap}
  th:first-child,td:first-child{text-align:left}
  thead .grp{font-size:.72rem;letter-spacing:.06em;color:var(--muted);font-weight:700;text-transform:uppercase;
    border-bottom:2px solid var(--line);padding-bottom:4px}
  thead .grp.y25{color:var(--y25)} thead .grp.y26{color:var(--y26)}
  thead th{font-size:.78rem;color:var(--muted);font-weight:700;border-bottom:2px solid var(--line)}
  tbody td{font-size:.95rem}
  tbody tr:hover{background:color-mix(in srgb,var(--accent-soft) 45%,transparent)}
  .co{font-weight:700}
  .sub td:first-child{padding-left:26px;font-weight:600}
  .grouphead td{font-weight:800;color:var(--accent-d);background:color-mix(in srgb,var(--accent-soft) 22%,transparent)}
  .subtot td{font-weight:800;border-bottom:2px solid var(--line);background:color-mix(in srgb,var(--accent-soft) 14%,transparent)}
  .big{font-weight:800;font-size:1.02rem}
  .z{color:var(--muted)}
  tfoot td{border-top:2px solid var(--line);font-weight:800;background:color-mix(in srgb,var(--accent-soft) 30%,transparent)}
  .divider{border-left:2px solid var(--line)}
  .rate{color:var(--muted);font-size:.86rem}
  .rate.on{color:var(--accent-d);font-weight:700}

  /* 數據說明：小字底線連結 + 彈窗 */
  .notelink{font:inherit;font-size:.8rem;color:var(--muted);background:none;border:0;padding:0;cursor:pointer;
    text-decoration:underline;text-underline-offset:3px;text-decoration-thickness:1px}
  .notelink:hover{color:var(--accent-d)}
  .notebar{margin:6px 0 14px}
  dialog#noteDlg{border:1px solid var(--line);border-radius:16px;background:var(--card);color:var(--ink);
    padding:0;max-width:560px;width:calc(100% - 32px);box-shadow:0 12px 40px rgba(0,0,0,.25)}
  dialog#noteDlg::backdrop{background:rgba(20,23,26,.45)}
  .dlghd{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:16px 18px 6px}
  .dlghd h4{margin:0;font-size:1rem;font-weight:800}
  .dlgclose{background:none;border:0;color:var(--muted);font-size:1.2rem;line-height:1;cursor:pointer;padding:4px 6px}
  .dlgbody{padding:0 18px 20px;font-size:.85rem;color:var(--muted);line-height:1.8}
  .dlgbody b{color:var(--ink);font-weight:700}
  .dlgbody p{margin:0 0 10px}
  .dlgbody code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.8rem}

  /* 員工總數 / 參與率 */
  .hcbar{display:flex;flex-wrap:wrap;align-items:center;gap:10px;margin:0 0 12px;font-size:.82rem}
  .btn{font:inherit;font-size:.82rem;font-weight:700;padding:5px 12px;border-radius:999px;cursor:pointer;
    border:1px solid var(--line);background:var(--card);color:var(--ink)}
  .btn:hover{border-color:var(--accent)}
  .btn.pri{background:var(--accent);border-color:var(--accent);color:#fff}
  .hcinfo{color:var(--muted)}
  .hcmsg{color:var(--accent-d);font-weight:700}
  .hcmsg.bad{color:var(--warn)}
  input.code{font:inherit;font-size:.82rem;padding:5px 10px;border-radius:8px;border:1px solid var(--line);
    background:var(--bg);color:var(--ink);width:130px}
  input.hc{font:inherit;font-size:.9rem;width:74px;text-align:right;padding:3px 6px;border-radius:8px;
    border:1px solid transparent;background:transparent;color:var(--ink);font-variant-numeric:tabular-nums}
  input.hc:disabled{color:var(--muted)}
  input.hc:not(:disabled){border-color:var(--line);background:var(--bg)}
  input.hc:focus{outline:2px solid var(--accent);outline-offset:1px}

  /* 大區塊收合 */
  details.block{border:1px solid var(--line);border-radius:16px;background:var(--card);
    box-shadow:var(--shadow);margin:20px 0;overflow:hidden}
  details.block>summary{padding:18px 20px}
  details.block>summary .btitle{font-size:1.12rem;font-weight:800;letter-spacing:-.01em}
  details.block>summary .bmeta{font-size:.78rem;color:var(--muted);font-weight:600}
  details.block>summary .bchev{margin-left:auto;color:var(--muted);font-size:.9rem;transition:transform .18s}
  details.block[open]>summary .bchev{transform:rotate(180deg)}
  details.block>.bbody{padding:0 20px 18px}

  details.yearblk{border:0;background:transparent;box-shadow:none;border-radius:0;margin:18px 0 0;overflow:visible}
  details.yearblk>summary{padding:6px 2px;border-bottom:2px solid var(--line);margin-bottom:4px}
  details.yearblk>summary .ytitle{font-size:1.02rem;font-weight:800}
  details.yearblk>summary .ymeta{font-size:.78rem;color:var(--muted);font-weight:600}
  details.yearblk>summary .bchev{margin-left:auto;color:var(--muted);font-size:.9rem;transition:transform .18s}
  details.yearblk[open]>summary .bchev{transform:rotate(180deg)}

  h3.sech{font-size:1.05rem;margin:30px 0 6px;font-weight:800}
  h3.sech .pill{font-size:.7rem}
  details{border:1px solid var(--line);border-radius:12px;background:var(--card);margin:10px 0;overflow:hidden}
  details[open]{box-shadow:var(--shadow)}
  details.yearblk[open],details.block[open]{box-shadow:none}
  details.block[open]{box-shadow:var(--shadow)}
  summary{cursor:pointer;list-style:none;padding:13px 16px;display:flex;align-items:center;gap:10px;font-weight:700}
  summary::-webkit-details-marker{display:none}
  summary .chev{transition:transform .18s;color:var(--muted);font-size:.8rem}
  details[open]>summary .chev{transform:rotate(90deg)}
  summary .evname{flex:1;min-width:0}
  summary .evname .dt{color:var(--accent-d);margin-right:6px}
  summary .nums{font-size:.8rem;color:var(--muted);font-weight:700;white-space:nowrap;letter-spacing:.01em}
  summary .nums .yes{color:var(--yes)} summary .nums .wait{color:var(--wait)}
  summary .nums .leave{color:var(--leave)} summary .nums .checkin{color:var(--checkin)}
  summary .nums .sep{color:var(--line);margin:0 4px}
  .evbody{padding:2px 16px 14px}
  .rawtab{width:100%;border-collapse:collapse;font-size:.86rem;min-width:0}
  .rawtab td,.rawtab th{padding:6px 8px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}
  .rawtab th:first-child,.rawtab td:first-child{text-align:left}
  .rawtab th{color:var(--muted);font-size:.74rem;font-weight:700}
  .rawtab thead .yes{color:var(--yes)} .rawtab thead .wait{color:var(--wait)}
  .rawtab thead .leave{color:var(--leave)} .rawtab thead .checkin{color:var(--checkin)}
  .dom{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.82rem}
  .cotag{color:var(--muted);font-size:.76rem;margin-left:6px}
  .conm{font-weight:700}
  .dash{color:var(--muted)}
  .notdone{color:var(--warn);font-weight:700;font-size:.78rem}
  .foot{color:var(--muted);font-size:.8rem;margin-top:26px;line-height:1.6;border-top:1px solid var(--line);padding-top:16px}
  .theme{position:fixed;top:12px;right:12px;background:var(--card);border:1px solid var(--line);color:var(--muted);
    border-radius:999px;padding:6px 12px;font-size:.8rem;cursor:pointer;z-index:5}
  .legend{display:flex;flex-wrap:wrap;gap:12px;font-size:.78rem;color:var(--muted);margin:2px 0 4px}
  .legend b{font-weight:700}
  .legend .yes{color:var(--yes)} .legend .wait{color:var(--wait)}
  .legend .leave{color:var(--leave)} .legend .checkin{color:var(--checkin)}
  /* 歸戶區 */
  .maptab td:nth-child(1){font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.84rem;
    white-space:normal;font-weight:700}
  .maptab .vari{font-family:inherit;font-size:.72rem;font-weight:400;color:var(--muted);
    margin-top:2px;line-height:1.5;max-width:22em}
  .maptab td,.maptab th{text-align:left;vertical-align:top}
  .maptab td:nth-child(4),.maptab th:nth-child(4),
  .maptab td:nth-child(5),.maptab th:nth-child(5){text-align:right}
  .tag{display:inline-block;font-size:.72rem;font-weight:700;padding:1px 7px;border-radius:999px;
    border:1px solid var(--line);color:var(--muted)}
  .tag.ok{border-color:var(--accent);color:var(--accent-d)}
  .tag.ask{border-color:var(--warn);color:var(--warn)}
  .askbox{border:1px solid var(--warn);border-radius:12px;padding:12px 14px;margin:14px 0 2px;
    background:color-mix(in srgb,var(--warn) 7%,transparent)}
  .askbox h4{margin:0 0 6px;font-size:.9rem;color:var(--warn)}
  .askbox ul{margin:6px 0 0;padding-left:20px;font-size:.85rem;line-height:1.7}
  .askbox code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.82rem}
</style>
</head>
<body>
<button class="theme" id="themeBtn" aria-label="切換深淺色">◐ 主題</button>
<div class="wrap">
  <header>
    <p class="eyebrow">練息場 Join to Enjoy</p>
    <h1>UCG · 先勢 · 台北博報堂 HTM<br>參與練息場活動統計</h1>
    <p class="lede">聯廣傳播集團（UCG）各子公司、先勢集團、台北博報堂（HTM）同仁，參加練息場身心活動的統計。</p>
  </header>

  <!-- ===== 總表：實際到場（報到）===== -->
  <section class="card">
    <h2>實際到場總表<span class="pill">數字＝報到人數，非報名數</span></h2>
    <div class="notebar"><button class="notelink" data-note="sum">數據說明</button></div>

    <div class="hcbar">
      <button class="btn" id="hcEdit">✎ 編輯員工總數</button>
      <span class="hcinfo" id="hcInfo">填入各公司員工總數，即可算出參與率</span>
      <span id="hcLock" hidden>
        <input class="code" type="password" id="hcCode" placeholder="編輯碼" autocomplete="off">
        <button class="btn pri" id="hcSave">儲存到雲端</button>
        <button class="btn" id="hcCancel">取消</button>
      </span>
      <span class="hcmsg" id="hcMsg"></span>
    </div>

    <div class="scroll">
      <table id="summary" style="min-width:820px">
        <thead>
          <tr><th rowspan="2">公司</th>
            <th rowspan="2">員工總數</th>
            <th colspan="4" class="grp y25">2025 全年報到</th>
            <th colspan="4" class="grp y26 divider">2026 報到（截至 7/17 已辦）</th></tr>
          <tr><th class="y25">人次</th><th class="y25">人數</th><th class="y25">人次率</th><th class="y25">人數率</th>
            <th class="y26 divider">人次</th><th class="y26">人數</th><th class="y26">人次率</th><th class="y26">人數率</th></tr>
        </thead>
        <tbody id="sumBody"></tbody>
        <tfoot id="sumFoot"></tfoot>
      </table>
    </div>
  </section>

  <!-- ===== Email 歸戶區（預設收合）===== -->
  <details class="block" id="mapBlock">
    <summary>
      <span class="btitle">Email 歸戶對照</span>
      <span class="bmeta">怎麼判斷一封報名信屬於哪家</span>
      <span class="bchev">▾</span>
    </summary>
    <div class="bbody">
      <div class="notebar"><button class="notelink" data-note="map">數據說明</button></div>
      <div class="scroll">
        <table class="maptab">
          <thead><tr><th>Email 網域（已合併變體）</th><th>歸戶到</th><th>說明</th><th>2026 筆數</th><th>2026 報到</th></tr></thead>
          <tbody id="mapBody"></tbody>
        </table>
      </div>
      <div class="askbox" id="askBox"></div>
    </div>
  </details>

  <!-- ===== 各場明細（大區塊收合，內含 2026 / 2025 兩塊）===== -->
  <details class="block" id="evBlock">
    <summary>
      <span class="btitle">各場明細</span>
      <span class="bmeta" id="evMeta"></span>
      <span class="bchev">▾</span>
    </summary>
    <div class="bbody">
      <div class="legend">
        <span><b class="yes">正取</b>＝取得名額</span>
        <span><b class="wait">候補</b>＝額滿排補</span>
        <span><b class="leave">請假</b>＝取消</span>
        <span><b class="checkin">報到</b>＝當天實際到場</span>
      </div>
      <div class="notebar"><button class="notelink" data-note="ev">數據說明</button></div>

      <details class="yearblk" open>
        <summary><span class="ytitle">2026</span><span class="ymeta" id="m26"></span><span class="bchev">▾</span></summary>
        <div id="ev2026"></div>
      </details>

      <details class="yearblk" open>
        <summary><span class="ytitle">2025</span><span class="ymeta" id="m25"></span><span class="bchev">▾</span></summary>
        <div id="ev2025"></div>
      </details>
    </div>
  </details>

  <p class="foot" id="foot"></p>
</div>

<dialog id="noteDlg">
  <div class="dlghd"><h4 id="dlgTitle">數據說明</h4>
    <button class="dlgclose" id="dlgClose" aria-label="關閉">✕</button></div>
  <div class="dlgbody" id="dlgBody"></div>
</dialog>

<script>
const D = __DATA__;

const esc = s => String(s).replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));
const cellNum = n => n>0 ? String(n) : '<span class="z">0</span>';

/* ============ 數據說明彈窗 ============ */
const NOTES = {
  sum: ["實際到場總表 · 數據說明", `
    <p><b>數據來源</b>：現場<b>報到</b>紀錄（Google 試算表）。數字意義為<b>實際有到場者（報到）</b>，不是報名數。</p>
    <p><b>人次</b>＝重複參與（同一人參加多場累計）；<b>人數</b>＝不重複參與（同一人只算一次）。</p>
    <p><b>參與率</b>：填入員工總數後自動計算。<b>人次率</b>＝人次 ÷ 員工總數（可能超過 100%，代表平均每人不只參加一場）；
       <b>人數率</b>＝人數 ÷ 員工總數（代表全公司有多少比例的同仁至少來過一次）。</p>
    <p><b>公司分類</b>：UCG 拆為聯廣、聯太、聯樂、艾斯、聯眾、2008傳媒、迪維、聯勤；先勢集團不拆、維持一家。
       2026/1/16 那場歸入 2025 統計。</p>
    <p><b>2026 尚在進行中</b>：7/30、7/31 與 8 月之後的場次尚未舉辦，報到未計入。</p>
    <p><b>UCG 小計／三家合計</b>的員工總數＝各列<b>已填</b>數字的加總；還沒填的公司不會被算進去，
       所以填寫未齊時，合計列的參與率僅供參考。</p>
    <p>員工總數存放於雲端，任何人開啟此頁都會看到最新填寫的數字；修改需要編輯碼。</p>`],
  map: ["Email 歸戶對照 · 數據說明", `
    <p><b>歸戶方式</b>：<b>2025</b> 依現場報到名冊的「公司」欄；<b>2026</b> 依報名 email <b>@ 之後的網域</b>。</p>
    <p><b>網域已合併</b>：現場多為手動輸入，<code>.com.tw</code>／<code>.com</code> 與拼字常有出入，
       因此<b>名字相同者一律視為同一家</b>，合併成一列呈現。每列下方灰字為實際出現過的所有寫法（含打錯的變體）。</p>
    <p><b>筆數</b>＝2026 該網域的報名紀錄筆數；<b>報到</b>＝其中實際到場的人次。</p>
    <p>本頁只顯示 email 的網域，不含任何帳號或姓名。唯一例外是最下方「待確認」清單，
       為了讓貴集團能指認是哪位同仁，顯示遮罩後的帳號前兩碼。</p>`],
  ev: ["各場明細 · 數據說明", `
    <p><b>正取／候補／請假</b> 來源：Wix 報名系統。<b>報到</b> 來源：Google 現場報到表，
       與上方總表<b>同一份資料</b>，各場報到加總＝總表當年人次。</p>
    <p>只列上表三家（UCG／先勢／HTM）的資料，其餘集團公司與外部來賓不列入。</p>
    <p><b>2026</b> 各場以 <b>email 網域</b>為單位（寫法變體已合併，同歸戶對照）；
       <b>2025</b> 現場名冊沒有 email，故各場以<b>公司</b>為單位呈現。</p>
    <p>未舉辦的場次，報到欄標示「尚未舉辦」；名冊上查不到報到紀錄的場次以「—」表示。</p>`]
};
(function(){
  const dlg=document.getElementById("noteDlg");
  document.querySelectorAll(".notelink").forEach(b=>b.addEventListener("click",e=>{
    e.preventDefault(); e.stopPropagation();
    const n=NOTES[b.dataset.note]; if(!n) return;
    document.getElementById("dlgTitle").textContent=n[0];
    document.getElementById("dlgBody").innerHTML=n[1];
    dlg.showModal();
  }));
  document.getElementById("dlgClose").addEventListener("click",()=>dlg.close());
  dlg.addEventListener("click",e=>{ if(e.target===dlg) dlg.close(); });
})();

/* ============ 總表 + 員工總數 + 參與率 ============ */
const HC = {};                       // {公司: 員工總數}
const g25 = c => D.y2025[c] || {visits:0,people:0};
const g26 = c => D.y2026[c] || {att:0,att_uniq:0};
const sum = (list,f) => list.reduce((s,c)=>s+f(c),0);
const rate = (n,hc) => (hc>0) ? '<span class="rate on">'+Math.round(n/hc*100)+'%</span>'
                              : '<span class="rate">—</span>';

(function(){
  const ucg=D.ucgSubs;
  const row=(c,cls)=>{
    const a=g25(c), b=g26(c);
    return `<tr class="${cls}" data-cat="${esc(c)}"><td>${esc(c)}</td>
      <td><input class="hc" type="number" min="0" step="1" inputmode="numeric" placeholder="—"
                 aria-label="${esc(c)} 員工總數" data-cat="${esc(c)}" disabled></td>
      <td class="big">${cellNum(a.visits)}</td><td>${cellNum(a.people)}</td>
      <td class="r" data-r="25v" data-n="${a.visits}"></td><td class="r" data-r="25p" data-n="${a.people}"></td>
      <td class="big divider">${cellNum(b.att)}</td><td>${cellNum(b.att_uniq)}</td>
      <td class="r" data-r="26v" data-n="${b.att}"></td><td class="r" data-r="26p" data-n="${b.att_uniq}"></td></tr>`;
  };
  let rows=`<tr class="grouphead"><td colspan="10">UCG 聯廣傳播集團</td></tr>`;
  rows+=ucg.map(c=>row(c,"sub")).join("");
  rows+=`<tr class="subtot" id="ucgTot"><td>UCG 小計</td><td id="hcUcg" class="z">—</td>
    <td>${sum(ucg,c=>g25(c).visits)}</td><td>${sum(ucg,c=>g25(c).people)}</td>
    <td class="r" data-r="25v" data-n="${sum(ucg,c=>g25(c).visits)}"></td>
    <td class="r" data-r="25p" data-n="${sum(ucg,c=>g25(c).people)}"></td>
    <td class="divider">${sum(ucg,c=>g26(c).att)}</td><td>${sum(ucg,c=>g26(c).att_uniq)}</td>
    <td class="r" data-r="26v" data-n="${sum(ucg,c=>g26(c).att)}"></td>
    <td class="r" data-r="26p" data-n="${sum(ucg,c=>g26(c).att_uniq)}"></td></tr>`;
  rows+=row("先勢集團","co2");
  rows+=row("台北博報堂 HTM","co2");
  document.getElementById("sumBody").innerHTML=rows;

  const all=D.cats;
  document.getElementById("sumFoot").innerHTML=
    `<tr id="allTot"><td>三家合計</td><td id="hcAll" class="z">—</td>
      <td class="big">${sum(all,c=>g25(c).visits)}</td><td>${sum(all,c=>g25(c).people)}</td>
      <td class="r" data-r="25v" data-n="${sum(all,c=>g25(c).visits)}"></td>
      <td class="r" data-r="25p" data-n="${sum(all,c=>g25(c).people)}"></td>
      <td class="big divider">${sum(all,c=>g26(c).att)}</td><td>${sum(all,c=>g26(c).att_uniq)}</td>
      <td class="r" data-r="26v" data-n="${sum(all,c=>g26(c).att)}"></td>
      <td class="r" data-r="26p" data-n="${sum(all,c=>g26(c).att_uniq)}"></td></tr>`;
})();

function paintRates(){
  const ucgHC=sum(D.ucgSubs,c=>HC[c]||0);
  const allHC=sum(D.cats,c=>HC[c]||0);
  document.getElementById("hcUcg").textContent = ucgHC>0 ? ucgHC : "—";
  document.getElementById("hcAll").textContent = allHC>0 ? allHC : "—";
  document.querySelectorAll("#summary tr").forEach(tr=>{
    let hc=0;
    if(tr.id==="ucgTot") hc=ucgHC;
    else if(tr.id==="allTot") hc=allHC;
    else if(tr.dataset.cat) hc=HC[tr.dataset.cat]||0;
    else return;
    tr.querySelectorAll("td.r").forEach(td=>{
      td.innerHTML = rate(+td.dataset.n, hc);
    });
  });
}
function fillInputs(){
  document.querySelectorAll("input.hc").forEach(i=>{
    const v=HC[i.dataset.cat];
    i.value = (v===undefined || v===null) ? "" : v;
  });
}
document.addEventListener("input", e=>{
  if(!e.target.classList.contains("hc")) return;
  const v=parseInt(e.target.value,10);
  if(Number.isFinite(v) && v>=0) HC[e.target.dataset.cat]=v;
  else delete HC[e.target.dataset.cat];
  paintRates();
});

/* ---- 雲端讀寫（Cloudflare KV；本機預覽時 API 不存在，靜靜跳過）---- */
const API="/api/part-state";
const msg=(t,bad)=>{const m=document.getElementById("hcMsg");m.textContent=t;m.className="hcmsg"+(bad?" bad":"");};
function setInfo(updated){
  const has = Object.keys(HC).length>0;
  let t = "填入各公司員工總數，即可算出參與率";
  if(updated && has){
    const d=new Date(updated);
    t = "雲端最後更新："+(isNaN(d) ? updated.slice(0,16)
        : d.toLocaleString("zh-TW",{year:"numeric",month:"2-digit",day:"2-digit",
                                    hour:"2-digit",minute:"2-digit",hour12:false}));
  }
  document.getElementById("hcInfo").textContent = t;
}
(async function load(){
  try{
    const r=await fetch(API,{cache:"no-store"});
    if(!r.ok) throw 0;
    const j=await r.json();
    Object.assign(HC, j.headcount||{});
    setInfo(j.updated);
  }catch(e){ /* 本機預覽或尚未部署 */ }
  fillInputs(); paintRates();
})();

(function(){
  const edit=document.getElementById("hcEdit"), lock=document.getElementById("hcLock");
  const code=document.getElementById("hcCode");
  const enable=on=>document.querySelectorAll("input.hc").forEach(i=>i.disabled=!on);
  edit.addEventListener("click",()=>{ lock.hidden=false; edit.hidden=true; enable(true); msg(""); code.focus(); });
  document.getElementById("hcCancel").addEventListener("click",()=>{
    lock.hidden=true; edit.hidden=false; enable(false); code.value=""; msg("");
    fillInputs(); paintRates();
  });
  document.getElementById("hcSave").addEventListener("click",async()=>{
    msg("儲存中…");
    try{
      const r=await fetch(API,{method:"PUT",
        headers:{"content-type":"application/json","x-edit-code":code.value},
        body:JSON.stringify({headcount:HC})});
      const j=await r.json().catch(()=>({}));
      if(!r.ok){ msg(j.error||("儲存失敗（"+r.status+"）"),true); return; }
      setInfo(j.updated); msg("已儲存到雲端 ✓");
      lock.hidden=true; edit.hidden=false; enable(false); code.value="";
    }catch(e){ msg("連不上雲端（本機預覽不會儲存）",true); }
  });
})();

/* ============ Email 歸戶區 ============ */
(function(){
  const order=D.cats;
  const doms=D.domains.slice().sort((a,b)=>
    (order.indexOf(a.cat)-order.indexOf(b.cat)) || (b.rows-a.rows) || a.key.localeCompare(b.key));
  document.getElementById("mapBody").innerHTML = doms.map(x=>{
    const seen=(x.seen||[]);
    const vari = seen.length ? `<div class="vari">實際寫法：${seen.map(s=>"@"+esc(s)).join("、")}</div>` : "";
    return `<tr>
      <td>@${esc(x.key)}${vari}</td>
      <td>${esc(x.cat)} ${x.confirmed?'<span class="tag ok">已確認</span>':'<span class="tag ask">待確認</span>'}</td>
      <td class="z" style="white-space:normal">${esc(x.note)}</td>
      <td>${cellNum(x.rows)}</td><td>${cellNum(x.att)}</td></tr>`;}).join("");

  const ex=D.exceptions, box=document.getElementById("askBox");
  if(!ex.length){ box.style.display="none"; return; }
  box.innerHTML = `<h4>以下 ${ex.length} 筆需要貴集團幫忙確認歸戶</h4>
    <ul>` + ex.map(e => e.kind==="unmapped"
      ? `<li><code>${esc(e.email)}</code>：私人信箱，無法用網域判斷。報到表標為 <b>${esc(e.sheet)}</b> —— 請問實際是哪一家？（目前<b>未</b>計入上表）</li>`
      : `<li><code>${esc(e.email)}</code>：網域屬 <b>${esc(e.ours)}</b>，但報到表的「所屬企業」欄填 <b>${esc(e.sheet)}</b> —— 請問以哪個為準？（目前依網域計入 <b>${esc(e.ours)}</b>）</li>`
    ).join("") + `</ul>`;
})();

/* ============ 各場明細 ============ */
const TODAY = new Date().toISOString().slice(0,10);
const mmdd = d => { const p=d.split("-"); return (+p[1])+"/"+(+p[2]); };
const grpYear = e => e.date==="2026-01-16" ? "2025" : e.year;

function checkinCell(e,val,isTotal){
  if(e.date>TODAY) return isTotal ? '<span class="notdone">尚未舉辦</span>' : '<span class="dash">—</span>';
  if(!e.has_checkin) return '<span class="dash">—</span>';
  return cellNum(val);
}

function renderEvent(e){
  const t=e.totals, isDom = e.rowkind!=="cat";
  const future = e.date>TODAY;
  const ciSummary = future ? '<span class="notdone">尚未舉辦</span>'
                  : !e.has_checkin ? '<span class="dash">報到 —</span>'
                  : `報到 <span class="checkin">${t.c}</span>`;
  const raw = e.domains.map(d=>`<tr>
      <td>${isDom ? `<span class="dom">@${esc(d.d)}</span><span class="cotag">${esc(d.cat)}</span>`
                  : `<span class="conm">${esc(d.cat)}</span>`}</td>
      <td>${cellNum(d.y)}</td><td>${cellNum(d.w)}</td><td>${cellNum(d.l)}</td>
      <td>${checkinCell(e,d.c,false)}</td></tr>`).join("");
  return `<details>
    <summary><span class="chev">▸</span>
      <span class="evname"><span class="dt">${mmdd(e.date)}</span>${esc(e.title)}</span>
      <span class="nums"><span class="yes">正 ${t.y}</span><span class="sep">·</span>`+
      `<span class="wait">補 ${t.w}</span><span class="sep">·</span>`+
      `<span class="leave">假 ${t.l}</span><span class="sep">·</span>${ciSummary}</span></summary>
    <div class="evbody"><div class="scroll"><table class="rawtab">
      <thead><tr><th>${isDom ? "Email 網域（公司）" : "公司"}</th>
        <th class="yes">正取</th><th class="wait">候補</th><th class="leave">請假</th>
        <th class="checkin">報到</th></tr></thead>
      <tbody>${raw}</tbody>
      <tfoot><tr><td>小計</td><td>${t.y}</td><td>${t.w}</td><td>${t.l}</td>
        <td>${checkinCell(e,t.c,true)}</td></tr></tfoot>
    </table></div></div>
  </details>`;
}

(function(){
  const EV=__EVENTS__;
  const e26=EV.filter(e=>grpYear(e)==="2026"), e25=EV.filter(e=>grpYear(e)==="2025");
  const ci=list=>list.filter(e=>e.has_checkin).reduce((s,e)=>s+e.totals.c,0);
  document.getElementById("ev2026").innerHTML=e26.map(renderEvent).join("");
  document.getElementById("ev2025").innerHTML=e25.map(renderEvent).join("");
  document.getElementById("m26").textContent=`${e26.length} 場・報到 ${ci(e26)} 人次`;
  document.getElementById("m25").textContent=`${e25.length} 場・報到 ${ci(e25)} 人次`;
  document.getElementById("evMeta").textContent=`2026 ${e26.length} 場 · 2025 ${e25.length} 場`;
})();

document.getElementById("foot").innerHTML =
  "資料經去識別化：僅呈現公司層級數字與 email 網域，全程未輸出任何姓名或完整信箱。｜"+
  "報名（正取／候補／請假）來源：Wix 報名系統　·　報到來源：Google 現場報到表。";

const tb=document.getElementById("themeBtn"), root=document.documentElement;
tb.addEventListener("click",()=>{
  const cur=root.getAttribute("data-theme")||(matchMedia("(prefers-color-scheme:dark)").matches?"dark":"light");
  root.setAttribute("data-theme", cur==="dark"?"light":"dark");
});
</script>
</body>
</html>
"""

HTML = (HTML.replace("__DATA__", json.dumps(PAYLOAD, ensure_ascii=False))
            .replace("__EVENTS__", json.dumps(EVENTS, ensure_ascii=False)))
out = os.path.join(ROOT, "site", "part", "index.html")
open(out, "w", encoding="utf-8").write(HTML)
print("已寫出", out, "size=", len(HTML))
