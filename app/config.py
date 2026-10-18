"""Project settings, read from the .env file."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
load_dotenv(ROOT / ".env")

MODES = ("real", "sandbox")
DEFAULT_MODE = os.getenv("APP_MODE", "sandbox") if os.getenv("APP_MODE") in MODES else "sandbox"
REDIRECT_URL = os.getenv("REDIRECT_URL", "https://localhost:8501/")

# Which bank to connect to (name as listed by Enable Banking, and its country code)
BANK_NAME = os.getenv("BANK_NAME", "").strip()
BANK_COUNTRY = os.getenv("BANK_COUNTRY", "ES").strip().upper()

# Real and test data live in separate files, so they never mix.
DB_FILES = {"real": DATA / "finance.db", "sandbox": DATA / "sandbox.db"}


def bank_credentials(mode: str) -> tuple[str, str]:
    """Return (application id, private key text) for "real" or "sandbox"."""
    prefix = "REAL" if mode == "real" else "SANDBOX"
    app_id = os.getenv(f"{prefix}_APP_ID", "").strip()
    key_path = os.getenv(f"{prefix}_KEY_PATH", "").strip()
    if not app_id or not key_path:
        raise RuntimeError(f"Missing {prefix}_APP_ID or {prefix}_KEY_PATH in .env")
    key_file = ROOT / key_path
    if not key_file.exists():
        raise RuntimeError(f"Private key not found: {key_path}")
    return app_id, key_file.read_text()
