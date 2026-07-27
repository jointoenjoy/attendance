// 雲端狀態儲存：GET 讀最新、PUT 覆寫最新。資料只有公司層級數字與員工總數，無個資。
const KEY = "boda-state-v1";

export async function onRequestGet(context) {
  const raw = await context.env.STATE.get(KEY);
  return new Response(raw || "null", {
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });
}

export async function onRequestPut(context) {
  const body = await context.request.text();
  // 基本防呆：必須是合法 JSON 且不過大（256KB 上限）
  if (body.length > 256 * 1024) return new Response("too large", { status: 413 });
  try { JSON.parse(body); } catch (e) { return new Response("bad json", { status: 400 }); }
  await context.env.STATE.put(KEY, body);
  return new Response(JSON.stringify({ ok: true }), {
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}
