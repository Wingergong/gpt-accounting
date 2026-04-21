#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8000}"

echo "[INFO] 停止 gpt-accounting 本地预览相关进程 (port=${PORT})"
pids=$(python3 - <<'PY'
import os, socket, struct
port = int(os.environ.get('PORT', '8000'))
hex_port = format(port, '04X')
pids = set()
for path in ['/proc/net/tcp', '/proc/net/tcp6']:
    try:
        with open(path) as f:
            next(f)
            for line in f:
                parts = line.split()
                local = parts[1]
                inode = parts[9]
                if local.endswith(':' + hex_port):
                    pids.add(inode)
    except FileNotFoundError:
        pass
inode_to_pid = []
for pid in filter(str.isdigit, os.listdir('/proc')):
    fd_dir = f'/proc/{pid}/fd'
    try:
        for fd in os.listdir(fd_dir):
            target = os.readlink(f'{fd_dir}/{fd}')
            if target.startswith('socket:['):
                inode = target[8:-1]
                if inode in pids:
                    inode_to_pid.append(pid)
                    break
    except Exception:
        continue
print(' '.join(sorted(set(inode_to_pid))))
PY
)
if [ -n "$pids" ]; then
  kill $pids >/dev/null 2>&1 || true
fi
echo "[OK] 已停止"
