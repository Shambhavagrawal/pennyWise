# Test Type: Unit Test
# Validation: q/p/k period rules application and interaction
# Command: pytest test/test_filter.py -v

from src.models.challenge import FilterInput
from src.services.transaction_service import filter_transactions


def _payload(**overrides):
    base = {
        "q": [],
        "p": [],
        "k": [],
        "wage": 50000,
        "transactions": [{"date": "2023-10-12 14:23:00", "amount": 250}],
    }
    base.update(overrides)
    return FilterInput(**base)


class TestQPeriod:
    def test_q_replaces_remanent(self):
        payload = _payload(q=[{"fixed": 10, "start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:59"}])
        result = filter_transactions(payload)
        assert result.valid[0].remanent == 10

    def test_q_latest_start_wins(self):
        payload = _payload(
            q=[
                {"fixed": 10, "start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:59"},
                {"fixed": 99, "start": "2023-06-01 00:00:00", "end": "2023-12-31 23:59:59"},
            ]
        )
        result = filter_transactions(payload)
        assert result.valid[0].remanent == 99

    def test_q_tiebreak_first_in_list(self):
        payload = _payload(
            q=[
                {"fixed": 11, "start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:59"},
                {"fixed": 22, "start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:59"},
            ]
        )
        result = filter_transactions(payload)
        assert result.valid[0].remanent == 11


class TestPPeriod:
    def test_p_adds_extra(self):
        payload = _payload(p=[{"extra": 25, "start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:59"}])
        result = filter_transactions(payload)
        # base remanent = 50 (250 -> ceiling 300), + 25 = 75
        assert result.valid[0].remanent == 75

    def test_p_multiple_accumulate(self):
        payload = _payload(
            p=[
                {"extra": 10, "start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:59"},
                {"extra": 20, "start": "2023-06-01 00:00:00", "end": "2023-12-31 23:59:59"},
            ]
        )
        result = filter_transactions(payload)
        assert result.valid[0].remanent == 80  # 50 + 10 + 20


class TestQThenP:
    def test_q_then_p_order(self):
        payload = _payload(
            q=[{"fixed": 0, "start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:59"}],
            p=[{"extra": 25, "start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:59"}],
        )
        result = filter_transactions(payload)
        # q sets to 0, then p adds 25 = 25
        assert result.valid[0].remanent == 25


class TestKPeriod:
    def test_in_range(self):
        payload = _payload(k=[{"start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:59"}])
        result = filter_transactions(payload)
        assert result.valid[0].inkPeriod is True

    def test_out_of_range(self):
        payload = _payload(k=[{"start": "2024-01-01 00:00:00", "end": "2024-12-31 23:59:59"}])
        result = filter_transactions(payload)
        assert result.valid[0].inkPeriod is False

    def test_ceiling_computed_from_raw(self):
        payload = _payload(transactions=[{"date": "2023-10-12 14:23:00", "amount": 620}])
        result = filter_transactions(payload)
        assert result.valid[0].ceiling == 700
        assert result.valid[0].remanent == 80


class TestFilterIntegration:
    def test_spec_example(self, client):
        resp = client.post(
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
        assert resp.status_code == 200
        data = resp.json()
        # July omitted (remanent=0 after q), 3 valid remain
        assert len(data["valid"]) == 3
        assert len(data["invalid"]) == 0
