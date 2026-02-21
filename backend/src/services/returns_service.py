import bisect

from src.models.challenge import (
    ExpenseInput,
    ReturnsInput,
    ReturnsOutput,
    SavingsByDate,
    compute_ceiling,
    compute_remanent,
)

NPS_RATE = 0.0711
INDEX_RATE = 0.1449

TAX_SLABS = [
    (700_000, 0.00),
    (1_000_000, 0.10),
    (1_200_000, 0.15),
    (1_500_000, 0.20),
    (float("inf"), 0.30),
]


def compute_tax(income: float) -> float:
    """Compute progressive tax using Indian new regime slabs."""
    tax = 0.0
    prev_limit = 0.0
    for limit, rate in TAX_SLABS:
        if income <= prev_limit:
            break
        taxable = min(income, limit) - prev_limit
        tax += taxable * rate
        prev_limit = limit
    return tax


def _compute_returns(
    payload: ReturnsInput,
    *,
    rate: float,
    include_tax_benefit: bool,
) -> ReturnsOutput:
    """Shared returns calculation parameterized by rate and tax logic."""
    # Step 1: Validate — reject negatives and duplicates
    valid_raw: list[ExpenseInput] = []
    seen_dates: set[str] = set()

    for txn in payload.transactions:
        if txn.amount < 0:
            continue
        elif txn.date in seen_dates:
            continue
        else:
            seen_dates.add(txn.date)
            valid_raw.append(txn)

    # Step 2: Compute ceiling/remanent and totals (before q/p processing)
    total_transaction_amount = 0.0
    total_ceiling = 0.0
    processed: list[dict] = []

    for txn in valid_raw:
        ceiling = compute_ceiling(txn.amount)
        remanent = compute_remanent(txn.amount, ceiling)
        total_transaction_amount += txn.amount
        total_ceiling += ceiling
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

    # Step 6: Group valid transactions by k periods, compute returns
    t = max(60 - payload.age, 5)
    annual_income = payload.wage * 12
    savings_by_dates: list[SavingsByDate] = []

    for k_period in payload.k:
        # Sum remanents of transactions within this k period
        k_amount = 0.0
        for txn in processed:
            if k_period.start <= txn["date"] <= k_period.end:
                k_amount += txn["remanent"]

        # Compound interest (never round intermediates)
        a = k_amount * (1 + rate) ** t

        # Inflation adjustment
        a_real = a / (1 + payload.inflation / 100) ** t

        # Profit — round ONLY at final stage
        profit = round(a_real - k_amount, 2)

        # Tax benefit (NPS only)
        tax_benefit = 0.0
        if include_tax_benefit:
            nps_deduction = min(k_amount, 0.10 * annual_income, 200_000)
            tax_without = compute_tax(annual_income)
            tax_with = compute_tax(annual_income - nps_deduction)
            tax_benefit = round(tax_without - tax_with, 2)

        savings_by_dates.append(
            SavingsByDate(
                start=k_period.start,
                end=k_period.end,
                amount=round(k_amount, 2),
                profit=profit,
                taxBenefit=tax_benefit,
            )
        )

    return ReturnsOutput(
        totalTransactionAmount=round(total_transaction_amount, 2),
        totalCeiling=round(total_ceiling, 2),
        savingsByDates=savings_by_dates,
    )


def compute_nps_returns(payload: ReturnsInput) -> ReturnsOutput:
    """Calculate NPS returns with tax benefits at 7.11% rate."""
    return _compute_returns(payload, rate=NPS_RATE, include_tax_benefit=True)


def compute_index_returns(payload: ReturnsInput) -> ReturnsOutput:
    """Calculate Index Fund returns at 14.49% rate, no tax benefit."""
    return _compute_returns(payload, rate=INDEX_RATE, include_tax_benefit=False)
