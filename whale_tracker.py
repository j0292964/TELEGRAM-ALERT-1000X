import logging
import os
from dataclasses import dataclass, field
from typing import Dict, List

from dotenv import load_dotenv
from web3 import Web3
from telegram import Bot

TRANSFER_EVENT_SIG = Web3.keccak(text="Transfer(address,address,uint256)").hex()

load_dotenv()

@dataclass
class WhaleTracker:
    quicknode_url: str = field(default_factory=lambda: os.getenv("QUICKNODE_URL", ""))
    telegram_token: str = field(default_factory=lambda: os.getenv("TELEGRAM_TOKEN", ""))
    telegram_chat_id: str = field(default_factory=lambda: os.getenv("TELEGRAM_CHAT_ID", ""))
    wallet_labels: Dict[str, str] = field(default_factory=dict)

    def send_log(self, message: str) -> None:
        """Send an informational log message to Telegram and the console."""
        logging.info(message)
        try:
            self.bot.send_message(chat_id=self.telegram_chat_id, text=message)
        except Exception as exc:
            logging.error("Failed to send log message: %s", exc)

    def __post_init__(self):
        if not self.quicknode_url:
            raise ValueError("QUICKNODE_URL environment variable not set")
        if not self.telegram_token:
            raise ValueError("TELEGRAM_TOKEN environment variable not set")
        if not self.telegram_chat_id:
            raise ValueError("TELEGRAM_CHAT_ID environment variable not set")
        self.web3 = Web3(Web3.HTTPProvider(self.quicknode_url))
        self.bot = Bot(self.telegram_token)
        if not self.wallet_labels:
            # Example labels for demonstration; replace with real data lookup
            self.wallet_labels = {
                "0xWalletA": "Dogecoin millionaire 1000x",
                "0xWalletB": "Shiba inu 100000x",
            }
        self.send_log("WhaleTracker initialized")

    def scan_new_blocks(self) -> List[str]:
        """Scan the latest Ethereum blocks for token purchase events."""
        self.send_log("Scanning new blocks for whale activity...")
        try:
            latest = self.web3.eth.block_number
            from_block = max(latest - 5, 0)
            logs = self.web3.eth.get_logs({
                "fromBlock": from_block,
                "toBlock": latest,
                "topics": [TRANSFER_EVENT_SIG],
            })
            wallets = []
            for entry in logs:
                if len(entry["topics"]) >= 3:
                    to_addr = "0x" + entry["topics"][2].hex()[-40:]
                    wallets.append(self.web3.to_checksum_address(to_addr))
            return wallets
        except Exception as exc:
            logging.error("Block scanning failed: %s", exc)
            return []

    def filter_smart_whales(self, wallets: List[str]) -> List[str]:
        """Filter wallets to those meeting holding and profit criteria."""
        self.send_log(f"Evaluating {len(wallets)} wallets for smart whale criteria")
        # Placeholder logic: de-duplicate and pretend all are smart whales
        unique_wallets = list(dict.fromkeys(wallets))
        return unique_wallets

    def cluster_wallets(self, wallets: List[str]) -> List[List[str]]:
        """Cluster wallets that buy and hold together."""
        self.send_log(f"Clustering {len(wallets)} potential whales")
        if len(wallets) < 2:
            return []
        # Simple placeholder: group all wallets together
        return [wallets]

    def send_alert(self, token_address: str, wallets: List[str]):
        lines = [
            "\ud83d\udea8 Smart whale activity detected!",
            f"Token: {token_address}",
            "Wallets:",
        ]
        for w in wallets:
            label = self.wallet_labels.get(w, "unknown history")
            lines.append(f"{w} - {label}")
        message = "\n".join(lines)
        logging.info("Sending Telegram alert: %s", message)
        self.bot.send_message(chat_id=self.telegram_chat_id, text=message)

    def run(self):
        """Main loop for scanning and alerting."""
        self.send_log("Starting WhaleTracker loop")
        wallets = self.scan_new_blocks()
        whales = self.filter_smart_whales(wallets)
        clusters = self.cluster_wallets(whales)
        for group in clusters:
            if len(group) >= 2:
                # Placeholder token address until real detection implemented
                token_address = "0xPLACEHOLDER"
                self.send_alert(token_address, group)

