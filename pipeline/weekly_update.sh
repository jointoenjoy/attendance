#!/bin/bash
# 每週三自動更新：重抓 Wix → 重算 /part、/all、/2026 → 部署 attendance-j2e → 把不含個資的檔 commit + push。
# 結果寫在 pipeline/_private/last_run.txt（第一行 OK 或 FAIL），排程任務讀它來寄通知信。
# 用法：bash pipeline/weekly_update.sh
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$ROOT/pipeline/_private/last_run.txt"
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
cd "$ROOT/pipeline"
TMP="$(mktemp)"
fail() { { echo "FAIL"; echo "失敗步驟：$1"; echo "時間：$(date '+%Y-%m-%d %H:%M')"; echo "---"; tail -40 "$TMP"; } > "$LOG"; cat "$LOG"; exit 1; }

git -C "$ROOT" pull --ff-only origin main >>"$TMP" 2>&1 || fail "git pull（抓雲端最新）"
for s in pull_2026_guests pull_states parse_part merge_part_events build_part build_all_2026 build_all_downloads build_2026; do
  echo "== $s" >>"$TMP"
  python3 "$s.py" >>"$TMP" 2>&1 || fail "$s.py"
done
# 對外 /part 頁絕不能有完整 email
if grep -qE "[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}" "$ROOT/site/part/index.html"; then fail "/part 個資檢查（發現完整 email，已停止部署）"; fi

( cd "$ROOT/site" && wrangler pages deploy . --project-name attendance-j2e --branch main --commit-dirty=true ) >>"$TMP" 2>&1 || fail "部署 attendance-j2e"

cd "$ROOT"
git add -A pipeline site .gitignore >>"$TMP" 2>&1
if ! git diff --cached --quiet; then
  git commit -m "每週自動更新 2026 Wix 數據（$(date '+%Y-%m-%d')）" >>"$TMP" 2>&1 || fail "git commit"
  git push origin main >>"$TMP" 2>&1 || fail "git push"
fi

{ echo "OK"; echo "時間：$(date '+%Y-%m-%d %H:%M')";
  grep -E "^/2026：|^未納入|^2026 已舉辦|各場加總|報到（Wix" "$TMP" | head -8; } > "$LOG"
cat "$LOG"
