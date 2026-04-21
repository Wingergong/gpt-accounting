#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip >/dev/null
pip install -r requirements.txt >/dev/null

export DATABASE_URL="${DATABASE_URL:-sqlite:///$(pwd)/expenses.db}"
export PORT="${PORT:-8000}"

echo "[OK] 启动记账应用：http://127.0.0.1:${PORT}/"
echo "[INFO] 页面密码：7758（仅前端提示，不是安全鉴权）"
exec python main.py
