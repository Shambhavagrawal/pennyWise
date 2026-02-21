import pytest

from src.models.challenge import (
    ExpenseInput,
    FilterInput,
    KPeriod,
    PPeriod,
    QPeriod,
)
from src.services.transaction_service import filter_transactions


def _build_input(
    transactions: list[dict],
    q: list[dict] | None = None,
    p: list[dict] | None = None,
    k: list[dict] | None = None,
    wage: float = 50000,
) -> FilterInput:
    return FilterInput(
        q=[QPeriod(**item) for item in (q or [])],
        p=[PPeriod(**item) for item in (p or [])],
        k=[KPeriod(**item) for item in (k or [])],
        wage=wage,
        transactions=[ExpenseInput(**t) for t in transactions],
    )


class TestQPeriod:
    def test_q_single_match(self):
        payload = _build_input(
            transactions=[{"date": "2023-07-15 10:00:00", "amount": 250}],
            q=[{"fixed": 100, "start": "2023-07-01 00:00:00", "end": "2023-07-31 23:59:59"}],
        )
        result = filter_transactions(payload)
        assert len(result.valid) == 1
        assert result.valid[0].remanent == 100

    def test_q_no_match(self):
        payload = _build_input(
            transactions=[{"date": "2023-06-15 10:00:00", "amount": 250}],
            q=[{"fixed": 100, "start": "2023-07-01 00:00:00", "end": "2023-07-31 23:59:59"}],
        )
        result = filter_transactions(payload)
        assert len(result.valid) == 1
        # Original remanent: ceiling(250)=300, remanent=50
        assert result.valid[0].remanent == 50

    def test_q_multiple_latest_start(self):
        payload = _build_input(
            transactions=[{"date": "2023-07-15 10:00:00", "amount": 250}],
            q=[
                {"fixed": 10, "start": "2023-06-01 00:00:00", "end": "2023-08-31 23:59:59"},
                {"fixed": 99, "start": "2023-07-01 00:00:00", "end": "2023-07-31 23:59:59"},
            ],
        )
        result = filter_transactions(payload)
        assert len(result.valid) == 1
        # Second q has later start → wins
        assert result.valid[0].remanent == 99

    def test_q_tiebreak_list_order(self):
        payload = _build_input(
            transactions=[{"date": "2023-07-15 10:00:00", "amount": 250}],
            q=[
                {"fixed": 11, "start": "2023-07-01 00:00:00", "end": "2023-07-31 23:59:59"},
                {"fixed": 22, "start": "2023-07-01 00:00:00", "end": "2023-07-31 23:59:59"},
            ],
        )
        result = filter_transactions(payload)
        assert len(result.valid) == 1
        # Same start → first in list wins
        assert result.valid[0].remanent == 11


class TestPPeriod:
    def test_p_single_match(self):
        payload = _build_input(
            transactions=[{"date": "2023-10-15 10:00:00", "amount": 250}],
            p=[{"extra": 25, "start": "2023-10-01 00:00:00", "end": "2023-12-31 23:59:59"}],
        )
        result = filter_transactions(payload)
        assert len(result.valid) == 1
        # remanent = 50 + 25 = 75
        assert result.valid[0].remanent == 75

    def test_p_multiple_accumulate(self):
        payload = _build_input(
            transactions=[{"date": "2023-10-15 10:00:00", "amount": 250}],
            p=[
                {"extra": 25, "start": "2023-10-01 00:00:00", "end": "2023-12-31 23:59:59"},
                {"extra": 10, "start": "2023-09-01 00:00:00", "end": "2023-11-30 23:59:59"},
            ],
        )
        result = filter_transactions(payload)
        assert len(result.valid) == 1
        # remanent = 50 + 25 + 10 = 85
        assert result.valid[0].remanent == 85


class TestQThenP:
    def test_q_then_p(self):
        payload = _build_input(
            transactions=[{"date": "2023-07-15 10:00:00", "amount": 250}],
            q=[{"fixed": 30, "start": "2023-07-01 00:00:00", "end": "2023-07-31 23:59:59"}],
            p=[{"extra": 15, "start": "2023-07-01 00:00:00", "end": "2023-07-31 23:59:59"}],
        )
        result = filter_transactions(payload)
        assert len(result.valid) == 1
        # q replaces remanent with 30, then p adds 15 → 45
        assert result.valid[0].remanent == 45


