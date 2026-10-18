"""Download only the new transactions since the last sync.

    python scripts/sync.py            # real bank
    python scripts/sync.py sandbox    # test bank
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.bank.sync import sync  # noqa: E402

mode = sys.argv[1] if len(sys.argv) > 1 else "real"
try:
    sync(mode)
    print("✅ Sync done.")
except RuntimeError as e:
    sys.exit(f"❌ {e}")
