from src.models.challenge import (
    ExpenseInput,
    ParsedTransaction,
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
