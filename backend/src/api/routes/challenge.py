from fastapi import APIRouter

from src.models.challenge import ExpenseInput, ParsedTransaction, ValidatorInput, ValidatorOutput
from src.services.transaction_service import parse_transactions, validate_transactions

router = APIRouter(prefix="/blackrock/challenge/v1", tags=["challenge"])


@router.post("/transactions:parse", response_model=list[ParsedTransaction])
async def transactions_parse(expenses: list[ExpenseInput]):
    return parse_transactions(expenses)


@router.post("/transactions:validator", response_model=ValidatorOutput)
async def transactions_validator(payload: ValidatorInput):
    return validate_transactions(payload.transactions)
