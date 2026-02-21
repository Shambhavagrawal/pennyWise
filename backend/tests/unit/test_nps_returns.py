from fastapi.testclient import TestClient

from src.main import app
from src.models.challenge import ReturnsInput
from src.services.returns_service import NPS_RATE, compute_nps_returns, compute_tax

client = TestClient(app)


# ---------------------------------------------------------------------------
# Tax slab unit tests
# ---------------------------------------------------------------------------


class TestComputeTax:
    def test_below_7l(self):
        assert compute_tax(600_000) == 0.0

    def test_at_7l_boundary(self):
        assert compute_tax(700_000) == 0.0

    def test_in_10_percent_slab(self):
        # 200k above 7L at 10%
        assert compute_tax(900_000) == 20_000.0

    def test_at_10l_boundary(self):
        # 300k at 10% = 30000
        assert compute_tax(1_000_000) == 30_000.0

    def test_in_15_percent_slab(self):
        # 30000 (10%) + 100k at 15% = 15000 => 45000
        assert compute_tax(1_100_000) == 45_000.0

    def test_at_12l_boundary(self):
        # 30000 + 30000 = 60000
        assert compute_tax(1_200_000) == 60_000.0

    def test_in_20_percent_slab(self):
        # 30000 + 30000 + 200k at 20% = 40000 => 100000
        assert compute_tax(1_400_000) == 100_000.0

    def test_at_15l_boundary(self):
        # 30000 + 30000 + 60000 = 120000
        assert compute_tax(1_500_000) == 120_000.0

    def test_above_15l(self):
        # 30000 + 30000 + 60000 + 500k at 30% = 150000 => 270000
        assert compute_tax(2_000_000) == 270_000.0

    def test_zero_income(self):
        assert compute_tax(0) == 0.0


# ---------------------------------------------------------------------------
# Compound interest / inflation / profit unit tests
# ---------------------------------------------------------------------------


class TestCompoundInterestAndProfit:
    def test_investment_period_young(self):
        """age 29 -> t = 31"""
        t = max(60 - 29, 5)
        assert t == 31

    def test_investment_period_at_60(self):
        """age 60 -> t = 5 (minimum)"""
        t = max(60 - 60, 5)
        assert t == 5

    def test_investment_period_over_60(self):
        """age 75 -> t = 5 (minimum)"""
        t = max(60 - 75, 5)
        assert t == 5

    def test_compound_interest_nps(self):
        """Verify A = P * (1.0711)^t for known values."""
        amount = 100.0
        t = 10
        a = amount * (1 + NPS_RATE) ** t
        expected = 100.0 * (1.0711**10)
        assert abs(a - expected) < 1e-6

    def test_inflation_adjustment(self):
        """Verify A_real = A / (1.055)^t."""
        a = 200.0
        t = 10
        inflation = 5.5
        a_real = a / (1 + inflation / 100) ** t
        expected = 200.0 / (1.055**10)
        assert abs(a_real - expected) < 1e-6

    def test_profit_pinned_k1(self):
        """Pinned precision test: k[1] amount=145, age=29 (t=31), inflation=5.5 → profit=86.88."""
        amount = 145.0
        t = 31
        inflation = 5.5
        a = amount * (1 + NPS_RATE) ** t
        a_real = a / (1 + inflation / 100) ** t
        profit = round(a_real - amount, 2)
        assert profit == 86.88

    def test_profit_age_60(self):
        """Age 60 → t=5, verify returns are smaller."""
        amount = 100.0
        t = 5
        inflation = 5.0
        a = amount * (1 + NPS_RATE) ** t
        a_real = a / (1 + inflation / 100) ** t
        profit = round(a_real - amount, 2)
        assert profit == 10.46


# ---------------------------------------------------------------------------
# NPS deduction and tax benefit tests
# ---------------------------------------------------------------------------


