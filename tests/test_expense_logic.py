import unittest
from datetime import date
from decimal import Decimal

from expense_logic import build_month_summary, normalize_category


class ExpenseLogicTests(unittest.TestCase):
    def test_normalize_category_uses_custom_category_for_other(self):
        expense = {"category": "其他", "customCategory": "水电费"}
        self.assertEqual(normalize_category(expense), "水电费")

    def test_normalize_category_keeps_regular_category(self):
        expense = {"category": "早餐"}
        self.assertEqual(normalize_category(expense), "早餐")

    def test_build_month_summary_groups_by_month_and_category(self):
        expenses = [
            {"date": date(2026, 4, 1), "category": "早餐", "amount": 10.0},
            {"date": date(2026, 4, 3), "category": "早餐", "amount": 12.5},
            {"date": date(2026, 4, 3), "category": "水电费", "amount": 88.0},
            {"date": date(2026, 5, 1), "category": "早餐", "amount": 5.0},
        ]

        summary = build_month_summary(expenses)

        self.assertEqual(
            summary,
            [
                {"month": "2026-04", "category": "早餐", "amount": 22.5},
                {"month": "2026-04", "category": "水电费", "amount": 88.0},
                {"month": "2026-05", "category": "早餐", "amount": 5.0},
            ],
        )

    def test_build_month_summary_uses_decimal_precision_for_currency(self):
        expenses = [
            {"date": date(2026, 4, 1), "category": "早餐", "amount": Decimal("1.005")},
            {"date": date(2026, 4, 2), "category": "早餐", "amount": Decimal("1.005")},
            {"date": date(2026, 4, 3), "category": "早餐", "amount": Decimal("0.67")},
        ]

        summary = build_month_summary(expenses)

        self.assertEqual(
            summary,
            [
                {"month": "2026-04", "category": "早餐", "amount": Decimal("2.69")},
            ],
        )


if __name__ == "__main__":
    unittest.main()
