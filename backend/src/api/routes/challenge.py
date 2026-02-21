from fastapi import APIRouter

from src.core.startup import SERVER_START_TIME
from src.models.challenge import (
    ExpenseInput,
    FilterInput,
    FilterOutput,
    ParsedTransaction,
    PerformanceOutput,
    ValidatorInput,
    ValidatorOutput,
)
from src.services.performance_service import get_performance_metrics
from src.services.transaction_service import (
    filter_transactions,
    parse_transactions,
    validate_transactions,
)

router = APIRouter(prefix="/blackrock/challenge/v1", tags=["challenge"])


@router.post("/transactions:parse", response_model=list[ParsedTransaction])
async def transactions_parse(expenses: list[ExpenseInput]):
    return parse_transactions(expenses)


@router.post("/transactions:validator", response_model=ValidatorOutput)
async def transactions_validator(payload: ValidatorInput):
    return validate_transactions(payload.transactions)


@router.post("/transactions:filter", response_model=FilterOutput)
async def transactions_filter(payload: FilterInput):
    return filter_transactions(payload)


@router.get("/performance", response_model=PerformanceOutput)
async def performance():
    return get_performance_metrics(SERVER_START_TIME)
