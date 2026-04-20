#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v docker >/dev/null 2>&1; then
  echo "[ERROR] docker 未安装，无法启动本地 MySQL 预览环境。"
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "[ERROR] docker daemon 未运行。请先启动 Docker。"
  exit 1
fi

readarray -t CFG < <(python3 - <<'PY'
from pathlib import Path
import re
from urllib.parse import urlparse
text = Path('main.py').read_text(encoding='utf-8')
m = re.search(r'DATABASE_URL\s*=\s*"([^"]+)"', text)
if not m:
    raise SystemExit('DATABASE_URL not found in main.py')
parsed = urlparse(m.group(1))
print(parsed.username or '')
print(parsed.password or '')
print(parsed.path.lstrip('/'))
PY
)

DB_USER="${CFG[0]}"
DB_PASS="${CFG[1]}"
DB_NAME="${CFG[2]}"
MYSQL_CONTAINER="gpt-accounting-mysql"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip >/dev/null
pip install fastapi uvicorn sqlalchemy pydantic starlette pymysql cryptography >/dev/null

if ! docker ps --format '{{.Names}}' | grep -qx "$MYSQL_CONTAINER"; then
  docker rm -f "$MYSQL_CONTAINER" >/dev/null 2>&1 || true
  docker run -d \
    --name "$MYSQL_CONTAINER" \
    -e MYSQL_DATABASE="$DB_NAME" \
    -e MYSQL_USER="$DB_USER" \
    -e MYSQL_PASSWORD="$DB_PASS" \
    -e MYSQL_ROOT_PASSWORD="$DB_PASS" \
    -p 3306:3306 \
    mysql:8 >/dev/null
fi

python3 - <<'PY'
import subprocess, time, sys
for _ in range(60):
    logs = subprocess.run(['docker','logs','gpt-accounting-mysql'], capture_output=True, text=True)
    txt = ((logs.stdout or '') + (logs.stderr or '')).lower()
    if 'ready for connections' in txt:
        print('[OK] MySQL 已就绪')
        sys.exit(0)
    time.sleep(2)
print('[ERROR] MySQL 启动超时')
sys.exit(1)
PY

echo "[OK] 启动记账应用：http://127.0.0.1:8000/"
echo "[INFO] 页面密码：7758"
exec python main.py
