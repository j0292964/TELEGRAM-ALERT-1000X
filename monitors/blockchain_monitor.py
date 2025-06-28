from abc import ABC, abstractmethod
from typing import List, Dict

class BlockchainMonitor(ABC):
    """Base class for blockchain monitors."""

    def __init__(self, wallets: List[str]):
        self.wallets = wallets
        # {wallet: {token_address: first_seen_timestamp}}
        self.known_tokens: Dict[str, Dict[str, int]] = {w: {} for w in wallets}

    @abstractmethod
    def fetch_new_token_purchases(self, wallet: str) -> List[dict]:
        """Return a list of new token purchase events for the wallet.
        Each event should at least contain 'token_address', 'amount', 'tx_hash', and 'timestamp'.
        """
        raise NotImplementedError

    def check_wallets(self) -> List[dict]:
        """Check all wallets for new token purchases."""
        alerts = []
        for wallet in self.wallets:
            events = self.fetch_new_token_purchases(wallet)
            for event in events:
                token = event['token_address']
                if token not in self.known_tokens[wallet]:
                    self.known_tokens[wallet][token] = event['timestamp']
                    alerts.append({**event, 'wallet': wallet})
        return alerts
