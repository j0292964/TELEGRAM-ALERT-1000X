import os
import time
from typing import List, Dict, Optional
import requests

QUICKNODE_RPC_URL = os.getenv("QUICKNODE_RPC_URL")
DISCOVERY_TOKEN = os.getenv("DISCOVERY_TOKEN")
COINGECKO_URL = "https://api.coingecko.com/api/v3"

SECONDS_PER_DAY = 86400
PROFIT_MULTIPLIER = float(os.getenv("DISCOVERY_PROFIT_MULTIPLIER", "500"))
MIN_HOLD_DAYS = int(os.getenv("DISCOVERY_MIN_HOLD_DAYS", "60"))
MAX_WALLETS = int(os.getenv("DISCOVERY_MAX_WALLETS", "20"))


def _rpc_request(method: str, params: Optional[list] = None) -> Optional[dict]:
    if not QUICKNODE_RPC_URL:
        return None
    payload = {"jsonrpc": "2.0", "method": method, "params": params or [], "id": 1}
    try:
        r = requests.post(QUICKNODE_RPC_URL, json=payload, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get("result")
    except Exception:
        return None


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
    data = "0x70a08231" + address[2:].rjust(64, "0")
    result = _rpc_request("eth_call", [{"to": token, "data": data}, "latest"])
    return int(result, 16) if result else 0


TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a69f8cdbe9"


def _get_early_transfers(token: str) -> List[Dict[str, str]]:
    params = [{
        "fromBlock": "0x0",
        "toBlock": "latest",
        "address": token,
        "topics": [TRANSFER_TOPIC],
    }]
    logs = _rpc_request("eth_getLogs", params) or []
    result = []
    for log in logs[:100]:
        blk = log["blockNumber"]
        blk_data = _rpc_request("eth_getBlockByNumber", [blk, False])
        ts = int(blk_data["timestamp"], 16) if blk_data else 0
        result.append({
            "to": "0x" + log["topics"][2][-40:],
            "timeStamp": str(ts),
        })
    return result


def discover_smart_wallets(min_hold_days: int = MIN_HOLD_DAYS, max_wallets: int = MAX_WALLETS) -> List[str]:
    """Discover wallets that hit the desired profit multiplier holding DISCOVERY_TOKEN."""
    if not (QUICKNODE_RPC_URL and DISCOVERY_TOKEN):
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
