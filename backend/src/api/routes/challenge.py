from fastapi import APIRouter

from src.core.startup import SERVER_START_TIME
from src.models.challenge import ExpenseInput, ParsedTransaction, PerformanceOutput
from src.services.performance_service import get_performance_metrics
from src.services.transaction_service import parse_transactions

router = APIRouter(prefix="/blackrock/challenge/v1", tags=["challenge"])


@router.post("/transactions:parse", response_model=list[ParsedTransaction])
async def transactions_parse(expenses: list[ExpenseInput]):
    return parse_transactions(expenses)


@router.get("/performance", response_model=PerformanceOutput)
async def performance():
    return get_performance_metrics(SERVER_START_TIME)
