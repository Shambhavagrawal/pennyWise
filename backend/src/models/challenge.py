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


class TransactionInput(BaseModel):
    date: str
    amount: float
    ceiling: float
    remanent: float


class InvalidTransaction(BaseModel):
    date: str
    amount: float
    ceiling: float
    remanent: float
    message: str


class ValidatorInput(BaseModel):
    wage: float
    transactions: list[TransactionInput]


class ValidatorOutput(BaseModel):
    valid: list[TransactionInput]
    invalid: list[InvalidTransaction]


class PerformanceOutput(BaseModel):
    time: str
    memory: str
    threads: int


def compute_ceiling(amount: float) -> float:
    return float(math.ceil(amount / 100) * 100)


def compute_remanent(amount: float, ceiling: float) -> float:
    return ceiling - amount
