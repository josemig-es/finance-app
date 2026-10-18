"""Connect to your bank (log in), download the full history and save it.

The bank is set in .env (BANK_NAME, BANK_COUNTRY).

    python scripts/connect_bank.py            # real bank (default)
    python scripts/connect_bank.py sandbox    # test bank (fake credentials from the Enable Banking sandbox docs)

Run it the first time, and again whenever the bank access expires (~every 180 days).
"""
import json
import sys
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.bank.sync import data_report, finish_connection, start_connection, sync  # noqa: E402
from app.config import BANK_NAME, DATA, REDIRECT_URL  # noqa: E402


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "real"
    if mode not in ("real", "sandbox"):
        sys.exit("Usage: python scripts/connect_bank.py [real|sandbox]")
    bank = BANK_NAME or "your bank"
    print(f"🔐 Connecting to {bank} ({'REAL bank' if mode == 'real' else 'TEST bank'})...\n")

    start = start_connection(mode)
    print(f"Access will be valid for {start['days']} days.")
    print(f"🌐 Opening the {bank} login page in your browser...")
    print("   If it doesn't open, copy this link:\n  ", start["url"])
    webbrowser.open(start["url"])
    print(
        "\n1. Log in and approve the access (your bank may ask you to confirm in its mobile app)."
        "\n2. Select the accounts you want to share and accept."
        "\n3. Your browser will end on a page that says 'This site can't be reached'. That's expected!"
        f"\n   Copy the FULL address from the address bar (it starts with {REDIRECT_URL}) and paste it here."
    )
    while True:
        pasted = input("\nPaste the address: ").strip()
        if pasted.startswith(REDIRECT_URL.rstrip("/")):
            break
        print(f"⚠️  That's not the final address. It must start with {REDIRECT_URL}")

    session = finish_connection(mode, pasted, start["state"])
    print(f"\n✅ Connected. {len(session['accounts'])} account(s). Access valid until {session['valid_until'][:10]}.")

    print("\n⬇️  Downloading history (first time: as far back as the bank allows)...")
    sync(mode)

    report = data_report(mode)
    out = DATA / f"bank_report_{mode}.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n📊 {report['total_transactions']} transactions saved.")
    for a in report["accounts"]:
        print(f"   {str(a['product'])[:30]:<30} {a['transactions']:>5} tx   {a['first_date']} → {a['last_date']}")
    print(f"\nSummary (counts only, no personal data) saved to {out.relative_to(DATA.parent)}")
    print("Open the app with:  streamlit run dashboard.py")


if __name__ == "__main__":
    main()
