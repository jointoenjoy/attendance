// /part 頁的雲端設定：目前只存各子公司的「員工總數」，用來算參與率。
// 內容只有公司名稱與整數人數，無任何個資。
// GET  任何人都可讀（頁面載入時抓最新值）
// PUT  需要編輯碼（header: x-edit-code），避免外部拿到網址的人亂改
const KEY = "part-state-v1";

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });
}

export async function onRequestGet(context) {
  const raw = await context.env.STATE.get(KEY);
  return new Response(raw || '{"headcount":{}}', {
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });
}

export async function onRequestPut(context) {
  // 預設編輯碼；之後想換，去 Cloudflare Pages 專案設環境變數 PART_EDIT_CODE 即可（不用改程式）
  const code = context.env.PART_EDIT_CODE || "jte-ucg-2026";
  if (context.request.headers.get("x-edit-code") !== code) {
    return json({ ok: false, error: "編輯碼不正確" }, 403);
  }
  let body;
  try {
    body = await context.request.json();
  } catch (e) {
    return json({ ok: false, error: "bad json" }, 400);
  }
  // 只收「公司名稱 -> 非負整數」，其他一律丟掉
  const hc = {};
  for (const [k, v] of Object.entries(body.headcount || {})) {
    if (typeof k !== "string" || k.length > 40) continue;
    const n = Math.floor(Number(v));
    if (Number.isFinite(n) && n >= 0 && n < 1000000) hc[k] = n;
  }
  if (Object.keys(hc).length > 60) return json({ ok: false, error: "too many keys" }, 400);
  const out = { headcount: hc, updated: new Date().toISOString() };
  await context.env.STATE.put(KEY, JSON.stringify(out));
  return json({ ok: true, ...out });
}
