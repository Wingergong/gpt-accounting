from pathlib import Path
import unittest

HTML_PATH = Path(__file__).resolve().parents[1] / "expenses.html"


def read_html() -> str:
    return HTML_PATH.read_text(encoding="utf-8")


class FrontendOptimizationsTests(unittest.TestCase):
    def test_uses_category_fallback_helper_for_unknown_categories(self):
        html = read_html()
        self.assertIn("function getCategoryMeta(category)", html)
        self.assertIn("const meta = getCategoryMeta(expense.category);", html)
        self.assertIn("const meta = getCategoryMeta(category);", html)
        self.assertNotIn("categories[expense.category].emoji", html)
        self.assertNotIn("categories[category].emoji", html)

    def test_removes_legacy_custom_category_dead_code(self):
        html = read_html()
        legacy_tokens = [
            "customCategory",
            "getElementById('category')",
            "querySelectorAll('.category')",
            "style.backgroundColor = '#d1e7dd'",
        ]
        for token in legacy_tokens:
            with self.subTest(token=token):
                self.assertNotIn(token, html)

    def test_active_form_hooks_exist_for_basic_regression_coverage(self):
        html = read_html()
        required_snippets = [
            'id="expenseForm"',
            'id="date"',
            'id="amount"',
            'id="expenseTable"',
            'id="monthSelect"',
            'id="stats-tab"',
        ]
        for snippet in required_snippets:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, html)


if __name__ == "__main__":
    unittest.main()
