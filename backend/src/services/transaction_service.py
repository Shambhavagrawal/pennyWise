import bisect

from src.models.challenge import (
    ExpenseInput,
    FilteredTransaction,
    FilterInput,
    FilterInvalidTransaction,
    FilterOutput,
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


def filter_transactions(payload: FilterInput) -> FilterOutput:
    # Step 1: Validate — reject negatives and duplicates
    valid_raw: list[ExpenseInput] = []
    invalid: list[FilterInvalidTransaction] = []
    seen_dates: set[str] = set()

    for txn in payload.transactions:
        if txn.amount < 0:
            invalid.append(
                FilterInvalidTransaction(
                    date=txn.date,
                    amount=txn.amount,
                    message="Negative amounts are not allowed",
                )
            )
        elif txn.date in seen_dates:
            invalid.append(
                FilterInvalidTransaction(
                    date=txn.date,
                    amount=txn.amount,
                    message="Duplicate transaction",
                )
            )
        else:
            seen_dates.add(txn.date)
            valid_raw.append(txn)

    # Step 2: Compute ceiling/remanent
    processed: list[dict] = []
    for txn in valid_raw:
        ceiling = compute_ceiling(txn.amount)
        remanent = compute_remanent(txn.amount, ceiling)
        processed.append(
            {
                "date": txn.date,
                "amount": txn.amount,
                "ceiling": ceiling,
                "remanent": remanent,
            }
        )

    # Prepare sorted periods for binary search (O(n log m))
    q_sorted = sorted(
        [(q.start, i, q) for i, q in enumerate(payload.q)],
        key=lambda x: (x[0], x[1]),
    )
    q_starts = [item[0] for item in q_sorted]

    p_sorted = sorted(
        [(p.start, i, p) for i, p in enumerate(payload.p)],
        key=lambda x: (x[0], x[1]),
    )
    p_starts = [item[0] for item in p_sorted]

    k_sorted = sorted(
        [(k.start, i, k) for i, k in enumerate(payload.k)],
        key=lambda x: (x[0], x[1]),
    )
    k_starts = [item[0] for item in k_sorted]

    # Step 3: Apply q periods — latest start wins, first-in-list tiebreak
    for txn in processed:
        date = txn["date"]
        idx = bisect.bisect_right(q_starts, date)
        best_q = None
        for j in range(idx - 1, -1, -1):
            start, orig_idx, q = q_sorted[j]
            if best_q is not None and start < best_q[0]:
                break
            if q.end >= date:
                if (
                    best_q is None
                    or start > best_q[0]
                    or (start == best_q[0] and orig_idx < best_q[1])
                ):
                    best_q = (start, orig_idx, q)
        if best_q is not None:
            txn["remanent"] = best_q[2].fixed

    # Step 4: Apply p periods — all matching extras sum
    for txn in processed:
        date = txn["date"]
        idx = bisect.bisect_right(p_starts, date)
        total_extra = 0.0
        for j in range(idx):
            _start, _orig_idx, p = p_sorted[j]
            if p.end >= date:
                total_extra += p.extra
        txn["remanent"] += total_extra

    # Step 5: Remove transactions with remanent=0
    processed = [txn for txn in processed if txn["remanent"] != 0]

    # Step 6: Set inkPeriod — determined by k periods ONLY
    for txn in processed:
        date = txn["date"]
        idx = bisect.bisect_right(k_starts, date)
        in_period = False
        for j in range(idx):
            _start, _orig_idx, k = k_sorted[j]
            if k.end >= date:
                in_period = True
                break
        txn["inkPeriod"] = in_period

    valid_output = [
        FilteredTransaction(
            date=txn["date"],
            amount=txn["amount"],
            ceiling=txn["ceiling"],
            remanent=txn["remanent"],
            inkPeriod=txn["inkPeriod"],
        )
        for txn in processed
    ]

    return FilterOutput(valid=valid_output, invalid=invalid)
