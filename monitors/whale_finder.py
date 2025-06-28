import json
import os
from typing import List, Dict
import requests


class WhaleFinder:
    """Fetch whale wallets from an external API and store them locally.

    The API is expected to return a JSON object with a `wallets` array. Each
    entry may contain optional metrics like `times_1000x` and
    `average_hold_days` so we can filter the results.
    """

    def __init__(self, api_url: str | None, api_key: str | None, db_path: str = "whales.json"):
        self.api_url = api_url
        self.api_key = api_key
        self.db_path = db_path

    def load(self) -> List[str]:
        if not os.path.exists(self.db_path):
            return []
        try:
            with open(self.db_path, "r") as f:
                return json.load(f)
        except Exception:
            return []

    def save(self, wallets: List[str]) -> None:
        try:
            with open(self.db_path, "w") as f:
                json.dump(wallets, f)
        except Exception:
            pass

    def fetch(self) -> List[Dict]:
        if not self.api_url:
            return []
        params = {}
        if self.api_key:
            params["api_key"] = self.api_key
        try:
            resp = requests.get(self.api_url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            wallets = data.get("wallets", [])
            if isinstance(wallets, list):
                return wallets
            return []
        except Exception:
            return []

    def update_whales(self,
                      min_times_1000x: int = 2,
                      min_hold_days: int = 30) -> List[str]:
        """Fetch whales and store the ones matching our criteria."""
        wallets = self.load()
        fetched = self.fetch()
        for entry in fetched:
            address = entry.get("address") if isinstance(entry, dict) else entry
            if not address:
                continue
            times = entry.get("times_1000x", 0) if isinstance(entry, dict) else 0
            hold = entry.get("average_hold_days", 0) if isinstance(entry, dict) else 0
            if times >= min_times_1000x and hold >= min_hold_days:
                if address not in wallets:
                    wallets.append(address)
        if fetched:
            self.save(wallets)
        return wallets
