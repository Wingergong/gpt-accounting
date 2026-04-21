from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable, Mapping

MONEY_QUANTUM = Decimal("0.01")


def normalize_category(expense: Mapping[str, Any]) -> str:
    category = str(expense.get("category", "")).strip()
    custom_category = str(expense.get("customCategory", "")).strip()
    if category == "其他" and custom_category:
        return custom_category
    return category



def normalize_amount(value: Any) -> Decimal:
    return Decimal(str(value)).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)



def format_amount(value: Any) -> str:
    return f"{normalize_amount(value):.2f}"



def build_month_summary(expenses: Iterable[Mapping[str, Any]]) -> list[dict[str, Decimal | str]]:
    totals: dict[tuple[str, str], Decimal] = defaultdict(lambda: Decimal("0.00"))
    for expense in expenses:
        expense_date = expense["date"]
        if isinstance(expense_date, str):
            expense_date = date.fromisoformat(expense_date)
        month = expense_date.strftime("%Y-%m")
        category = str(expense["category"])
        totals[(month, category)] += normalize_amount(expense["amount"])

    return [
        {"month": month, "category": category, "amount": normalize_amount(amount)}
        for (month, category), amount in sorted(totals.items(), key=lambda item: (item[0][0], item[0][1]))
    ]
