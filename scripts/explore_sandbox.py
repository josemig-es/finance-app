"""Explore the Enable Banking sandbox (Iteration #5).

What it does, step by step:
  1. Reads your Application ID and private key path from .env
  2. Lists the banks (ASPSPs) available for a country
  3. Opens the bank's login page in your browser so you approve access
  4. Downloads accounts, balances and transactions
  5. Saves everything to data/sandbox_sample.json so we can look at it

Run it from the project folder, with the virtual environment active:
    python scripts/explore_sandbox.py
"""
import json
import os
import sys
import time
import uuid
import webbrowser
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import jwt
import requests
from dotenv import load_dotenv

API = "https://api.enablebanking.com"
ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "data" / "sandbox_sample.json"


def load_settings():
    load_dotenv(ROOT / ".env")
    app_id = os.getenv("ENABLE_BANKING_APPLICATION_ID", "").strip()
    key_path = os.getenv("ENABLE_BANKING_PRIVATE_KEY_PATH", "").strip()
    redirect = os.getenv("ENABLE_BANKING_REDIRECT_URL", "").strip()
    if not app_id or not key_path or not redirect:
        sys.exit("❌ Missing values in .env (APPLICATION_ID, PRIVATE_KEY_PATH or REDIRECT_URL).")
    key_file = ROOT / key_path
    if not key_file.exists():
        sys.exit(f"❌ Private key not found at: {key_file}")
    return app_id, key_file.read_text(), redirect


def make_jwt(app_id, private_key):
    """Digital signature that proves to Enable Banking that the request is really from us."""
    now = int(time.time())
    payload = {"iss": "enablebanking.com", "aud": "api.enablebanking.com", "iat": now, "exp": now + 3600}
    return jwt.encode(payload, private_key, algorithm="RS256", headers={"kid": app_id})


def call(method, path, token, **kwargs):
    r = requests.request(method, API + path, headers={"Authorization": f"Bearer {token}"}, timeout=60, **kwargs)
    if not r.ok:
        sys.exit(f"❌ {method} {path} failed ({r.status_code}): {r.text}")
    return r.json()


def choose_bank(token):
    country = input("Country code [ES]: ").strip().upper() or "ES"
    banks = call("GET", "/aspsps", token, params={"country": country}).get("aspsps", [])
    if not banks:
        sys.exit(f"❌ No banks available for {country} in your sandbox. Try another country (e.g. FI).")
    print(f"\nBanks available in {country}:")
    for i, b in enumerate(banks, 1):
        print(f"  {i:>3}. {b['name']}")
    while True:
        pick = input("\nNumber of the bank to use: ").strip()
        if pick.isdigit() and 1 <= int(pick) <= len(banks):
            return banks[int(pick) - 1], country
        print("Please type a number from the list.")


def authorize(token, bank, country, redirect):
    state = str(uuid.uuid4())
    body = {
        "access": {"valid_until": (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()},
        "aspsp": {"name": bank["name"], "country": country},
        "state": state,
        "redirect_url": redirect,
        "psu_type": "personal",
    }
    url = call("POST", "/auth", token, json=body)["url"]
    print("\n🌐 Opening the bank login page in your browser...")
    print("   If it doesn't open, copy this link into your browser:\n  ", url)
    webbrowser.open(url)
    print(
        "\nAfter you approve access, your browser will go to a localhost page that"
        "\nprobably shows an error like 'This site can't be reached'. That's expected!"
        "\nCopy the FULL address from the address bar and paste it here."
    )
    expected_host = urlparse(redirect).netloc
    while True:
        pasted = input("\nPaste the address: ").strip()
        if urlparse(pasted).netloc == expected_host:
            break
        print(f"⚠️  That's not the final address. It must start with {redirect}"
              "\n   Finish the login in the browser first, then copy the address of the error page.")
    params = parse_qs(urlparse(pasted).query)
    if "error" in params:
        sys.exit(f"❌ The bank returned an error: {params}")
    if params.get("state", [None])[0] != state:
        sys.exit("❌ The address doesn't match this login attempt (state mismatch). Run the script again.")
    code = params.get("code", [None])[0]
    if not code:
        sys.exit("❌ No 'code' found in that address.")
    return code


def fetch_transactions(token, uid, date_from):
    """Transactions come in pages; keep asking until there are no more."""
    all_tx, params = [], {"date_from": date_from}
    while True:
        page = call("GET", f"/accounts/{uid}/transactions", token, params=params)
        all_tx.extend(page.get("transactions", []))
        key = page.get("continuation_key")
        if not key:
            return all_tx
        params = {"date_from": date_from, "continuation_key": key}


def main():
    app_id, private_key, redirect = load_settings()
    token = make_jwt(app_id, private_key)
    print("✅ Settings loaded and request signed.\n")

    bank, country = choose_bank(token)
    code = authorize(token, bank, country, redirect)
    session = call("POST", "/sessions", token, json={"code": code})
    accounts = session.get("accounts", [])
    print(f"\n✅ Access granted. {len(accounts)} account(s) found.")

    date_from = (date.today() - timedelta(days=180)).isoformat()
    result = {"bank": bank["name"], "country": country, "fetched_at": datetime.now().isoformat(),
              "session": session, "accounts": []}
    for acc in accounts:
        uid = acc["uid"] if isinstance(acc, dict) else acc
        print(f"   ↳ Downloading account {uid[:8]}...")
        balances = call("GET", f"/accounts/{uid}/balances", token)
        txs = fetch_transactions(token, uid, date_from)
        result["accounts"].append({"uid": uid, "balances": balances, "transactions": txs})
        print(f"     {len(txs)} transactions")

    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n💾 Saved to {OUTPUT.relative_to(ROOT)}")

    sample = next((a["transactions"][0] for a in result["accounts"] if a["transactions"]), None)
    if sample:
        print("\n🔎 Fields in a transaction:", ", ".join(sample.keys()))


if __name__ == "__main__":
    main()
