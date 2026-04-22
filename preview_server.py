from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import mimetypes

ROOT = Path(__file__).resolve().parent
SQL_PATH = ROOT / 'expenses.sql'
HTML_PATH = ROOT / 'expenses.html'
STATIC_DIR = ROOT / 'static'
PROMPT_SNIPPET = """const password = prompt(\"请输入密码以继续:\");\n            if (password !== \"7758\") {\n                alert(\"密码错误，无法访问页面。\");\n                document.body.innerHTML = \"<h1 style='text-align:center;color:red;'>访问被拒绝</h1>\";\n            }"""

INSERT_RE = re.compile(r"INSERT INTO expenses VALUES\(([^,]+),'(\d{4}-\d{2}-\d{2})',([0-9.]+),'([^']+)'\);")


def load_expenses():
    text = SQL_PATH.read_text(encoding='utf-8')
    expenses = []
    for expense_id, day, amount, category in INSERT_RE.findall(text):
        expenses.append({
            'id': int(expense_id),
            'date': day,
            'amount': float(amount),
            'category': category,
        })
    return expenses


def load_month_data(expenses):
    month_data = []
    month_totals = defaultdict(float)
    for item in expenses:
        month_totals[(item['date'][:7], item['category'])] += item['amount']
    for (month, category), amount in sorted(month_totals.items()):
        month_data.append({
            'month': month,
            'category': category,
            'amount': round(amount, 2),
        })
    return month_data


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path):
        if not path.exists() or not path.is_file():
            self.send_error(404, 'Not found')
            return
        content = path.read_bytes()
        mime_type, _ = mimetypes.guess_type(path.name)
        self.send_response(200)
        self.send_header('Content-Type', mime_type or 'application/octet-stream')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format, *args):
        return

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ('/', '/expenses.html'):
            html = HTML_PATH.read_text(encoding='utf-8').replace(PROMPT_SNIPPET, 'const password = "7758";')
            body = html.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path.startswith('/static/'):
            return self._send_file(ROOT / parsed.path.lstrip('/'))
        if parsed.path == '/monthData':
            params = parse_qs(parsed.query)
            month = params.get('month', [''])[0]
            month_data = load_month_data(load_expenses())
            if month:
                filtered = [item for item in month_data if item['month'] == month]
            else:
                filtered = month_data
            return self._send_json(filtered)
        if parsed.path == '/expenses':
            params = parse_qs(parsed.query)
            day = params.get('date', [''])[0]
            expenses = load_expenses()
            if day:
                filtered = [item for item in expenses if item['date'] == day]
            else:
                filtered = [item for item in expenses if item['date'] <= date.today().isoformat()]
            return self._send_json(filtered)
        self.send_error(404, 'Not found')


if __name__ == '__main__':
    server = ThreadingHTTPServer(('127.0.0.1', 8766), Handler)
    print('preview server listening on http://127.0.0.1:8766', flush=True)
    server.serve_forever()
