"""Core fetcher: gets transactions and token transfer events via web3.py."""
from __future__ import annotations
from typing import List, Optional, Dict, Any
from web3 import Web3
from web3.exceptions import BlockNotFound
from ledger_flux.models import TxRecord, TokenTransfer, ChainConfig
from ledger_flux.decoder import get_transfer_topic, decode_transfers_batch


class Fetcher:
    """Fetches wallet activity from an EVM chain via RPC."""

    def __init__(self, chain_config: ChainConfig):
        self.config = chain_config
        self.w3 = Web3(Web3.HTTPProvider(chain_config.rpc_url))

    def get_latest_block(self) -> int:
        return self.w3.eth.block_number

    def get_block_range(
        self,
        address: str,
        from_block: Optional[int] = None,
        to_block: Optional[int] = None,
    ) -> tuple[int, int]:
        """Resolve from/to block numbers."""
        if from_block is not None and to_block is not None:
            return from_block, to_block
        latest = self.get_latest_block()
        fb = from_block if from_block is not None else max(0, latest - 1000)
        tb = to_block if to_block is not None else latest
        return fb, tb

    def get_transactions(
        self,
        address: str,
        from_block: Optional[int] = None,
        to_block: Optional[int] = None,
    ) -> List[TxRecord]:
        """
        Get native transactions for an address by scanning blocks.
        Uses eth_getBlockByNumber with full txs and filters by from/to.
        """
        address = address.lower()
        fb, tb = self.get_block_range(address, from_block, to_block)
        records = []

        batch_size = min(self.config.batch_size, 500)  # smaller for full block scans
        current = fb

        while current <= tb:
            end = min(current + batch_size - 1, tb)
            # For efficiency, we fetch logs of native txs aren't easily filterable
            # We'll scan recent blocks for txs involving the address
            for block_num in range(current, end + 1):
                try:
                    block = self.w3.eth.get_block(block_num, full_transactions=True)
                except BlockNotFound:
                    continue
                for tx in block.transactions:
                    tx_from = (tx.get("from") or "").lower()
                    tx_to = (tx.get("to") or "").lower() if tx.get("to") else ""
                    if tx_from == address or tx_to == address:
                        records.append(TxRecord(
                            chain=self.config.name,
                            tx_hash=tx.hash.hex() if isinstance(tx.hash, bytes) else str(tx.hash),
                            block_number=block.number,
                            timestamp=block.timestamp,
                            from_address=tx_from,
                            to_address=tx.get("to"),
                            value_wei=str(tx.get("value", 0)),
                            gas_used=0,  # gas_used only known after receipt
                            gas_price_wei=str(tx.get("gasPrice", 0)),
                            method_id=(tx.get("input", b"")[:4].hex() if isinstance(tx.get("input"), bytes) and len(tx.get("input", b"")) >= 4 else None),
                        ))
            current = end + 1

        return records

    def get_token_transfers(
        self,
        address: str,
        from_block: Optional[int] = None,
        to_block: Optional[int] = None,
    ) -> List[TokenTransfer]:
        """
        Get ERC-20/ERC-721 token transfers for an address using eth_getLogs.
        Queries for Transfer events where the address is sender or receiver.
        """
        address = address.lower()
        padded = "0x" + address[2:].zfill(64)
        transfer_topic = get_transfer_topic()

        fb, tb = self.get_block_range(address, from_block, to_block)
        batch_size = self.config.batch_size
        all_decoded = []
        current = fb

        while current <= tb:
            end = min(current + batch_size - 1, tb)
            from_block_hex = hex(current)
            to_block_hex = hex(end)

            # Query as sender
            try:
                logs_from = self.w3.eth.get_logs({
                    "fromBlock": from_block_hex,
                    "toBlock": to_block_hex,
                    "topics": [transfer_topic, padded],
                })
            except Exception:
                logs_from = []

            # Query as receiver
            try:
                logs_to = self.w3.eth.get_logs({
                    "fromBlock": from_block_hex,
                    "toBlock": to_block_hex,
                    "topics": [transfer_topic, None, padded],
                })
            except Exception:
                logs_to = []

            # Merge and deduplicate
            seen = set()
            combined = []
            for log in logs_from + logs_to:
                key = (
                    log.get("transactionHash", ""),
                    log.get("logIndex", ""),
                )
                if key not in seen:
                    seen.add(key)
                    combined.append(log)

            decoded = decode_transfers_batch(combined)
            for d in decoded:
                all_decoded.append(TokenTransfer(
                    chain=self.config.name,
                    tx_hash=d["tx_hash"],
                    block_number=d["block_number"],
                    log_index=d["log_index"],
                    token_type=d.get("token_type", "erc20"),
                    contract_address=d["contract_address"],
                    from_address=d["from_address"],
                    to_address=d["to_address"],
                    value=d.get("value", "0"),
                    token_id=d.get("token_id"),
                ))

            current = end + 1

        return all_decoded

    def fetch_all(
        self,
        address: str,
        from_block: Optional[int] = None,
        to_block: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Fetch both native txs and token transfers."""
        txs = self.get_transactions(address, from_block, to_block)
        transfers = self.get_token_transfers(address, from_block, to_block)
        return {
            "transactions": txs,
            "transfers": transfers,
        }
