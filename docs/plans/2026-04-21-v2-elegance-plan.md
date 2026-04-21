# V.2.0 Elegance Refactor Plan

> **For Hermes:** Improve architecture, reliability, and maintainability on branch `V.2.0`.

**Goal:** Remove fragile monthly summary state, clean up frontend rendering logic, and make local development simpler and more predictable.

**Architecture:** Replace stored `monthdata` dependency with runtime aggregation from `expenses`, introduce a small pure logic module for testable business rules, and simplify local preview to use SQLite by default while keeping optional MySQL support via `DATABASE_URL`.

**Tech Stack:** FastAPI, SQLAlchemy, SQLite/MySQL via `DATABASE_URL`, vanilla HTML/JS, unittest.

---

## Planned Tasks

1. Add failing tests for expense aggregation helpers and frontend category fallback.
2. Extract pure expense aggregation logic into a separate module.
3. Refactor `main.py` to use environment-based config and computed monthly stats.
4. Refactor `expenses.html` for unknown-category fallback, reduced duplication, and dead-code cleanup.
5. Simplify local preview scripts and align `requirements.txt` + `README.md` with actual behavior.
6. Run verification and review final diff.
