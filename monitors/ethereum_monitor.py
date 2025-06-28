import os
import requests
from typing import List, Dict

from .blockchain_monitor import BlockchainMonitor

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
ETHERSCAN_API_URL = os.getenv(
    "ETHERSCAN_API_URL",
    "https://api.etherscan.io/api"
)

class EthereumMonitor(BlockchainMonitor):
    """Monitor Ethereum wallets for new token purchases."""

    def __init__(self, wallets: List[str]):
        super().__init__(wallets)

    def _etherscan_request(self, params: Dict[str, str]) -> dict:
        params["apikey"] = ETHERSCAN_API_KEY
        try:
            resp = requests.get(ETHERSCAN_API_URL, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return {}

    def fetch_new_token_purchases(self, wallet: str) -> List[dict]:
        # Fetch ERC20 token transfer events using Etherscan API.
        # For other blockchains, replace this logic with the relevant API calls.
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
                # Basic example: treat the first transfer of a token to the wallet as a "purchase".
                result.append({
                    "token_address": tx["contractAddress"],
                    "amount": tx["value"],
                    "tx_hash": tx["hash"],
                    "timestamp": int(tx["timeStamp"]),
                })
        return result

