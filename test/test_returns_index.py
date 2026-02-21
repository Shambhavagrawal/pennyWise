# Test Type: Unit Test
# Validation: Index fund returns with 14.49% rate and zero tax benefit
# Command: pytest test/test_returns_index.py -v

from src.models.challenge import ReturnsInput
from src.services.returns_service import (
    INDEX_RATE,
    NPS_RATE,
    compute_index_returns,
    compute_nps_returns,
)


def _spec_payload():
    return {
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
    }


class TestIndexRate:
    def test_uses_higher_rate(self):
        assert INDEX_RATE == 0.1449
        assert INDEX_RATE > NPS_RATE


class TestIndexTaxBenefit:
    def test_always_zero(self):
        payload = ReturnsInput(**_spec_payload())
        result = compute_index_returns(payload)
        for s in result.savingsByDates:
            assert s.taxBenefit == 0.0


class TestIndexVsNps:
    def test_profit_higher(self):
        payload = ReturnsInput(**_spec_payload())
        nps = compute_nps_returns(payload)
        index = compute_index_returns(payload)
        for n, i in zip(nps.savingsByDates, index.savingsByDates, strict=True):
            assert i.profit > n.profit

    def test_totals_identical(self):
        payload = ReturnsInput(**_spec_payload())
        nps = compute_nps_returns(payload)
        index = compute_index_returns(payload)
        assert index.totalTransactionAmount == nps.totalTransactionAmount
        assert index.totalCeiling == nps.totalCeiling


class TestIndexIntegration:
    def test_endpoint(self, client):
        resp = client.post("/blackrock/challenge/v1/returns:index", json=_spec_payload())
        assert resp.status_code == 200
        data = resp.json()
        assert data["totalTransactionAmount"] == 1725.0
        assert data["savingsByDates"][1]["taxBenefit"] == 0.0