class TestKPeriod:
    def test_k_in_period(self):
        payload = _build_input(
            transactions=[{"date": "2023-07-15 10:00:00", "amount": 250}],
            k=[{"start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:59"}],
        )
        result = filter_transactions(payload)
        assert len(result.valid) == 1
        assert result.valid[0].inkPeriod is True

    def test_k_not_in_period(self):
        payload = _build_input(
            transactions=[{"date": "2023-07-15 10:00:00", "amount": 250}],
            k=[{"start": "2024-01-01 00:00:00", "end": "2024-12-31 23:59:59"}],
        )
        result = filter_transactions(payload)
        assert len(result.valid) == 1
        assert result.valid[0].inkPeriod is False

    def test_ink_period_only_k_periods(self):
        """inkPeriod is determined solely by k periods, not q or p."""
        payload = _build_input(
            transactions=[{"date": "2023-07-15 10:00:00", "amount": 250}],
            q=[{"fixed": 30, "start": "2023-07-01 00:00:00", "end": "2023-07-31 23:59:59"}],
            p=[{"extra": 15, "start": "2023-07-01 00:00:00", "end": "2023-07-31 23:59:59"}],
            k=[],
        )
        result = filter_transactions(payload)
        assert len(result.valid) == 1
        assert result.valid[0].inkPeriod is False


class TestFilterValidation:
    def test_filter_negative(self):
        payload = _build_input(
            transactions=[{"date": "2023-07-15 10:00:00", "amount": -100}],
        )
        result = filter_transactions(payload)
        assert len(result.valid) == 0
        assert len(result.invalid) == 1
        assert result.invalid[0].message == "Negative amounts are not allowed"

    def test_filter_duplicate(self):
        payload = _build_input(
            transactions=[
                {"date": "2023-07-15 10:00:00", "amount": 250},
                {"date": "2023-07-15 10:00:00", "amount": 300},
            ],
        )
        result = filter_transactions(payload)
        assert len(result.valid) == 1
        assert len(result.invalid) == 1
        assert result.invalid[0].message == "Duplicate transaction"

    def test_filter_computes_ceiling(self):
        payload = _build_input(
            transactions=[{"date": "2023-07-15 10:00:00", "amount": 250}],
        )
        result = filter_transactions(payload)
        assert result.valid[0].ceiling == 300
        assert result.valid[0].remanent == 50


class TestZeroRemanent:
    def test_filter_omits_zero_remanent(self):
        payload = _build_input(
            transactions=[{"date": "2023-07-15 10:00:00", "amount": 300}],
        )
        # amount=300, ceiling=300, remanent=0 → omitted
        result = filter_transactions(payload)
        assert len(result.valid) == 0
        assert len(result.invalid) == 0

    def test_filter_omits_zero_remanent_after_q(self):
        payload = _build_input(
            transactions=[{"date": "2023-07-15 10:00:00", "amount": 250}],
            q=[{"fixed": 0, "start": "2023-07-01 00:00:00", "end": "2023-07-31 23:59:59"}],
        )
        # remanent replaced with 0 by q → omitted
        result = filter_transactions(payload)
        assert len(result.valid) == 0
        assert len(result.invalid) == 0


