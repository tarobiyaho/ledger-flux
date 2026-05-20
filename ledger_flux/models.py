"""Pydantic v2 models for ledger-flux."""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, field_validator
import re

HEX_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")


class TxRecord(BaseModel):
    """A single EVM transaction record."""
    model_config = ConfigDict(protected_namespaces=())

    chain: str
    tx_hash: str
    block_number: int
    timestamp: Optional[int] = None
    from_address: str
    to_address: Optional[str] = None
    value_wei: str = "0"
    gas_used: int = 0
    gas_price_wei: str = "0"
    status: int = 1
    method_id: Optional[str] = None

    @field_validator("from_address", "to_address", mode="before")
    @classmethod
    def normalize_address(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not v.startswith("0x"):
            raise ValueError(f"Address must start with 0x: {v}")
        return v.lower()


class TokenTransfer(BaseModel):
    """An ERC-20 or ERC-721 token transfer event."""
    model_config = ConfigDict(protected_namespaces=())

    chain: str
    tx_hash: str
    block_number: int
    timestamp: Optional[int] = None
    log_index: int
    token_type: str = "erc20"  # erc20 or erc721
    contract_address: str
    from_address: str
    to_address: str
    value: str = "0"
    token_id: Optional[str] = None

    @field_validator("from_address", "to_address", "contract_address", mode="before")
    @classmethod
    def normalize_address(cls, v: str) -> str:
        if not v.startswith("0x"):
            raise ValueError(f"Address must start with 0x: {v}")
        return v.lower()

    @field_validator("token_type", mode="before")
    @classmethod
    def validate_token_type(cls, v: str) -> str:
        if v not in ("erc20", "erc721"):
            raise ValueError(f"token_type must be 'erc20' or 'erc721': {v}")
        return v


class ExportResult(BaseModel):
    """Result of an export operation."""
    model_config = ConfigDict(protected_namespaces=())

    format: str
    output_path: str
    transaction_count: int
    transfer_count: int
    chains: List[str]
    file_size_bytes: int


class WalletSummary(BaseModel):
    """Summary of wallet activity."""
    model_config = ConfigDict(protected_namespaces=())

    address: str
    chains: List[str]
    total_transactions: int
    total_transfers: int
    erc20_transfers: int
    erc721_transfers: int
    unique_tokens: int
    first_block: Optional[int] = None
    last_block: Optional[int] = None


class ChainConfig(BaseModel):
    """Configuration for an EVM chain."""
    model_config = ConfigDict(protected_namespaces=())

    name: str
    chain_id: int
    rpc_url: str
    explorer_api: Optional[str] = None
    native_symbol: str = "ETH"
    batch_size: int = 2000
