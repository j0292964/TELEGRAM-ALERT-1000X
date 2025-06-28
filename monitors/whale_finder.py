import json
import os
from typing import List
import requests


class WhaleFinder:
    """Fetch whale wallets from an external API and store them locally."""

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

    def fetch(self) -> List[str]:
        if not self.api_url:
            return []
        params = {}
        if self.api_key:
            params["api_key"] = self.api_key
        try:
            resp = requests.get(self.api_url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            return data.get("wallets", [])
        except Exception:
            return []

    def update_whales(self) -> List[str]:
        wallets = self.load()
        fetched = self.fetch()
        for w in fetched:
            if w not in wallets:
                wallets.append(w)
        if fetched:
            self.save(wallets)
        return wallets
