# Test Type: Unit Test
# Validation: Negative amount and duplicate date detection
# Command: pytest test/test_validator.py -v

from src.models.challenge import TransactionInput
from src.services.transaction_service import validate_transactions


def _txn(date="2023-10-12", amount=250, ceiling=300, remanent=50):
    return TransactionInput(date=date, amount=amount, ceiling=ceiling, remanent=remanent)


class TestValidation:
    def test_negative_amount_invalid(self):
        result = validate_transactions([_txn(amount=-100)])
        assert len(result.valid) == 0
        assert len(result.invalid) == 1
        assert result.invalid[0].message == "Negative amounts are not allowed"

    def test_duplicate_date_invalid(self):
        result = validate_transactions([_txn(), _txn(amount=999)])
        assert len(result.valid) == 1
        assert len(result.invalid) == 1
        assert result.invalid[0].message == "Duplicate transaction"

    def test_valid_transaction(self):
        result = validate_transactions([_txn()])
        assert len(result.valid) == 1
        assert len(result.invalid) == 0

    def test_empty_input(self):
        result = validate_transactions([])
        assert result.valid == []
        assert result.invalid == []

    def test_preserves_fields(self):
        result = validate_transactions([_txn(date="2023-01-01", amount=500, ceiling=500, remanent=0)])
        v = result.valid[0]
        assert v.date == "2023-01-01"
        assert v.amount == 500
        assert v.ceiling == 500
        assert v.remanent == 0


class TestValidatorIntegration:
    def test_mixed_valid_invalid(self, client):
        resp = client.post(
            "/blackrock/challenge/v1/transactions:validator",
            json={
                "wage": 50000,
                "transactions": [
                    {"date": "2023-10-12", "amount": 250, "ceiling": 300, "remanent": 50},
                    {"date": "2023-10-12", "amount": 999, "ceiling": 1000, "remanent": 1},
                    {"date": "2023-05-01", "amount": -100, "ceiling": 0, "remanent": 0},
                ],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["valid"]) == 1
        assert len(data["invalid"]) == 2
