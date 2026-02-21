from fastapi import APIRouter

from src.models.challenge import ExpenseInput, ParsedTransaction
from src.services.transaction_service import parse_transactions

router = APIRouter(prefix="/blackrock/challenge/v1", tags=["challenge"])


@router.post("/transactions:parse", response_model=list[ParsedTransaction])
async def transactions_parse(expenses: list[ExpenseInput]):
    return parse_transactions(expenses)
