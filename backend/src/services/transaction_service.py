from src.models.challenge import (
    ExpenseInput,
    InvalidTransaction,
    ParsedTransaction,
    TransactionInput,
    ValidatorOutput,
    compute_ceiling,
    compute_remanent,
)


def parse_transactions(expenses: list[ExpenseInput]) -> list[ParsedTransaction]:
    results = []
    for expense in expenses:
        ceiling = compute_ceiling(expense.amount)
        remanent = compute_remanent(expense.amount, ceiling)
        results.append(
            ParsedTransaction(
                date=expense.date,
                amount=expense.amount,
                ceiling=ceiling,
                remanent=remanent,
            )
        )
    return results


def validate_transactions(
    transactions: list[TransactionInput],
) -> ValidatorOutput:
    valid: list[TransactionInput] = []
    invalid: list[InvalidTransaction] = []
    seen_dates: set[str] = set()

    for txn in transactions:
        if txn.amount < 0:
            invalid.append(
                InvalidTransaction(
                    date=txn.date,
                    amount=txn.amount,
                    ceiling=txn.ceiling,
                    remanent=txn.remanent,
                    message="Negative amounts are not allowed",
                )
            )
        elif txn.date in seen_dates:
            invalid.append(
                InvalidTransaction(
                    date=txn.date,
                    amount=txn.amount,
                    ceiling=txn.ceiling,
                    remanent=txn.remanent,
                    message="Duplicate transaction",
                )
            )
        else:
            seen_dates.add(txn.date)
            valid.append(txn)

    return ValidatorOutput(valid=valid, invalid=invalid)
