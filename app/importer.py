"""Turn Enable Banking data into rows of our database.

Used now to load the sandbox sample, and later by the "Sync" button.
"""
import hashlib
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlmodel import Session, select

from app.models import Account, Transaction


def _account_identifier(info: dict) -> str:
    acc_id = info.get("account_id") or {}
    return acc_id.get("iban") or (acc_id.get("other") or {}).get("identification") or info["uid"]


def save_account(session: Session, bank: str, info: dict, balances: dict) -> Account:
    """Create the account, or update it if we already have it."""
    identifier = _account_identifier(info)
    account = session.exec(select(Account).where(Account.identifier == identifier)).first()
    if account is None:
        account = Account(identifier=identifier, bank=bank)
    account.product = info.get("product")
    account.description = info.get("details")
    account.currency = info.get("currency") or "EUR"
    items = balances.get("balances") or []
    if items:
        account.balance = Decimal(items[0]["balance_amount"]["amount"])
        account.balance_updated_at = datetime.now(timezone.utc)
    session.add(account)
    session.commit()
    session.refresh(account)
    return account


def _reference(account: Account, tx: dict) -> str:
    """The bank's unique ID. If the bank doesn't give one, build a fingerprint from the data."""
    ref = tx.get("entry_reference") or tx.get("transaction_id")
    if ref:
        return str(ref)
    parts = [account.identifier, tx.get("booking_date"), tx["transaction_amount"]["amount"],
             tx.get("credit_debit_indicator"), "|".join(tx.get("remittance_information") or [])]
    return "hash:" + hashlib.sha256("§".join(map(str, parts)).encode()).hexdigest()[:32]


def _to_date(value):
    return date.fromisoformat(value) if value else None


def save_transactions(session: Session, account: Account, transactions: list[dict]) -> tuple[int, int]:
    """Save booked transactions. Returns (new, already_saved)."""
    new = skipped = 0
    for tx in transactions:
        if tx.get("status") not in (None, "BOOK"):
            continue  # pending ones can change; we only keep finished transactions for now
        ref = _reference(account, tx)
        if session.exec(select(Transaction.id).where(Transaction.reference == ref)).first():
            skipped += 1
            continue
        money_in = tx.get("credit_debit_indicator") == "CRDT"
        amount = Decimal(tx["transaction_amount"]["amount"])
        other_side = tx.get("debtor") if money_in else tx.get("creditor")
        session.add(Transaction(
            reference=ref,
            account_id=account.id,
            booking_date=_to_date(tx.get("booking_date") or tx.get("value_date")),
            value_date=_to_date(tx.get("value_date")),
            amount=amount if money_in else -amount,
            currency=tx["transaction_amount"].get("currency", "EUR"),
            concept=" ".join(tx.get("remittance_information") or []) or None,
            counterparty=(other_side or {}).get("name"),
            status=tx.get("status") or "BOOK",
            raw=tx,
        ))
        new += 1
    session.commit()
    return new, skipped
