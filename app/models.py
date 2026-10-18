"""Database tables, defined as Python classes with SQLModel.

Three tables:
  - Category:    the list of spending/income groups (Groceries, Rent, Salary...)
  - Account:     one row per bank account
  - Transaction: one row per money movement
"""
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    kind: str = "expense"  # "expense", "income" or "transfer"


class Account(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    # IBAN (or the bank's own account number when there's no IBAN). Never changes, so it identifies the account.
    identifier: str = Field(unique=True, index=True)
    bank: str
    product: Optional[str] = None       # e.g. "CURRENT ACCOUNT"
    description: Optional[str] = None   # e.g. "CUENTA PARA AHORROS"
    currency: str = "EUR"
    balance: Optional[Decimal] = Field(default=None, max_digits=14, decimal_places=2)
    balance_updated_at: Optional[datetime] = None


class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    # The bank's unique ID. "unique=True" makes the database refuse duplicates.
    reference: str = Field(unique=True, index=True)
    account_id: int = Field(foreign_key="account.id", index=True)
    booking_date: date = Field(index=True)
    value_date: Optional[date] = None
    # Signed amount: positive = money in, negative = money out.
    amount: Decimal = Field(max_digits=14, decimal_places=2)
    currency: str = "EUR"
    concept: Optional[str] = None        # e.g. "ALQUILER", "MERCADONA VALENCIA"
    counterparty: Optional[str] = None   # who paid us / who we paid
    status: str = "BOOK"                 # "BOOK" = done, "PDNG" = pending
    category_id: Optional[int] = Field(default=None, foreign_key="category.id", index=True)
    note: Optional[str] = None           # the user's own free text
    raw: dict = Field(default_factory=dict, sa_column=Column(JSON))  # original bank record, untouched
    imported_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
