import pytest

from src.models.challenge import TransactionInput
from src.services.transaction_service import validate_transactions


def _txn(date: str, amount: float, ceiling: float = 0.0, remanent: float = 0.0):
    return TransactionInput(date=date, amount=amount, ceiling=ceiling, remanent=remanent)


class TestValidateNegativeAmount:
    def test_negative_goes_to_invalid(self):
        result = validate_transactions([_txn("2023-01-01", -100, 0, 0)])
        assert len(result.valid) == 0
        assert len(result.invalid) == 1
        assert result.invalid[0].message == "Negative amounts are not allowed"

    def test_negative_preserves_fields(self):
        result = validate_transactions([_txn("2023-05-10 12:00:00", -375.0, 0.0, 0.0)])
        inv = result.invalid[0]
        assert inv.date == "2023-05-10 12:00:00"
        assert inv.amount == -375.0
        assert inv.ceiling == 0.0
        assert inv.remanent == 0.0


class TestValidateDuplicateDate:
    def test_second_occurrence_invalid(self):
        result = validate_transactions(
            [
                _txn("2023-10-12 14:23:00", 250, 300, 50),
                _txn("2023-10-12 14:23:00", 620, 700, 80),
            ]
        )
        assert len(result.valid) == 1
        assert result.valid[0].amount == 250.0
        assert len(result.invalid) == 1
        assert result.invalid[0].message == "Duplicate transaction"
        assert result.invalid[0].amount == 620.0

    def test_third_occurrence_also_invalid(self):
        result = validate_transactions(
            [
                _txn("2023-01-01", 100, 100, 0),
                _txn("2023-01-01", 200, 200, 0),
                _txn("2023-01-01", 300, 300, 0),
            ]
        )
        assert len(result.valid) == 1
        assert len(result.invalid) == 2
        assert all(inv.message == "Duplicate transaction" for inv in result.invalid)


class TestValidateValidTransaction:
    def test_positive_unique_stays_valid(self):
        result = validate_transactions([_txn("2023-06-15", 500, 500, 0)])
        assert len(result.valid) == 1
        assert len(result.invalid) == 0

    def test_preserves_all_fields(self):
        result = validate_transactions([_txn("2023-10-12 14:23:00", 250.0, 300.0, 50.0)])
        v = result.valid[0]
        assert v.date == "2023-10-12 14:23:00"
        assert v.amount == 250.0
        assert v.ceiling == 300.0
        assert v.remanent == 50.0


class TestValidateEmptyList:
    def test_empty_returns_empty(self):
        result = validate_transactions([])
        assert result.valid == []
        assert result.invalid == []


class TestValidateOrdering:
    def test_output_order_matches_input(self):
        txns = [
            _txn("2023-12-01", 100, 100, 0),
            _txn("2023-01-01", -50, 0, 0),
            _txn("2023-06-15", 200, 200, 0),
            _txn("2023-12-01", 300, 300, 0),
        ]
        result = validate_transactions(txns)
        # Valid: first and third (in order)
        assert result.valid[0].date == "2023-12-01"
        assert result.valid[0].amount == 100.0
        assert result.valid[1].date == "2023-06-15"
        assert result.valid[1].amount == 200.0
        # Invalid: second (negative) and fourth (duplicate), in order
        assert result.invalid[0].date == "2023-01-01"
        assert result.invalid[0].message == "Negative amounts are not allowed"
        assert result.invalid[1].date == "2023-12-01"
        assert result.invalid[1].message == "Duplicate transaction"


class TestValidateSpecExample:
    def test_spec_example(self):
        txns = [
            _txn("2023-10-12 14:23:00", 250.0, 300.0, 50.0),
            _txn("2023-02-28 09:15:00", -375.0, 0.0, 0.0),
            _txn("2023-10-12 14:23:00", 620.0, 700.0, 80.0),
        ]
        result = validate_transactions(txns)
        assert len(result.valid) == 1
        assert result.valid[0].amount == 250.0
        assert len(result.invalid) == 2
        assert result.invalid[0].message == "Negative amounts are not allowed"
        assert result.invalid[1].message == "Duplicate transaction"


class TestValidateAllValid:
    def test_all_valid_empty_invalid(self):
        txns = [
            _txn("2023-01-01", 100, 100, 0),
            _txn("2023-02-01", 200, 200, 0),
            _txn("2023-03-01", 300, 300, 0),
        ]
        result = validate_transactions(txns)
        assert len(result.valid) == 3
        assert len(result.invalid) == 0


class TestValidateAllInvalid:
    def test_all_invalid_empty_valid(self):
        txns = [
            _txn("2023-01-01", -100, 0, 0),
            _txn("2023-02-01", -200, 0, 0),
        ]
        result = validate_transactions(txns)
        assert len(result.valid) == 0
        assert len(result.invalid) == 2


class TestValidatorEndpoint:
    @pytest.mark.api
    async def test_validator_spec_example(self, client):
        response = await client.post(
            "/blackrock/challenge/v1/transactions:validator",
            json={
                "wage": 50000,
                "transactions": [
                    {
                        "date": "2023-10-12 14:23:00",
                        "amount": 250.0,
                        "ceiling": 300.0,
                        "remanent": 50.0,
                    },
                    {
                        "date": "2023-02-28 09:15:00",
                        "amount": -375.0,
                        "ceiling": 0.0,
                        "remanent": 0.0,
                    },
                    {
                        "date": "2023-10-12 14:23:00",
                        "amount": 620.0,
                        "ceiling": 700.0,
                        "remanent": 80.0,
                    },
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["valid"]) == 1
        assert data["valid"][0]["amount"] == 250.0
        assert len(data["invalid"]) == 2
        assert data["invalid"][0]["message"] == "Negative amounts are not allowed"
        assert data["invalid"][1]["message"] == "Duplicate transaction"

    @pytest.mark.api
    async def test_validator_empty_list(self, client):
        response = await client.post(
            "/blackrock/challenge/v1/transactions:validator",
            json={"wage": 50000, "transactions": []},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == []
        assert data["invalid"] == []

    @pytest.mark.api
    async def test_validator_all_valid(self, client):
        response = await client.post(
            "/blackrock/challenge/v1/transactions:validator",
            json={
                "wage": 50000,
                "transactions": [
                    {
                        "date": "2023-01-01",
                        "amount": 100.0,
                        "ceiling": 100.0,
                        "remanent": 0.0,
                    },
                    {
                        "date": "2023-02-01",
                        "amount": 200.0,
                        "ceiling": 200.0,
                        "remanent": 0.0,
                    },
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["valid"]) == 2
        assert len(data["invalid"]) == 0
