from pathlib import Path
import json
import re
import subprocess
import textwrap
import unittest

REPO_DIR = Path(__file__).resolve().parents[1]
HTML_PATH = REPO_DIR / "expenses.html"
SQL_PATH = REPO_DIR / "expenses.sql"
ALLOWED_CATEGORIES = ["早餐", "午餐", "晚餐", "咖啡饮料", "旅行", "教育", "超市", "网购", "其他"]
INSERT_RE = re.compile(r"INSERT INTO expenses VALUES\([^,]+,'(\d{4}-\d{2}-\d{2})',[0-9.]+,'([^']+)'\);")


def run_node(script: str):
    completed = subprocess.run(
        ["node", "-e", script],
        cwd=REPO_DIR,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(completed.stdout)


def latest_allowed_months_from_sql():
    rows = INSERT_RE.findall(SQL_PATH.read_text(encoding="utf-8"))
    months = sorted({day[:7] for day, category in rows if category in ALLOWED_CATEGORIES})
    return months[-3:]


class MonthlyInsightsFeatureTests(unittest.TestCase):
    def test_html_exposes_recent_three_month_comparison_and_suggestions(self):
        html = HTML_PATH.read_text(encoding="utf-8")
        self.assertIn('id="recentThreeMonthSummary"', html)
        self.assertIn('id="recentThreeMonthComparison"', html)
        self.assertIn('id="optimizationSuggestions"', html)
        self.assertIn('<script src="/static/monthly-insights.js"></script>', html)
        self.assertIn('loadRecentThreeMonthInsights()', html)
        self.assertIn('filterAllowedMonthData', html)

    def test_sql_fixture_covers_three_recent_months_for_allowed_categories(self):
        self.assertEqual(latest_allowed_months_from_sql(), ['2025-10', '2025-11', '2025-12'])

    def test_build_recent_three_month_comparison_uses_latest_three_months_and_filters_unknown_categories(self):
        script = textwrap.dedent(
            """
            const helpers = require('./static/monthly-insights.js');
            const sample = [
              { month: '2025-09', category: '超市', amount: 80 },
              { month: '2025-10', category: '旅行', amount: 120 },
              { month: '2025-11', category: '旅行', amount: 240 },
              { month: '2025-12', category: '旅行', amount: 360 },
              { month: '2025-10', category: '超市', amount: 50 },
              { month: '2025-11', category: '超市', amount: 70 },
              { month: '2025-12', category: '超市', amount: 90 },
              { month: '2025-11', category: '月亮', amount: 888 },
              { month: '2025-12', category: '测试', amount: 666 }
            ];
            const result = helpers.buildRecentThreeMonthComparison(sample);
            console.log(JSON.stringify(result));
            """
        )
        result = run_node(script)
        self.assertEqual(result['months'], ['2025-10', '2025-11', '2025-12'])
        categories = {item['category'] for item in result['categories']}
        self.assertEqual(categories, {'旅行', '超市'})
        travel = next(item for item in result['categories'] if item['category'] == '旅行')
        self.assertEqual(travel['values'], [120, 240, 360])
        self.assertEqual(travel['total'], 720)

    def test_build_recent_three_month_comparison_keeps_only_latest_month_top_three_categories(self):
        script = textwrap.dedent(
            """
            const helpers = require('./static/monthly-insights.js');
            const sample = [
              { month: '2025-10', category: '旅行', amount: 120 },
              { month: '2025-11', category: '旅行', amount: 220 },
              { month: '2025-12', category: '旅行', amount: 320 },
              { month: '2025-10', category: '网购', amount: 80 },
              { month: '2025-11', category: '网购', amount: 180 },
              { month: '2025-12', category: '网购', amount: 280 },
              { month: '2025-10', category: '晚餐', amount: 60 },
              { month: '2025-11', category: '晚餐', amount: 160 },
              { month: '2025-12', category: '晚餐', amount: 260 },
              { month: '2025-10', category: '超市', amount: 200 },
              { month: '2025-11', category: '超市', amount: 240 },
              { month: '2025-12', category: '超市', amount: 120 },
              { month: '2025-10', category: '教育', amount: 20 },
              { month: '2025-11', category: '教育', amount: 40 },
              { month: '2025-12', category: '教育', amount: 40 }
            ];
            const result = helpers.buildRecentThreeMonthComparison(sample);
            console.log(JSON.stringify(result));
            """
        )
        result = run_node(script)
        self.assertEqual([item['category'] for item in result['categories']], ['旅行', '网购', '晚餐'])
        self.assertEqual(result['latestMonth'], '2025-12')
        self.assertEqual(result['latestMonthTopCategories'], ['旅行', '网购', '晚餐'])

    def test_generate_optimization_suggestions_produces_actionable_advice(self):
        script = textwrap.dedent(
            """
            const helpers = require('./static/monthly-insights.js');
            const sample = [
              { month: '2025-10', category: '旅行', amount: 500 },
              { month: '2025-11', category: '旅行', amount: 900 },
              { month: '2025-12', category: '旅行', amount: 1400 },
              { month: '2025-10', category: '超市', amount: 220 },
              { month: '2025-11', category: '超市', amount: 240 },
              { month: '2025-12', category: '超市', amount: 260 },
              { month: '2025-10', category: '咖啡饮料', amount: 60 },
              { month: '2025-11', category: '咖啡饮料', amount: 80 },
              { month: '2025-12', category: '咖啡饮料', amount: 120 },
              { month: '2025-12', category: '月亮', amount: 5000 }
            ];
            const comparison = helpers.buildRecentThreeMonthComparison(sample);
            const suggestions = helpers.generateOptimizationSuggestions(comparison);
            console.log(JSON.stringify(suggestions));
            """
        )
        suggestions = run_node(script)
        self.assertEqual(len(suggestions), 3)
        combined = ' '.join(suggestions)
        self.assertIn('旅行', combined)
        self.assertIn('预算', combined)
        self.assertTrue('上升' in combined or '增长' in combined)
        self.assertTrue('复盘' in combined or '按周' in combined)
        self.assertNotIn('月亮', combined)

    def test_render_recent_three_month_insights_matches_c_style_summary_and_cards(self):
        script = textwrap.dedent(
            """
            const helpers = require('./static/monthly-insights.js');
            const comparison = helpers.buildRecentThreeMonthComparison([
              { month: '2025-10', category: '旅行', amount: 120 },
              { month: '2025-11', category: '旅行', amount: 220 },
              { month: '2025-12', category: '旅行', amount: 320 },
              { month: '2025-10', category: '网购', amount: 80 },
              { month: '2025-11', category: '网购', amount: 180 },
              { month: '2025-12', category: '网购', amount: 280 },
              { month: '2025-10', category: '晚餐', amount: 60 },
              { month: '2025-11', category: '晚餐', amount: 160 },
              { month: '2025-12', category: '晚餐', amount: 260 },
              { month: '2025-10', category: '超市', amount: 200 },
              { month: '2025-11', category: '超市', amount: 240 },
              { month: '2025-12', category: '超市', amount: 120 }
            ]);

            const store = {};
            const makeNode = (id) => ({ id, innerHTML: '', innerText: '' });
            const document = {
              getElementById(id) {
                if (!store[id]) store[id] = makeNode(id);
                return store[id];
              }
            };

            helpers.renderRecentThreeMonthInsights(comparison, {
              document,
              getCategoryMeta(category) {
                return { name: category, emoji: category === '旅行' ? '✈️' : category === '晚餐' ? '🍽️' : '🛍️', color: '#123456' };
              }
            });

            console.log(JSON.stringify({
              summaryHtml: store.recentThreeMonthSummary.innerHTML,
              comparisonHtml: store.recentThreeMonthComparison.innerHTML
            }));
            """
        )
        result = run_node(script)
        self.assertIn('本月消费重心明显落在旅行、网购、晚餐', result['summaryHtml'])
        self.assertIn('class="insight-rank', result['comparisonHtml'])
        self.assertIn('>Top 1<', result['comparisonHtml'])
        self.assertIn('>Top 2<', result['comparisonHtml'])
        self.assertIn('>Top 3<', result['comparisonHtml'])
        self.assertIn('class="insight-label', result['comparisonHtml'])
        self.assertIn('insight-trend', result['comparisonHtml'])
        self.assertNotIn('持续上升</span><span', result['comparisonHtml'])


if __name__ == '__main__':
    unittest.main()