class TestNpsDeductionAndTaxBenefit:
    def test_deduction_limited_by_amount(self):
        """When amount < 10% annual and < 200000, deduction = amount."""
        k_amount = 100.0
        annual = 600_000
        deduction = min(k_amount, 0.10 * annual, 200_000)
        assert deduction == 100.0

    def test_deduction_limited_by_10_percent(self):
        """When 10% annual is the smallest."""
        k_amount = 500_000.0
        annual = 600_000  # 10% = 60000
        deduction = min(k_amount, 0.10 * annual, 200_000)
        assert deduction == 60_000.0

    def test_deduction_limited_by_200k_cap(self):
        """When 200000 cap is the smallest."""
        k_amount = 500_000.0
        annual = 3_000_000  # 10% = 300000
        deduction = min(k_amount, 0.10 * annual, 200_000)
        assert deduction == 200_000.0

    def test_tax_benefit_low_income_zero(self):
        """Income below 7L → tax benefit is 0 regardless of deduction."""
        income = 600_000
        deduction = 145.0
        benefit = compute_tax(income) - compute_tax(income - deduction)
        assert benefit == 0.0

    def test_tax_benefit_high_income(self):
        """Income 1200000 with large deduction → real tax savings."""
        income = 1_200_000
        deduction = 50_000.0
        # Tax(1200000) = 60000
        # Tax(1150000) = 30000 + (150000*0.15) = 30000 + 22500 = 52500
        benefit = compute_tax(income) - compute_tax(income - deduction)
        assert benefit == 7_500.0


# ---------------------------------------------------------------------------
# Full pipeline service tests
# ---------------------------------------------------------------------------


class TestComputeNpsReturns:
    def _spec_payload(self) -> dict:
        """Standard spec example payload."""
        return {
            "age": 29,
            "wage": 50000,
            "inflation": 5.5,
            "q": [
                {
                    "fixed": 0,
                    "start": "2023-07-01 00:00:00",
                    "end": "2023-07-31 23:59:59",
                }
            ],
            "p": [
                {
                    "extra": 25,
                    "start": "2023-10-01 08:00:00",
                    "end": "2023-12-31 19:59:59",
                }
            ],
            "k": [
                {
                    "start": "2023-03-01 00:00:00",
                    "end": "2023-11-30 23:59:59",
                },
                {
                    "start": "2023-01-01 00:00:00",
                    "end": "2023-12-31 23:59:59",
                },
            ],
            "transactions": [
                {"date": "2023-10-12 14:23:00", "amount": 250},
                {"date": "2023-02-28 09:15:00", "amount": 375},
                {"date": "2023-07-01 12:00:00", "amount": 620},
                {"date": "2023-12-17 18:30:00", "amount": 480},
            ],
        }

    def test_total_transaction_amount(self):
        """totalTransactionAmount includes ALL valid txns (before zero-remanent removal)."""
        payload = ReturnsInput(**self._spec_payload())
        result = compute_nps_returns(payload)
        # 250 + 375 + 620 + 480 = 1725
        assert result.totalTransactionAmount == 1725.0

    def test_total_ceiling(self):
        """totalCeiling includes ALL valid txns (before zero-remanent removal)."""
        payload = ReturnsInput(**self._spec_payload())
        result = compute_nps_returns(payload)
        # 300 + 400 + 700 + 500 = 1900
        assert result.totalCeiling == 1900.0

    def test_savings_by_dates_length(self):
        """savingsByDates has same length as k input array."""
        payload = ReturnsInput(**self._spec_payload())
        result = compute_nps_returns(payload)
        assert len(result.savingsByDates) == 2

    def test_savings_preserves_k_dates(self):
        """savingsByDates preserves start/end strings from k input."""
        payload = ReturnsInput(**self._spec_payload())
        result = compute_nps_returns(payload)
        assert result.savingsByDates[0].start == "2023-03-01 00:00:00"
        assert result.savingsByDates[0].end == "2023-11-30 23:59:59"
        assert result.savingsByDates[1].start == "2023-01-01 00:00:00"
        assert result.savingsByDates[1].end == "2023-12-31 23:59:59"

    def test_k0_amount(self):
        """k[0] (Mar-Nov) captures only Oct's adjusted remanent=75."""
        payload = ReturnsInput(**self._spec_payload())
        result = compute_nps_returns(payload)
        assert result.savingsByDates[0].amount == 75.0

    def test_k1_amount(self):
        """k[1] (Jan-Dec) captures Feb(25) + Oct(75) + Dec(45) = 145."""
        payload = ReturnsInput(**self._spec_payload())
        result = compute_nps_returns(payload)
        assert result.savingsByDates[1].amount == 145.0

    def test_pinned_profit_k1(self):
        """PINNED: k[1] profit MUST equal exactly 86.88."""
        payload = ReturnsInput(**self._spec_payload())
        result = compute_nps_returns(payload)
        assert result.savingsByDates[1].profit == 86.88

    def test_tax_benefit_spec_example(self):
        """Wage=50000 → annual=600000 (below 7L) → taxBenefit=0."""
        payload = ReturnsInput(**self._spec_payload())
        result = compute_nps_returns(payload)
        assert result.savingsByDates[0].taxBenefit == 0.0
        assert result.savingsByDates[1].taxBenefit == 0.0

    def test_negative_transactions_excluded(self):
        """Negative amounts are excluded from totals and processing."""
        data = self._spec_payload()
        data["transactions"].append({"date": "2023-05-01 10:00:00", "amount": -100})
        payload = ReturnsInput(**data)
        result = compute_nps_returns(payload)
        # Totals should remain unchanged (negative excluded)
        assert result.totalTransactionAmount == 1725.0

    def test_duplicate_transactions_excluded(self):
        """Duplicate dates are excluded from totals and processing."""
        data = self._spec_payload()
        data["transactions"].append({"date": "2023-10-12 14:23:00", "amount": 999})
        payload = ReturnsInput(**data)
        result = compute_nps_returns(payload)
        assert result.totalTransactionAmount == 1725.0

    def test_empty_transactions(self):
        """Empty transactions → zero totals and zero-amount k periods."""
        data = self._spec_payload()
        data["transactions"] = []
        payload = ReturnsInput(**data)
        result = compute_nps_returns(payload)
        assert result.totalTransactionAmount == 0.0
        assert result.totalCeiling == 0.0
        assert len(result.savingsByDates) == 2
        assert result.savingsByDates[0].amount == 0.0
        assert result.savingsByDates[0].profit == 0.0

    def test_high_income_tax_benefit(self):
        """High wage produces non-zero tax benefit."""
        data = self._spec_payload()
        data["wage"] = 150000  # annual = 1800000
        # Remove q so remanents stay high, remove p to simplify
        data["q"] = []
        data["p"] = []
        payload = ReturnsInput(**data)
        result = compute_nps_returns(payload)
        # k[1] covers all transactions, total remanent = 50+25+80+20 = 175
        # deduction = min(175, 0.10*1800000=180000, 200000) = 175
        # Tax(1800000) - Tax(1800000-175) > 0 since income > 15L → 30% marginal
        assert result.savingsByDates[1].taxBenefit > 0


