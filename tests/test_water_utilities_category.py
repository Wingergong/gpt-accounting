import unittest
from datetime import date
from pathlib import Path


class WaterUtilitiesCategoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = Path("expenses.html").read_text(encoding="utf-8")

    def test_category_button_exists_for_water_utilities(self):
        self.assertIn('data-value="水电费"', self.html)
        self.assertIn('>水电费<', self.html)

    def test_categories_config_contains_water_utilities(self):
        self.assertIn('"水电费":', self.html)
        self.assertIn('emoji: "💧"', self.html)

    def test_unknown_category_has_fallback_config(self):
        self.assertIn('function getCategoryMeta(category)', self.html)
        self.assertIn('emoji: "🏷️"', self.html)
        self.assertIn('name: category', self.html)


if __name__ == "__main__":
    unittest.main()
