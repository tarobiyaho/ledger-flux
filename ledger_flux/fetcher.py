"""Core fetcher: gets transactions and token transfer events via Blockscout API + web3.py."""
from __future__ import annotations
import json
import urllib.request
from typing import List, Optional, Dict, Any
from ledger_flux.models import TxRecord, TokenTransfer, ChainConfig


class Fetcher:
    """Fetches wallet activity from an EVM chain via Blockscout REST API."""

    def __init__(self, chain_config: ChainConfig):
        self.config = chain_config
        self.blockscout_url = chain_config.blockscout_url or ""

    def _get_json(self, url: str) -> dict:
        req = urllib.request.Request(url, headers={"User-Agent": "ledger-flux/0.1"})
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read())

    def get_transactions(self, address: str) -> List[TxRecord]:
        """Get native transactions via Blockscout API."""
        if not self.blockscout_url:
            return []
        url = f"{self.blockscout_url}/api/v2/addresses/{address}/transactions"
        try:
            data = self._get_json(url)
        except Exception:
            return []

        records = []
        for tx in data.get("items", []):
            value_wei = tx.get("value", "0")
            records.append(TxRecord(
                chain=self.config.name,
                tx_hash=tx.get("tx_hash", ""),
                block_number=tx.get("block_number", 0),
                timestamp=int(
                    __import__("datetime").datetime.fromisoformat(
                        tx.get("timestamp", "2026-01-01T00:00:00+00:00").replace("Z", "+00:00")
                    ).timestamp()
                ),
                from_address=tx.get("from", {}).get("hash", ""),
                to_address=tx.get("to", {}).get("hash", ""),
                value_wei=value_wei,
                gas_used=int(tx.get("gas_used", 0)),
                gas_price_wei=tx.get("gas_price", "0"),
                method_id=tx.get("method", ""),
            ))
        return records

    def get_token_transfers(self, address: str) -> List[TokenTransfer]:
        """Get ERC-20/721 token transfers via Blockscout API."""
        if not self.blockscout_url:
            return []
        url = f"{self.blockscout_url}/api/v2/addresses/{address}/token-transfers"
        try:
            data = self._get_json(url)
        except Exception:
            return []

        transfers = []
        for t in data.get("items", []):
            total = t.get("total", {})
            value_str = total.get("value", "0") if isinstance(total, dict) else "0"
            transfers.append(TokenTransfer(
                chain=self.config.name,
                tx_hash=t.get("tx_hash", ""),
                block_number=t.get("block_number", 0),
                log_index=t.get("log_index", 0),
                token_type=t.get("token", {}).get("type", "ERC-20"),
                contract_address=t.get("token", {}).get("address", ""),
                from_address=t.get("from", {}).get("hash", ""),
                to_address=t.get("to", {}).get("hash", ""),
                value=value_str,
                token_id=t.get("token_id"),
            ))
        return transfers

    def fetch_all(self, address: str) -> Dict[str, Any]:
        """Fetch both native txs and token transfers."""
        txs = self.get_transactions(address)
        transfers = self.get_token_transfers(address)
        return {
            "transactions": txs,
            "transfers": transfers,
        }
