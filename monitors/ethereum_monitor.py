import os
import requests
from typing import List, Dict, Optional

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function",
    },
]

from web3 import Web3

from .blockchain_monitor import BlockchainMonitor

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
ETHERSCAN_API_URL = os.getenv(
    "ETHERSCAN_API_URL",
    "https://api.etherscan.io/api"
)
QUICKNODE_RPC_URL = os.getenv("QUICKNODE_RPC_URL")
WEB3_PROVIDER_URL = os.getenv("WEB3_PROVIDER_URL")
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a69f8cdbe9"

class EthereumMonitor(BlockchainMonitor):
    """Monitor Ethereum wallets for new token purchases."""

    def __init__(self, wallets: List[str]):
        super().__init__(wallets)
        # Keep track of the last scanned block for each wallet when using QuickNode
        self.last_block: Dict[str, int] = {w: 0 for w in wallets}
        self.w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER_URL)) if WEB3_PROVIDER_URL else None

    def _get_token_symbol(self, token_address: str) -> str:
        """Return the ERC-20 token symbol if possible."""
        if self.w3:
            try:
                contract = self.w3.eth.contract(
                    address=Web3.to_checksum_address(token_address), abi=ERC20_ABI
                )
                return contract.functions.symbol().call()
            except Exception:
                pass
        if QUICKNODE_RPC_URL:
            data = "0x95d89b41"  # keccak('symbol()') first 4 bytes
            params = [{"to": token_address, "data": data}, "latest"]
            result = self._rpc_request("eth_call", params)
            if isinstance(result, str) and result.startswith("0x"):
                try:
                    hex_bytes = result[2:]
                    text = bytes.fromhex(hex_bytes).decode("utf-8").rstrip("\x00")
                    if text:
                        return text
                except Exception:
                    pass
        return token_address

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

    def fetch_new_token_purchases(self, wallet: str) -> List[dict]:
        """Return token transfer events for the wallet."""
        # Prefer Web3 provider if configured, then QuickNode, otherwise fall back to Etherscan
        if self.w3:
            return self._fetch_via_web3(wallet)
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
                    "token": self._get_token_symbol(tx["contractAddress"]),
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
            "topics": [TRANSFER_TOPIC, None, "0x" + wallet[2:].lower().rjust(64, "0")]
        }]
        logs = self._rpc_request("eth_getLogs", params) or []
        result = []
        for log in logs:
            block = log["blockNumber"]
            ts_hex = self._rpc_request("eth_getBlockByNumber", [block, False])
            timestamp = int(ts_hex["timestamp"], 16) if ts_hex else 0
            result.append({
                "token_address": log["address"],
                "token": self._get_token_symbol(log["address"]),
                "amount": int(log["data"], 16),
                "tx_hash": log["transactionHash"],
                "timestamp": timestamp,
            })
            blk_int = int(block, 16)
            if blk_int > self.last_block.get(wallet, 0):
                self.last_block[wallet] = blk_int
        return result

    def _fetch_via_web3(self, wallet: str) -> List[dict]:
        if not self.w3:
            return []
        latest = self.w3.eth.block_number
        from_block = max(self.last_block.get(wallet, 0), latest - 1000)
        logs = self.w3.eth.get_logs({
            "fromBlock": from_block,
            "toBlock": latest,
            "topics": [TRANSFER_TOPIC, None, "0x" + wallet[2:].lower().rjust(64, "0")],
        })
        result = []
        for log in logs:
            block_number = log.blockNumber
            block = self.w3.eth.get_block(block_number)
            result.append({
                "token_address": log.address,
                "token": self._get_token_symbol(log.address),
                "amount": int(log.data, 16),
                "tx_hash": log.transactionHash.hex(),
                "timestamp": block.timestamp,
            })
            if block_number > self.last_block.get(wallet, 0):
                self.last_block[wallet] = block_number
        return result

