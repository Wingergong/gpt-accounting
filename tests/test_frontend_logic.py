import unittest
from pathlib import Path


class FrontendLogicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = Path("expenses.html").read_text(encoding="utf-8")

    def test_month_selector_logic_preserves_selected_month(self):
        self.assertIn('function updateMonthSelect(monthdata, selectedMonth)', self.html)
        self.assertIn('monthSelect.value = selectedMonth;', self.html)
        self.assertIn('const selectedMonth = selectedMonthOverride ?? monthSelect.value;', self.html)
        self.assertIn('await loadMonthStats(currentMonth);', self.html)

    def test_frontend_formats_string_amounts_with_number_coercion(self):
        self.assertIn('Number(expense.amount).toFixed(2)', self.html)
        self.assertIn('sum + parseFloat(item.amount)', self.html)
        self.assertIn('parseFloat(b.amount) - parseFloat(a.amount)', self.html)


if __name__ == "__main__":
    unittest.main()
