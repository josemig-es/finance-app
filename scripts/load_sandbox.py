"""Load data/sandbox_sample.json into the database (Iteration #6).

Run it twice: the second time it should save 0 new transactions,
which proves the duplicate protection works.

    python scripts/load_sandbox.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlmodel import func, select  # noqa: E402

from app.db import get_session, init_db  # noqa: E402
from app.importer import save_account, save_transactions  # noqa: E402
from app.models import Account, Transaction  # noqa: E402

SAMPLE = ROOT / "data" / "sandbox_sample.json"


def main():
    if not SAMPLE.exists():
        sys.exit("❌ data/sandbox_sample.json not found. Run scripts/explore_sandbox.py first.")
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    init_db()
    infos = {a["uid"]: a for a in data["session"]["accounts"]}

    with get_session() as session:
        for acc in data["accounts"]:
            account = save_account(session, data["bank"], infos[acc["uid"]], acc["balances"])
            new, skipped = save_transactions(session, account, acc["transactions"])
            label = account.description or account.product
            print(f"  {label[:28]:<28} {account.identifier[-4:]}  new: {new:>3}  already saved: {skipped:>3}")

        n_acc = session.exec(select(func.count()).select_from(Account)).one()
        n_tx = session.exec(select(func.count()).select_from(Transaction)).one()
    print(f"\n✅ Database now has {n_acc} accounts and {n_tx} transactions (data/finance.db)")


if __name__ == "__main__":
    main()
