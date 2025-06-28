import os
import time
import requests
from typing import List, Dict, Optional

from .blockchain_monitor import BlockchainMonitor

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
ETHERSCAN_API_URL = os.getenv("ETHERSCAN_API_URL", "https://api.etherscan.io/api")
QUICKNODE_RPC_URL = os.getenv("QUICKNODE_RPC_URL")
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a69f8cdbe9"

HOLD_SECONDS = int(os.getenv("HOLD_PERIOD_SECONDS", "3600"))


class EthereumMonitor(BlockchainMonitor):
    """Monitor Ethereum wallets for new token purchases and holding."""

    def __init__(self, wallets: List[str]):
        super().__init__(wallets)
        self.last_block: Dict[str, int] = {w: 0 for w in wallets}
        self.pending: Dict[str, Dict[str, dict]] = {w: {} for w in wallets}

    def update_wallets(self, wallets: List[str]):
        super().update_wallets(wallets)
        for w in wallets:
            self.last_block.setdefault(w, 0)
            self.pending.setdefault(w, {})

    def _etherscan_request(self, params: Dict[str, str]) -> dict:
        params["apikey"] = ETHERSCAN_API_KEY
        try:
            resp = requests.get(ETHERSCAN_API_URL, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return {}

    def _rpc_request(self, method: str, params: Optional[list] = None) -> Optional[dict]:
        if not QUICKNODE_RPC_URL:
            return None
        payload = {"jsonrpc": "2.0", "method": method, "params": params or [], "id": 1}
        try:
            resp = requests.post(QUICKNODE_RPC_URL, json=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return data.get("result")
        except Exception:
            return None

    def _get_balance(self, wallet: str, token: str) -> int:
        if QUICKNODE_RPC_URL:
            data = "0x70a08231" + wallet[2:].rjust(64, "0")
            result = self._rpc_request("eth_call", [{"to": token, "data": data}, "latest"])
            return int(result, 16) if result else 0
        params = {
            "module": "account",
            "action": "tokenbalance",
            "contractaddress": token,
            "address": wallet,
            "tag": "latest",
        }
        data = self._etherscan_request(params)
        if data.get("status") == "1":
            try:
                return int(data.get("result", "0"))
            except Exception:
                return 0
        return 0

    def fetch_new_token_purchases(self, wallet: str) -> List[dict]:
        if QUICKNODE_RPC_URL:
            return self._fetch_via_quicknode(wallet)
        return self._fetch_via_etherscan(wallet)

    def _fetch_via_etherscan(self, wallet: str) -> List[dict]:
        params = {
            "module": "account",
            "action": "tokentx",
            "address": wallet,
            "page": 1,
            "offset": 10,
            "sort": "desc",
        }
        data = self._etherscan_request(params)
        result = []
        if data.get("status") == "1":
            for tx in data.get("result", []):
                result.append({
                    "token_address": tx["contractAddress"],
                    "amount": tx["value"],
                    "tx_hash": tx["hash"],
                    "timestamp": int(tx["timeStamp"]),
                })
        return result

    def _fetch_via_quicknode(self, wallet: str) -> List[dict]:
        latest_hex = self._rpc_request("eth_blockNumber")
        if latest_hex is None:
            return []
        latest = int(latest_hex, 16)
        from_block = hex(max(self.last_block.get(wallet, 0), latest - 1000))
        params = [{
            "fromBlock": from_block,
            "toBlock": hex(latest),
            "topics": [TRANSFER_TOPIC, None, "0x" + wallet[2:].lower().rjust(64, "0")],
        }]
        logs = self._rpc_request("eth_getLogs", params) or []
        result = []
        for log in logs:
            block = log["blockNumber"]
            ts_hex = self._rpc_request("eth_getBlockByNumber", [block, False])
            timestamp = int(ts_hex["timestamp"], 16) if ts_hex else 0
            result.append({
                "token_address": log["address"],
                "amount": int(log["data"], 16),
                "tx_hash": log["transactionHash"],
                "timestamp": timestamp,
            })
            blk_int = int(block, 16)
            if blk_int > self.last_block.get(wallet, 0):
                self.last_block[wallet] = blk_int
        return result

    def check_wallets(self) -> List[dict]:
        now = int(time.time())
        alerts: List[dict] = []
        for wallet in self.wallets:
            # check pending buys first
            pending_tokens = list(self.pending.get(wallet, {}).items())
            for token, info in pending_tokens:
                if now - info["timestamp"] >= HOLD_SECONDS:
                    balance = self._get_balance(wallet, token)
                    if balance > 0:
                        alerts.append({
                            "wallet": wallet,
                            "token_address": token,
                            "amount": balance,
                            "tx_hash": info["tx_hash"],
                        })
                    del self.pending[wallet][token]

            # fetch new purchases
            events = self.fetch_new_token_purchases(wallet)
            for event in events:
                token = event["token_address"]
                if token not in self.known_tokens[wallet]:
                    self.known_tokens[wallet][token] = event["timestamp"]
                    self.pending[wallet][token] = event
        return alerts
