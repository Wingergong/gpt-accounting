# FastAPI Expense Tracker

A family expense tracker built with FastAPI and a lightweight HTML frontend. It supports daily expense entry, category-based monthly summaries, and simple local preview for personal use.

## Features

- Add, list, and delete expenses
- Category-based monthly summaries computed directly from expense records
- Daily budget overview on the homepage
- Local preview with SQLite by default
- Optional MySQL support through `DATABASE_URL`

## Tech Stack

- FastAPI
- SQLAlchemy
- SQLite by default (`expenses.db`)
- Optional MySQL via `pymysql`
- Vanilla HTML + Bootstrap

## Installation

```bash
git clone https://github.com/Wingergong/gpt-accounting.git
cd gpt-accounting
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

### Default database

By default the app uses local SQLite:

```bash
sqlite:///./expenses.db
```

### Optional MySQL

To use MySQL instead, set `DATABASE_URL` before starting the app:

```bash
export DATABASE_URL="mysql+pymysql://username:password@localhost:3306/expense"
```

### Optional CORS origins

```bash
export ALLOWED_ORIGINS="http://localhost:8000,http://127.0.0.1:8000"
```

### Optional port

```bash
export PORT=8000
```

## Run locally

Recommended:

```bash
./start_local_preview.sh
```

Then open:

```text
http://127.0.0.1:8000/
```

Stop it with:

```bash
./stop_local_preview.sh
```

## Important note about password prompt

The current page includes a frontend password prompt for convenience only. It is **not real backend authentication** and should not be treated as security.

## API Endpoints

### Create expense

```http
POST /expenses/
Content-Type: application/json

{
  "date": "2026-04-21",
  "amount": 25.50,
  "category": "水电费"
}
```

### Get expenses by date

```http
GET /expenses?date=2026-04-21
```

### Delete expense

```http
DELETE /expenses/{expense_id}
```

### Get month summary

```http
GET /monthData?month=2026-04
```

Returns aggregated totals by category for the given month.

## Project Structure

```text
gpt-accounting/
├── main.py
├── expense_logic.py
├── expenses.html
├── requirements.txt
├── start_local_preview.sh
├── stop_local_preview.sh
├── static/
└── tests/
```

## Testing

Run all tests:

```bash
python3 -m unittest discover -s tests -v
```

## Recent Improvements in V.2.0

- Added expense category `水电费`
- Replaced fragile stored monthly summary flow with runtime aggregation from expenses
- Added category fallback handling for unknown categories in the frontend
- Simplified local preview to SQLite-first setup
- Updated scripts and docs to match actual runtime behavior
