#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] 停止 gpt-accounting 本地预览相关进程/容器"
pkill -f "python main.py" >/dev/null 2>&1 || true
docker rm -f gpt-accounting-mysql >/dev/null 2>&1 || true
echo "[OK] 已停止"
