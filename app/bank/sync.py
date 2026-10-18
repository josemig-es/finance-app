"""Connect to the bank and sync transactions into the database.

- connect: start_connection() -> user logs in -> finish_connection(pasted address)
- sync:    sync(mode) asks only for new transactions and saves them
"""
import json
from datetime import date, datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

from sqlmodel import func, select

from app.bank.client import BankError, EnableBanking
from app.config import BANK_COUNTRY, BANK_NAME, DATA, REDIRECT_URL, bank_credentials
from app.db import get_session
from app.importer import save_account, save_transactions
from app.models import Account, Transaction

OVERLAP_DAYS = 7  # re-ask the last week, in case the bank books something late (duplicates are skipped)


def client(mode: str) -> EnableBanking:
    return EnableBanking(*bank_credentials(mode))


def _session_file(mode: str):
    return DATA / f"bank_session_{mode}.json"


def load_session(mode: str) -> dict | None:
    f = _session_file(mode)
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def session_valid_until(mode: str) -> datetime | None:
    s = load_session(mode)
    if not s:
        return None
    until = datetime.fromisoformat(s["valid_until"].replace("Z", "+00:00"))
    return until if until > datetime.now(timezone.utc) else None


# ---------- Connect (login) ----------
def find_bank(c: EnableBanking) -> dict:
    banks = c.aspsps(BANK_COUNTRY)
    if not BANK_NAME:
        raise RuntimeError("Set BANK_NAME in .env. Available in " + BANK_COUNTRY + ": " + ", ".join(b["name"] for b in banks))
    for b in banks:
        if b["name"].strip().upper() == BANK_NAME.upper():
            return b
    raise RuntimeError(f"Bank '{BANK_NAME}' not found in {BANK_COUNTRY}. Available: " + ", ".join(b["name"] for b in banks))


def start_connection(mode: str) -> dict:
    """Returns the login link and what we need to finish the connection."""
    c = client(mode)
    bank = find_bank(c)
    max_days = int(bank.get("maximum_consent_validity", 90 * 86400) // 86400)
    days = max(1, min(max_days, 180))
    url, state = c.start_auth(bank, REDIRECT_URL, days)
    (DATA / f"bank_info_{mode}.json").write_text(json.dumps(bank, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"url": url, "state": state, "days": days}


def finish_connection(mode: str, pasted_address: str, state: str) -> dict:
    params = parse_qs(urlparse(pasted_address.strip()).query)
    if "error" in params:
        raise RuntimeError(f"The bank returned an error: {params.get('error')} {params.get('error_description', '')}")
    if params.get("state", [None])[0] != state:
        raise RuntimeError("This address belongs to a different login attempt. Start again.")
    code = params.get("code", [None])[0]
    if not code:
        raise RuntimeError("No 'code' found in that address. Copy the full address of the final page.")
    s = client(mode).create_session(code)
    saved = {
        "session_id": s["session_id"],
        "valid_until": s["access"]["valid_until"],
        "aspsp": s.get("aspsp"),
        "accounts": s.get("accounts", []),
        "connected_at": datetime.now(timezone.utc).isoformat(),
    }
    _session_file(mode).write_text(json.dumps(saved, indent=2, ensure_ascii=False), encoding="utf-8")
    return saved


# ---------- Sync ----------
def sync(mode: str, log=print) -> list[dict]:
    s = load_session(mode)
    if not s:
        raise RuntimeError("Not connected to the bank yet. Run: python scripts\\connect_bank.py")
    if not session_valid_until(mode):
        raise RuntimeError("Bank access has expired. Connect again: python scripts\\connect_bank.py")
    c = client(mode)
    bank = (s.get("aspsp") or {}).get("name") or BANK_NAME or "Bank"
    summary = []
    with get_session(mode) as db:
        for info in s["accounts"]:
            uid = info["uid"] if isinstance(info, dict) else info
            try:
                balances = c.balances(uid)
                account = save_account(db, bank, info, balances)
                last = db.exec(select(func.max(Transaction.booking_date))
                               .where(Transaction.account_id == account.id)).one()
                if last:  # incremental: only recent days
                    txs = c.transactions(uid, date_from=(last - timedelta(days=OVERLAP_DAYS)).isoformat())
                else:     # first time: as much history as the bank allows
                    txs = c.transactions(uid, date_from=(date.today() - timedelta(days=5 * 365)).isoformat(),
                                         strategy="longest")
                new, old = save_transactions(db, account, txs)
                label = account.description or account.product or "Account"
                log(f"  {label[:30]:<30} ··{account.identifier[-4:]}  new: {new:>4}  already saved: {old:>4}")
                summary.append({"account": label, "new": new, "already_saved": old})
            except BankError as e:
                if e.code in ("EXPIRED_SESSION", "REVOKED_SESSION", "CLOSED_SESSION"):
                    raise RuntimeError("Bank access has expired. Connect again: python scripts\\connect_bank.py")
                if e.status == 429:
                    raise RuntimeError("The bank's daily limit was reached (usually 4 syncs/day). Try again in a few hours.")
                raise
    return summary


# ---------- Report (no personal data: only counts, dates and field names) ----------
def data_report(mode: str) -> dict:
    with get_session(mode) as db:
        accounts = db.exec(select(Account)).all()
        report = {"generated_at": datetime.now(timezone.utc).isoformat(), "accounts": []}
        field_counts, total, directions = {}, 0, {}
        for a in accounts:
            txs = db.exec(select(Transaction).where(Transaction.account_id == a.id)).all()
            dates = [t.booking_date for t in txs]
            report["accounts"].append({
                "product": a.product, "has_balance": a.balance is not None, "transactions": len(txs),
                "first_date": min(dates).isoformat() if dates else None,
                "last_date": max(dates).isoformat() if dates else None,
            })
            for t in txs:
                total += 1
                directions[t.raw.get("credit_debit_indicator")] = directions.get(t.raw.get("credit_debit_indicator"), 0) + 1
                for k, v in t.raw.items():
                    if v not in (None, "", [], {}):
                        field_counts[k] = field_counts.get(k, 0) + 1
        report["total_transactions"] = total
        report["directions"] = directions
        report["fields_filled_pct"] = {k: round(100 * v / total) for k, v in sorted(field_counts.items())} if total else {}
    bank_info = DATA / f"bank_info_{mode}.json"
    if bank_info.exists():
        b = json.loads(bank_info.read_text(encoding="utf-8"))
        report["bank"] = {"name": b.get("name"), "max_consent_days": b.get("maximum_consent_validity", 0) // 86400,
                          "auth_methods": [m.get("name") for m in b.get("auth_methods", [])], "beta": b.get("beta")}
    return report
