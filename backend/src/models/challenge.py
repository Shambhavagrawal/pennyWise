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


class QPeriod(BaseModel):
    fixed: float
    start: str
    end: str


class PPeriod(BaseModel):
    extra: float
    start: str
    end: str


class KPeriod(BaseModel):
    start: str
    end: str


class FilterInput(BaseModel):
    q: list[QPeriod]
    p: list[PPeriod]
    k: list[KPeriod]
    wage: float
    transactions: list[ExpenseInput]


class FilteredTransaction(BaseModel):
    date: str
    amount: float
    ceiling: float
    remanent: float
    inkPeriod: bool  # noqa: N815


class FilterInvalidTransaction(BaseModel):
    date: str
    amount: float
    message: str


class FilterOutput(BaseModel):
    valid: list[FilteredTransaction]
    invalid: list[FilterInvalidTransaction]


class ReturnsInput(BaseModel):
    age: int
    wage: float
    inflation: float
    q: list[QPeriod]
    p: list[PPeriod]
    k: list[KPeriod]
    transactions: list[ExpenseInput]


class SavingsByDate(BaseModel):
    start: str
    end: str
    amount: float
    profit: float
    taxBenefit: float  # noqa: N815


class ReturnsOutput(BaseModel):
    totalTransactionAmount: float  # noqa: N815
    totalCeiling: float  # noqa: N815
    savingsByDates: list[SavingsByDate]  # noqa: N815


def compute_ceiling(amount: float) -> float:
    return float(math.ceil(amount / 100) * 100)


def compute_remanent(amount: float, ceiling: float) -> float:
    return ceiling - amount
