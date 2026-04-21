from decimal import Decimal
import os
import tempfile
import unittest
from pathlib import Path

DB_FILE = Path(tempfile.gettempdir()) / 'gpt_accounting_test.db'
os.environ['DATABASE_URL'] = f'sqlite:///{DB_FILE}'
os.environ['ALLOWED_ORIGINS'] = 'http://localhost:8000'

from fastapi.testclient import TestClient
import main


class ApiBehaviorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        main.Base.metadata.drop_all(bind=main.engine)
        main.Base.metadata.create_all(bind=main.engine)
        cls.client = TestClient(main.app)

    def setUp(self):
        main.Base.metadata.drop_all(bind=main.engine)
        main.Base.metadata.create_all(bind=main.engine)

    def test_month_data_is_computed_from_expenses(self):
        payloads = [
            {"date": "2026-04-01", "amount": 10, "category": "早餐"},
            {"date": "2026-04-03", "amount": 15.5, "category": "早餐"},
            {"date": "2026-04-05", "amount": 88, "category": "水电费"},
        ]
        for payload in payloads:
            response = self.client.post('/expenses/', json=payload)
            self.assertEqual(response.status_code, 200)

        response = self.client.get('/monthData?month=2026-04')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [
                {'month': '2026-04', 'category': '早餐', 'amount': '25.50'},
                {'month': '2026-04', 'category': '水电费', 'amount': '88.00'},
            ],
        )

    def test_invalid_month_returns_400(self):
        response = self.client.get('/monthData?month=2026-99')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['detail'], 'Bad month')

    def test_create_expense_round_trips_currency_as_two_decimal_places(self):
        payload = {"date": "2026-04-01", "amount": "1.005", "category": "早餐"}

        create_response = self.client.post('/expenses/', json=payload)
        self.assertEqual(create_response.status_code, 200)
        self.assertEqual(create_response.json()['amount'], '1.01')

        read_response = self.client.get('/expenses?date=2026-04-01')
        self.assertEqual(read_response.status_code, 200)
        self.assertEqual(read_response.json()[0]['amount'], '1.01')

        month_response = self.client.get('/monthData?month=2026-04')
        self.assertEqual(month_response.status_code, 200)
        self.assertEqual(
            month_response.json(),
            [
                {'month': '2026-04', 'category': '早餐', 'amount': '1.01'},
            ],
        )

    def test_amount_is_stored_as_decimal_in_database_session(self):
        payload = {"date": "2026-04-01", "amount": "12.30", "category": "早餐"}
        response = self.client.post('/expenses/', json=payload)
        self.assertEqual(response.status_code, 200)

        with main.SessionLocal() as db:
            expense = db.query(main.Expense).one()
            self.assertIsInstance(expense.amount, Decimal)
            self.assertEqual(expense.amount, Decimal('12.30'))


if __name__ == '__main__':
    unittest.main()
