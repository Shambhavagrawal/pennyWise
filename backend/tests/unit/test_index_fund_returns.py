from fastapi.testclient import TestClient

from src.main import app
from src.models.challenge import ReturnsInput
from src.services.returns_service import (
    INDEX_RATE,
    NPS_RATE,
    compute_index_returns,
    compute_nps_returns,
)

client = TestClient(app)


def _spec_payload() -> dict:
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


# ---------------------------------------------------------------------------
# Unit tests — rate and tax behavior
# ---------------------------------------------------------------------------


class TestIndexRate:
    def test_index_rate_value(self):
        assert INDEX_RATE == 0.1449

    def test_index_rate_higher_than_nps(self):
        assert INDEX_RATE > NPS_RATE


class TestIndexTaxBenefitAlwaysZero:
    def test_low_income_zero(self):
        payload = ReturnsInput(**_spec_payload())
        result = compute_index_returns(payload)
        for s in result.savingsByDates:
            assert s.taxBenefit == 0.0

    def test_high_income_still_zero(self):
        data = _spec_payload()
        data["wage"] = 200000  # annual = 2.4M (well above tax slabs)
        payload = ReturnsInput(**data)
        result = compute_index_returns(payload)
        for s in result.savingsByDates:
            assert s.taxBenefit == 0.0


# ---------------------------------------------------------------------------
# Unit tests — profit comparison with NPS
# ---------------------------------------------------------------------------


class TestIndexVsNps:
    def test_profit_higher_than_nps(self):
        """Index fund profit should be higher than NPS for same inputs."""
        payload = ReturnsInput(**_spec_payload())
        nps = compute_nps_returns(payload)
        index = compute_index_returns(payload)
        for nps_s, idx_s in zip(nps.savingsByDates, index.savingsByDates, strict=True):
            assert idx_s.profit > nps_s.profit

    def test_totals_match_nps(self):
        """totalTransactionAmount and totalCeiling are identical to NPS."""
        payload = ReturnsInput(**_spec_payload())
        nps = compute_nps_returns(payload)
        index = compute_index_returns(payload)
        assert index.totalTransactionAmount == nps.totalTransactionAmount
        assert index.totalCeiling == nps.totalCeiling

    def test_amounts_match_nps(self):
        """k-period amounts are identical (same pipeline)."""
        payload = ReturnsInput(**_spec_payload())
        nps = compute_nps_returns(payload)
        index = compute_index_returns(payload)
        for nps_s, idx_s in zip(nps.savingsByDates, index.savingsByDates, strict=True):
            assert idx_s.amount == nps_s.amount


# ---------------------------------------------------------------------------
# Unit tests — full pipeline
# ---------------------------------------------------------------------------


class TestComputeIndexReturns:
    def test_total_transaction_amount(self):
        payload = ReturnsInput(**_spec_payload())
        result = compute_index_returns(payload)
        assert result.totalTransactionAmount == 1725.0

    def test_total_ceiling(self):
        payload = ReturnsInput(**_spec_payload())
        result = compute_index_returns(payload)
        assert result.totalCeiling == 1900.0

    def test_savings_by_dates_length(self):
        payload = ReturnsInput(**_spec_payload())
        result = compute_index_returns(payload)
        assert len(result.savingsByDates) == 2

    def test_k0_amount(self):
        payload = ReturnsInput(**_spec_payload())
        result = compute_index_returns(payload)
        assert result.savingsByDates[0].amount == 75.0

    def test_k1_amount(self):
        payload = ReturnsInput(**_spec_payload())
        result = compute_index_returns(payload)
        assert result.savingsByDates[1].amount == 145.0

    def test_k0_profit(self):
        payload = ReturnsInput(**_spec_payload())
        result = compute_index_returns(payload)
        assert result.savingsByDates[0].profit == 871.3

    def test_k1_profit(self):
        payload = ReturnsInput(**_spec_payload())
        result = compute_index_returns(payload)
        assert result.savingsByDates[1].profit == 1684.51

    def test_preserves_k_dates(self):
        payload = ReturnsInput(**_spec_payload())
        result = compute_index_returns(payload)
        assert result.savingsByDates[0].start == "2023-03-01 00:00:00"
        assert result.savingsByDates[1].end == "2023-12-31 23:59:59"

    def test_empty_transactions(self):
        data = _spec_payload()
        data["transactions"] = []
        payload = ReturnsInput(**data)
        result = compute_index_returns(payload)
        assert result.totalTransactionAmount == 0.0
        assert result.totalCeiling == 0.0
        assert result.savingsByDates[0].profit == 0.0


# ---------------------------------------------------------------------------
# Integration tests (HTTP endpoint)
# ---------------------------------------------------------------------------


class TestIndexReturnsEndpoint:
    def test_endpoint_status_200(self):
        resp = client.post("/blackrock/challenge/v1/returns:index", json=_spec_payload())
        assert resp.status_code == 200

    def test_endpoint_field_names(self):
        resp = client.post("/blackrock/challenge/v1/returns:index", json=_spec_payload())
        data = resp.json()
        assert "totalTransactionAmount" in data
        assert "totalCeiling" in data
        assert "savingsByDates" in data
        s = data["savingsByDates"][0]
        assert "profit" in s
        assert "taxBenefit" in s

    def test_endpoint_values(self):
        resp = client.post("/blackrock/challenge/v1/returns:index", json=_spec_payload())
        data = resp.json()
        assert data["totalTransactionAmount"] == 1725.0
        assert data["totalCeiling"] == 1900.0
        assert data["savingsByDates"][1]["profit"] == 1684.51
        assert data["savingsByDates"][1]["taxBenefit"] == 0.0

    def test_endpoint_422_malformed(self):
        resp = client.post("/blackrock/challenge/v1/returns:index", json={"bad": "data"})
        assert resp.status_code == 422
