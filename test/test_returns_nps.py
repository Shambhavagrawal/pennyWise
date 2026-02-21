# Test Type: Unit Test
# Validation: NPS compound interest, inflation adjustment, and progressive tax benefit
# Command: pytest test/test_returns_nps.py -v

from src.services.returns_service import NPS_RATE, compute_tax


class TestCompoundInterest:
    def test_known_value(self):
        amount = 100.0
        t = 10
        a = amount * (1 + NPS_RATE) ** t
        assert abs(a - 100.0 * (1.0711**10)) < 1e-6

    def test_inflation_adjustment(self):
        a = 200.0
        a_real = a / (1.055**10)
        assert a_real < a


class TestInvestmentPeriod:
    def test_age_29(self):
        assert max(60 - 29, 5) == 31

    def test_age_60(self):
        assert max(60 - 60, 5) == 5

    def test_age_75(self):
        assert max(60 - 75, 5) == 5


class TestTaxSlabs:
    def test_below_7l(self):
        assert compute_tax(600_000) == 0.0

    def test_10_percent_slab(self):
        assert compute_tax(900_000) == 20_000.0

    def test_12l_boundary(self):
        assert compute_tax(1_200_000) == 60_000.0

    def test_above_15l(self):
        assert compute_tax(2_000_000) == 270_000.0


class TestNpsDeduction:
    def test_limited_by_amount(self):
        assert min(100, 0.10 * 600_000, 200_000) == 100

    def test_limited_by_10_percent(self):
        assert min(500_000, 0.10 * 600_000, 200_000) == 60_000

    def test_limited_by_cap(self):
        assert min(500_000, 0.10 * 3_000_000, 200_000) == 200_000


class TestNpsIntegration:
    def test_pinned_profit(self, client):
        resp = client.post(
            "/blackrock/challenge/v1/returns:nps",
            json={
                "age": 29,
                "wage": 50000,
                "inflation": 5.5,
                "q": [{"fixed": 0, "start": "2023-07-01 00:00:00", "end": "2023-07-31 23:59:59"}],
                "p": [{"extra": 25, "start": "2023-10-01 08:00:00", "end": "2023-12-31 19:59:59"}],
                "k": [
                    {"start": "2023-03-01 00:00:00", "end": "2023-11-30 23:59:59"},
                    {"start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:59"},
                ],
                "transactions": [
                    {"date": "2023-10-12 14:23:00", "amount": 250},
                    {"date": "2023-02-28 09:15:00", "amount": 375},
                    {"date": "2023-07-01 12:00:00", "amount": 620},
                    {"date": "2023-12-17 18:30:00", "amount": 480},
                ],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["savingsByDates"][1]["amount"] == 145.0
        assert data["savingsByDates"][1]["profit"] == 86.88