class TestSpecExample:
    def test_full_spec_example(self):
        payload = _build_input(
            transactions=[
                {"date": "2023-10-12 14:23:00", "amount": 250},
                {"date": "2023-02-28 09:15:00", "amount": 375},
                {"date": "2023-07-01 12:00:00", "amount": 620},
                {"date": "2023-12-17 18:30:00", "amount": 480},
            ],
            q=[{"fixed": 0, "start": "2023-07-01 00:00:00", "end": "2023-07-31 23:59:59"}],
            p=[{"extra": 25, "start": "2023-10-01 08:00:00", "end": "2023-12-31 19:59:59"}],
            k=[
                {"start": "2023-03-01 00:00:00", "end": "2023-11-30 23:59:59"},
                {"start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:59"},
            ],
            wage=50000,
        )
        result = filter_transactions(payload)

        assert len(result.invalid) == 0
        assert len(result.valid) == 3

        # Oct: ceiling=300, remanent=50+25=75
        assert result.valid[0].date == "2023-10-12 14:23:00"
        assert result.valid[0].amount == 250.0
        assert result.valid[0].ceiling == 300.0
        assert result.valid[0].remanent == 75.0
        assert result.valid[0].inkPeriod is True

        # Feb: ceiling=400, remanent=25 (no q/p match)
        assert result.valid[1].date == "2023-02-28 09:15:00"
        assert result.valid[1].amount == 375.0
        assert result.valid[1].ceiling == 400.0
        assert result.valid[1].remanent == 25.0
        assert result.valid[1].inkPeriod is True

        # Dec: ceiling=500, remanent=20+25=45
        assert result.valid[2].date == "2023-12-17 18:30:00"
        assert result.valid[2].amount == 480.0
        assert result.valid[2].ceiling == 500.0
        assert result.valid[2].remanent == 45.0
        assert result.valid[2].inkPeriod is True

    def test_preserves_invalid_date_string(self):
        """Original date strings are preserved, even invalid ones like 2023-11-31."""
        payload = _build_input(
            transactions=[{"date": "2023-11-31 10:00:00", "amount": 250}],
        )
        result = filter_transactions(payload)
        assert result.valid[0].date == "2023-11-31 10:00:00"


class TestFilterEndpoint:
    @pytest.mark.api
    async def test_filter_returns_valid_and_invalid(self, client):
        response = await client.post(
            "/blackrock/challenge/v1/transactions:filter",
            json={
                "q": [],
                "p": [],
                "k": [],
                "wage": 50000,
                "transactions": [
                    {"date": "2023-10-12 14:23:00", "amount": 250},
                    {"date": "2023-10-12 14:23:00", "amount": 300},
                    {"date": "2023-05-01 10:00:00", "amount": -50},
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["valid"]) == 1
        assert len(data["invalid"]) == 2

    @pytest.mark.api
    async def test_filter_empty_transactions(self, client):
        response = await client.post(
            "/blackrock/challenge/v1/transactions:filter",
            json={
                "q": [],
                "p": [],
                "k": [],
                "wage": 50000,
                "transactions": [],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == []
        assert data["invalid"] == []

    @pytest.mark.api
    async def test_filter_all_negatives(self, client):
        response = await client.post(
            "/blackrock/challenge/v1/transactions:filter",
            json={
                "q": [],
                "p": [],
                "k": [],
                "wage": 50000,
                "transactions": [
                    {"date": "2023-01-01 10:00:00", "amount": -100},
                    {"date": "2023-02-01 10:00:00", "amount": -200},
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["valid"]) == 0
        assert len(data["invalid"]) == 2

    @pytest.mark.api
    async def test_filter_spec_example_integration(self, client):
        response = await client.post(
            "/blackrock/challenge/v1/transactions:filter",
            json={
                "q": [{"fixed": 0, "start": "2023-07-01 00:00:00", "end": "2023-07-31 23:59:59"}],
                "p": [{"extra": 25, "start": "2023-10-01 08:00:00", "end": "2023-12-31 19:59:59"}],
                "k": [
                    {"start": "2023-03-01 00:00:00", "end": "2023-11-30 23:59:59"},
                    {"start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:59"},
                ],
                "wage": 50000,
                "transactions": [
                    {"date": "2023-10-12 14:23:00", "amount": 250},
                    {"date": "2023-02-28 09:15:00", "amount": 375},
                    {"date": "2023-07-01 12:00:00", "amount": 620},
                    {"date": "2023-12-17 18:30:00", "amount": 480},
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["valid"]) == 3
        assert len(data["invalid"]) == 0
        # July transaction (remanent=0 after q) is omitted
        dates = [t["date"] for t in data["valid"]]
        assert "2023-07-01 12:00:00" not in dates
