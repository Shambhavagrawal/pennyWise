# Test Type: Unit Test
# Validation: Ceiling/remanent calculation for expense round-up
# Command: pytest test/test_parse.py -v

from src.models.challenge import compute_ceiling, compute_remanent
from src.services.transaction_service import parse_transactions
from src.models.challenge import ExpenseInput


class TestCeilingRemanent:
    def test_normal_amount(self):
        assert compute_ceiling(250) == 300
        assert compute_remanent(250, 300) == 50

    def test_exact_multiple(self):
        assert compute_ceiling(300) == 300
        assert compute_remanent(300, 300) == 0

    def test_zero(self):
        assert compute_ceiling(0) == 0
        assert compute_remanent(0, 0) == 0

    def test_large_amount(self):
        assert compute_ceiling(999) == 1000
        assert compute_remanent(999, 1000) == 1

    def test_small_amount(self):
        assert compute_ceiling(1) == 100
        assert compute_remanent(1, 100) == 99


class TestParseIntegration:
    def test_spec_example(self, client):
        resp = client.post(
            "/blackrock/challenge/v1/transactions:parse",
            json=[
                {"date": "2023-10-12 14:23:00", "amount": 250},
                {"date": "2023-02-28 09:15:00", "amount": 375},
                {"date": "2023-07-01 12:00:00", "amount": 620},
                {"date": "2023-12-17 18:30:00", "amount": 480},
            ],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 4
        assert data[0] == {"date": "2023-10-12 14:23:00", "amount": 250.0, "ceiling": 300.0, "remanent": 50.0}

    def test_empty_array(self, client):
        resp = client.post("/blackrock/challenge/v1/transactions:parse", json=[])
        assert resp.status_code == 200
        assert resp.json() == []
