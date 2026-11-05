// /2026 網域歸戶確認的回覆：每個 @網域「企業名稱對不對」打勾、改歸哪家公司、留言。
// 只存網域、公司名稱與備註文字，沒有姓名、email、手機。整條路徑跟 /2026 一樣要密碼（見 _middleware.js）。
// GET  讀最新一份回覆（頁面載入時帶回勾選狀態）
// PUT  送出：覆寫最新一份，並把這次送出另存一筆歷史（最多留 50 筆）
const KEY = "domain-check-2026-v1";
const HIST = "domain-check-2026-history";

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });
}

const str = (v, n) => (typeof v === "string" ? v.trim().slice(0, n) : "");

export async function onRequestGet(context) {
  const raw = await context.env.STATE.get(KEY);
  return new Response(raw || JSON.stringify({ items: {} }), {
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });
}

export async function onRequestPut(context) {
  let body;
  try {
    body = await context.request.json();
  } catch (e) {
    return json({ ok: false, error: "bad json" }, 400);
  }
  const items = {};
  for (const [d, v] of Object.entries(body.items || {})) {
    if (!/^[a-z0-9.-]{1,80}$/.test(d) || !v || typeof v !== "object") continue;
    items[d] = { ok: v.ok === true, co: str(v.co, 40), note: str(v.note, 300) };
  }
  if (Object.keys(items).length > 100) return json({ ok: false, error: "too many" }, 400);
  const out = { items, by: str(body.by, 30), updated: new Date().toISOString() };
  await context.env.STATE.put(KEY, JSON.stringify(out));
  let hist = [];
  try { hist = JSON.parse((await context.env.STATE.get(HIST)) || "[]"); } catch (e) {}
  hist.unshift(out);
  await context.env.STATE.put(HIST, JSON.stringify(hist.slice(0, 50)));
  return json({ ok: true, updated: out.updated });
}
