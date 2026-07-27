// /part 頁的雲端設定：只存各子公司「員工總數」（2025 / 2026 分開），用來算參與率。
// 內容只有公司名稱與整數人數，無任何個資。
// GET  任何人都可讀（頁面載入時抓最新值）
// PUT  任何人都可寫（2026-07-27 大寶決定拿掉編輯碼：會進到這頁的人不多，讓每個人都能自己改）
const KEY = "part-state-v1";
const YEARS = ["2025", "2026"];
const EMPTY = { "2025": {}, "2026": {} };

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });
}

// 只收「公司名稱 -> 非負整數」，其他一律丟掉
function clean(src) {
  const out = {};
  for (const [k, v] of Object.entries(src || {})) {
    if (typeof k !== "string" || k.length > 40) continue;
    const n = Math.floor(Number(v));
    if (Number.isFinite(n) && n >= 0 && n < 1000000) out[k] = n;
  }
  return out;
}

export async function onRequestGet(context) {
  const raw = await context.env.STATE.get(KEY);
  return new Response(raw || JSON.stringify({ headcount: EMPTY }), {
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
  const src = body.headcount || {};
  const hc = {};
  for (const y of YEARS) hc[y] = clean(src[y]);
  if (YEARS.some((y) => Object.keys(hc[y]).length > 60)) {
    return json({ ok: false, error: "too many keys" }, 400);
  }
  const out = { headcount: hc, updated: new Date().toISOString() };
  await context.env.STATE.put(KEY, JSON.stringify(out));
  return json({ ok: true, ...out });
}
