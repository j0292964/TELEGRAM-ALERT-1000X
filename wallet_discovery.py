import os
import time
from typing import List
import requests

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
ETHERSCAN_API_URL = os.getenv("ETHERSCAN_API_URL", "https://api.etherscan.io/api")
DISCOVERY_TOKEN = os.getenv("DISCOVERY_TOKEN")


def _etherscan_request(params: dict) -> dict:
    params["apikey"] = ETHERSCAN_API_KEY
    try:
        resp = requests.get(ETHERSCAN_API_URL, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return {}


def discover_smart_wallets(min_hold_days: int = 20, max_wallets: int = 10) -> List[str]:
    """Discover wallets that bought `DISCOVERY_TOKEN` early and still hold it."""
    if not (ETHERSCAN_API_KEY and DISCOVERY_TOKEN):
        return []

    params = {
        "module": "account",
        "action": "tokentx",
        "contractaddress": DISCOVERY_TOKEN,
        "page": 1,
        "offset": 100,
        "sort": "asc",
    }
    data = _etherscan_request(params)
    if data.get("status") != "1":
        return []

    first_seen = {}
    for tx in data.get("result", []):
        if tx.get("to"):
            addr = tx["to"].lower()
            first_seen.setdefault(addr, int(tx["timeStamp"]))
        if len(first_seen) >= 100:
            break

    now = int(time.time())
    candidates = []
    for addr, ts in first_seen.items():
        if now - ts < min_hold_days * SECONDS_PER_DAY:
            continue
        bal_params = {
            "module": "account",
            "action": "tokenbalance",
            "contractaddress": DISCOVERY_TOKEN,
            "address": addr,
            "tag": "latest",
        }
        bal_data = _etherscan_request(bal_params)
        if bal_data.get("status") == "1" and int(bal_data.get("result", "0")) > 0:
            candidates.append(addr)
        if len(candidates) >= max_wallets:
            break

    return candidates
