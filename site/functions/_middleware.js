// 只保護 /all（全集團互動工具）。/part 是要獨立給外部看的，完全不設密碼。
//
// 做法：進 /all 之前先出一頁輸入密碼，輸對就寫一個 cookie，之後同一台裝置直接進得去。
// 連 /api/state（/all 的資料端點）也一起擋，否則只擋畫面、資料還是被抓得走。
//
// 想換密碼：到 Cloudflare Pages 專案設環境變數 ALL_PASSWORD 即可，不用改程式。
const DEFAULT_PW = "27390000";
const COOKIE = "jte_all";

const GATED = (p) => p === "/all" || p.startsWith("/all/") || p === "/api/state";

async function tokenOf(pw) {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode("jte:" + pw));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

function cookieVal(req, name) {
  const raw = req.headers.get("cookie") || "";
  for (const part of raw.split(";")) {
    const [k, ...v] = part.trim().split("=");
    if (k === name) return v.join("=");
  }
  return null;
}

function loginPage(path, bad) {
  return `<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>需要密碼</title><style>
:root{--brand:#004D89;--ink:#032639;--line:#DBE0E3;--muted:#6F838E;--radius:16px;
  --spring:cubic-bezier(.32,.72,0,1)}
*{box-sizing:border-box}
body{margin:0;min-height:100vh;display:grid;place-items:center;background:#fff;color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"PingFang TC","Noto Sans TC",system-ui,sans-serif;padding:24px}
.box{position:relative;overflow:hidden;width:100%;max-width:360px;border-radius:24px;padding:32px 26px;
  background:linear-gradient(135deg,#CCE0F7 0%,#D3F5EC 58%,#FFFBEA 100%)}
.box>*{position:relative;z-index:1}
.orb{position:absolute;display:block;opacity:.5;border-radius:58% 42% 47% 53% / 45% 52% 48% 55%;
  will-change:transform}
.o1{width:120px;height:120px;background:#FFEBD3;right:-34px;top:-38px;animation:d1 24s ease-in-out infinite alternate}
.o2{width:64px;height:64px;background:#E6E5FB;left:-20px;bottom:-24px;animation:d2 28s ease-in-out infinite alternate}
@keyframes d1{to{transform:translate3d(-20px,18px,0) rotate(16deg) scale(1.08)}}
@keyframes d2{to{transform:translate3d(18px,-16px,0) rotate(-12deg) scale(1.1)}}
p.eb{margin:0 0 8px;font-size:.74rem;letter-spacing:.16em;font-weight:700;color:var(--brand)}
h1{margin:0 0 6px;font-size:1.24rem;font-weight:800;letter-spacing:-.02em;color:var(--brand)}
p.sub{margin:0 0 20px;font-size:.84rem;color:#4B6472;line-height:1.7}
input{width:100%;font:inherit;font-size:1rem;padding:11px 14px;border-radius:12px;border:1px solid var(--line);
  background:rgba(255,255,255,.85);color:var(--ink);text-align:center;letter-spacing:.2em;
  transition:border-color .2s var(--spring)}
input:focus{outline:2px solid #6694B8;outline-offset:1px}
button{width:100%;margin-top:12px;font:inherit;font-size:.92rem;font-weight:700;padding:11px;border-radius:999px;
  border:0;background:var(--brand);color:#fff;cursor:pointer;transition:transform .1s var(--spring),background-color .2s}
button:hover{background:#003864}
button:active{transform:scale(.97)}
.err{margin:12px 0 0;font-size:.82rem;color:#B4593A;font-weight:700}
.tip{margin:16px 0 0;font-size:.76rem;color:var(--muted);line-height:1.7}
@media (prefers-reduced-motion:reduce){.orb{animation:none}*{transition-duration:.01ms!important}}
</style></head><body>
<form class="box" method="post" action="${path}">
  <span class="orb o1"></span><span class="orb o2"></span>
  <p class="eb">練息場 Join to Enjoy</p>
  <h1>這一頁需要密碼</h1>
  <p class="sub">全集團互動工具（內部使用）。請輸入密碼後繼續。</p>
  <input type="password" name="pw" inputmode="numeric" autocomplete="current-password"
         placeholder="請輸入密碼" autofocus>
  <button type="submit">進入</button>
  ${bad ? '<p class="err">密碼不正確，請再試一次。</p>' : ""}
  <p class="tip">對外分享的統計頁不需要密碼，網址結尾是 <b>/part</b>。</p>
</form></body></html>`;
}

export async function onRequest(context) {
  const { request, env, next } = context;
  const url = new URL(request.url);
  if (!GATED(url.pathname)) return next();

  const token = await tokenOf(env.ALL_PASSWORD || DEFAULT_PW);
  if (cookieVal(request, COOKIE) === token) return next();

  // 送出密碼
  if (request.method === "POST") {
    const form = await request.formData().catch(() => null);
    const pw = form && form.get("pw");
    if (pw && (await tokenOf(String(pw))) === token) {
      return new Response(null, {
        status: 303,
        headers: {
          location: url.pathname,
          // 30 天內同一台裝置不用再輸入
          "set-cookie": `${COOKIE}=${token}; Path=/; Max-Age=2592000; HttpOnly; Secure; SameSite=Lax`,
        },
      });
    }
    return new Response(loginPage(url.pathname, true), {
      status: 401,
      headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store" },
    });
  }

  // 沒登入時，資料端點直接回 401 JSON，不要餵 HTML 給前端的 fetch
  if (url.pathname === "/api/state") {
    return new Response(JSON.stringify({ error: "unauthorized" }), {
      status: 401,
      headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
    });
  }

  return new Response(loginPage(url.pathname, false), {
    status: 401,
    headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store" },
  });
}
