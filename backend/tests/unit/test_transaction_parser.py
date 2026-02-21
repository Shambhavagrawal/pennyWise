import pytest

from src.models.challenge import ExpenseInput, compute_ceiling, compute_remanent
from src.services.transaction_service import parse_transactions


class TestCeilingComputation:
    def test_normal_amount(self):
        assert compute_ceiling(250) == 300.0

    def test_exact_multiple_of_100(self):
        assert compute_ceiling(300) == 300.0

    def test_zero(self):
        assert compute_ceiling(0) == 0.0

    def test_small_amount(self):
        assert compute_ceiling(1) == 100.0

    def test_large_amount(self):
        assert compute_ceiling(999) == 1000.0

    def test_amount_620(self):
        assert compute_ceiling(620) == 700.0


class TestRemanentComputation:
    def test_normal(self):
        assert compute_remanent(250, 300) == 50.0

    def test_exact_multiple(self):
        assert compute_remanent(300, 300) == 0.0

    def test_zero(self):
        assert compute_remanent(0, 0) == 0.0

    def test_small(self):
        assert compute_remanent(1, 100) == 99.0


class TestParseTransactions:
    def test_spec_example(self):
        expenses = [
            ExpenseInput(date="2023-10-12 14:23:00", amount=250),
            ExpenseInput(date="2023-02-28 09:15:00", amount=375),
            ExpenseInput(date="2023-07-01 11:30:00", amount=620),
            ExpenseInput(date="2023-12-17 16:45:00", amount=480),
        ]
        results = parse_transactions(expenses)
        assert len(results) == 4
        assert results[0].ceiling == 300.0
        assert results[0].remanent == 50.0
        assert results[1].ceiling == 400.0
        assert results[1].remanent == 25.0
        assert results[2].ceiling == 700.0
        assert results[2].remanent == 80.0
        assert results[3].ceiling == 500.0
        assert results[3].remanent == 20.0

    def test_empty_list(self):
        assert parse_transactions([]) == []

    def test_preserves_date_string(self):
        expenses = [ExpenseInput(date="2023-11-31 00:00:00", amount=100)]
        results = parse_transactions(expenses)
        assert results[0].date == "2023-11-31 00:00:00"

    def test_single_item(self):
        expenses = [ExpenseInput(date="2023-01-01", amount=450)]
        results = parse_transactions(expenses)
        assert len(results) == 1
        assert results[0].ceiling == 500.0
        assert results[0].remanent == 50.0


class TestParseEndpoint:
    @pytest.mark.api
    async def test_parse_spec_example(self, client):
        response = await client.post(
            "/blackrock/challenge/v1/transactions:parse",
            json=[
                {"date": "2023-10-12 14:23:00", "amount": 250},
                {"date": "2023-02-28 09:15:00", "amount": 375},
                {"date": "2023-07-01 11:30:00", "amount": 620},
                {"date": "2023-12-17 16:45:00", "amount": 480},
            ],
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4
        assert data[0] == {
            "date": "2023-10-12 14:23:00",
            "amount": 250.0,
            "ceiling": 300.0,
            "remanent": 50.0,
        }

    @pytest.mark.api
    async def test_parse_empty_list(self, client):
        response = await client.post(
            "/blackrock/challenge/v1/transactions:parse",
            json=[],
        )
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.api
    async def test_parse_edge_cases(self, client):
        response = await client.post(
            "/blackrock/challenge/v1/transactions:parse",
            json=[
                {"date": "2023-01-01", "amount": 300},
                {"date": "2023-01-02", "amount": 0},
            ],
        )
        assert response.status_code == 200
        data = response.json()
        assert data[0]["ceiling"] == 300.0
        assert data[0]["remanent"] == 0.0
        assert data[1]["ceiling"] == 0.0
        assert data[1]["remanent"] == 0.0
