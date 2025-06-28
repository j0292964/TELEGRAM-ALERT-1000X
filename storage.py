import json
from pathlib import Path

TRACK_FILE = Path("tracked_wallets.json")


def load_wallets() -> list:
    if TRACK_FILE.exists():
        try:
            return json.loads(TRACK_FILE.read_text())
        except Exception:
            return []
    return []


def save_wallets(wallets: list) -> None:
    TRACK_FILE.write_text(json.dumps(wallets, indent=2))
