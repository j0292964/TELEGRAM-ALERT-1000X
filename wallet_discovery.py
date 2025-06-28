import os
import time
from typing import List, Dict, Optional
import requests

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
ETHERSCAN_API_URL = os.getenv("ETHERSCAN_API_URL", "https://api.etherscan.io/api")
DISCOVERY_TOKEN = os.getenv("DISCOVERY_TOKEN")
COINGECKO_URL = "https://api.coingecko.com/api/v3"

SECONDS_PER_DAY = 86400
PROFIT_MULTIPLIER = float(os.getenv("DISCOVERY_PROFIT_MULTIPLIER", "500"))
MIN_HOLD_DAYS = int(os.getenv("DISCOVERY_MIN_HOLD_DAYS", "60"))
MAX_WALLETS = int(os.getenv("DISCOVERY_MAX_WALLETS", "20"))


def _etherscan_request(params: Dict[str, str]) -> dict:
    params["apikey"] = ETHERSCAN_API_KEY
    try:
        r = requests.get(ETHERSCAN_API_URL, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}


def _get_price_at(token: str, ts: int) -> Optional[float]:
    url = f"{COINGECKO_URL}/coins/ethereum/contract/{token}/market_chart/range"
    params = {"vs_currency": "usd", "from": ts - 43200, "to": ts + 43200}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json().get("prices", [])
        return data[0][1] if data else None
    except Exception:
        return None


def _get_current_price(token: str) -> Optional[float]:
    url = f"{COINGECKO_URL}/simple/token_price/ethereum"
    params = {"contract_addresses": token, "vs_currencies": "usd"}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        item = data.get(token.lower())
        return item.get("usd") if item else None
    except Exception:
        return None


def _get_balance(address: str, token: str) -> int:
    params = {
        "module": "account",
        "action": "tokenbalance",
        "contractaddress": token,
        "address": address,
        "tag": "latest",
    }
    data = _etherscan_request(params)
    if data.get("status") == "1":
        try:
            return int(data.get("result", "0"))
        except Exception:
            return 0
    return 0


def _get_early_transfers(token: str) -> List[Dict[str, str]]:
    params = {
        "module": "account",
        "action": "tokentx",
        "contractaddress": token,
        "page": 1,
        "offset": 100,
        "sort": "asc",
    }
    data = _etherscan_request(params)
    if data.get("status") == "1":
        return data.get("result", [])
    return []


def discover_smart_wallets(min_hold_days: int = MIN_HOLD_DAYS, max_wallets: int = MAX_WALLETS) -> List[str]:
    """Discover wallets that hit the desired profit multiplier holding DISCOVERY_TOKEN."""
    if not (ETHERSCAN_API_KEY and DISCOVERY_TOKEN):
        return []

    transfers = _get_early_transfers(DISCOVERY_TOKEN)
    now = int(time.time())
    wallets: List[str] = []
    for tx in transfers:
        if not tx.get("to"):
            continue
        wallet = tx["to"].lower()
        ts = int(tx["timeStamp"])
        if now - ts < min_hold_days * SECONDS_PER_DAY:
            continue
        bal = _get_balance(wallet, DISCOVERY_TOKEN)
        if bal <= 0:
            continue
        price_start = _get_price_at(DISCOVERY_TOKEN, ts)
        price_now = _get_current_price(DISCOVERY_TOKEN)
        if not price_start or not price_now or price_start == 0:
            continue
        if price_now / price_start >= PROFIT_MULTIPLIER:
            wallets.append(wallet)
            if len(wallets) >= max_wallets:
                break
    return wallets