# ---------------------------------------------------------------------------
# Integration tests (HTTP endpoint)
# ---------------------------------------------------------------------------


class TestNpsReturnsEndpoint:
    def _spec_payload(self) -> dict:
        return {
            "age": 29,
            "wage": 50000,
            "inflation": 5.5,
            "q": [
                {
                    "fixed": 0,
                    "start": "2023-07-01 00:00:00",
                    "end": "2023-07-31 23:59:59",
                }
            ],
            "p": [
                {
                    "extra": 25,
                    "start": "2023-10-01 08:00:00",
                    "end": "2023-12-31 19:59:59",
                }
            ],
            "k": [
                {
                    "start": "2023-03-01 00:00:00",
                    "end": "2023-11-30 23:59:59",
                },
                {
                    "start": "2023-01-01 00:00:00",
                    "end": "2023-12-31 23:59:59",
                },
            ],
            "transactions": [
                {"date": "2023-10-12 14:23:00", "amount": 250},
                {"date": "2023-02-28 09:15:00", "amount": 375},
                {"date": "2023-07-01 12:00:00", "amount": 620},
                {"date": "2023-12-17 18:30:00", "amount": 480},
            ],
        }

    def test_endpoint_status_200(self):
        resp = client.post("/blackrock/challenge/v1/returns:nps", json=self._spec_payload())
        assert resp.status_code == 200

    def test_endpoint_field_names(self):
        """Day-one smoke test: verify field names in response JSON."""
        resp = client.post("/blackrock/challenge/v1/returns:nps", json=self._spec_payload())
        data = resp.json()
        assert "totalTransactionAmount" in data
        assert "totalCeiling" in data
        assert "savingsByDates" in data
        s = data["savingsByDates"][0]
        assert "start" in s
        assert "end" in s
        assert "amount" in s
        assert "profit" in s
        assert "taxBenefit" in s

    def test_endpoint_spec_example_values(self):
        resp = client.post("/blackrock/challenge/v1/returns:nps", json=self._spec_payload())
        data = resp.json()
        assert data["totalTransactionAmount"] == 1725.0
        assert data["totalCeiling"] == 1900.0
        assert data["savingsByDates"][1]["amount"] == 145.0
        assert data["savingsByDates"][1]["profit"] == 86.88

    def test_endpoint_422_malformed(self):
        resp = client.post("/blackrock/challenge/v1/returns:nps", json={"bad": "data"})
        assert resp.status_code == 422
