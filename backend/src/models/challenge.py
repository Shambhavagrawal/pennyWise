import math

from pydantic import BaseModel


class ExpenseInput(BaseModel):
    date: str
    amount: float


class ParsedTransaction(BaseModel):
    date: str
    amount: float
    ceiling: float
    remanent: float


def compute_ceiling(amount: float) -> float:
    return float(math.ceil(amount / 100) * 100)


def compute_remanent(amount: float, ceiling: float) -> float:
    return ceiling - amount
