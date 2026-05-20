"""Chain configurations for supported EVM networks."""
from __future__ import annotations
from typing import Dict
from ledger_flux.models import ChainConfig

CHAIN_CONFIGS: Dict[str, ChainConfig] = {
    "eth": ChainConfig(
        name="Ethereum",
        chain_id=1,
        rpc_url="https://eth.llamarpc.com",
        explorer_api="https://api.etherscan.io",
        blockscout_url="https://eth.blockscout.com",
        native_symbol="ETH",
    ),
    "base": ChainConfig(
        name="Base",
        chain_id=8453,
        rpc_url="https://base-rpc.publicnode.com",
        explorer_api="https://api.basescan.org",
        blockscout_url="https://base.blockscout.com",
        native_symbol="ETH",
    ),
    "arb": ChainConfig(
        name="Arbitrum One",
        chain_id=42161,
        rpc_url="https://arb1.arbitrum.io/rpc",
        blockscout_url="https://arbitrum.blockscout.com",
        native_symbol="ETH",
    ),
    "op": ChainConfig(
        name="Optimism",
        chain_id=10,
        rpc_url="https://mainnet.optimism.io",
        blockscout_url="https://optimism.blockscout.com",
        native_symbol="ETH",
    ),
    "matic": ChainConfig(
        name="Polygon",
        chain_id=137,
        rpc_url="https://polygon-rpc.com",
        blockscout_url="https://polygon.blockscout.com",
        native_symbol="MATIC",
    ),
}

# Friendly aliases
CHAIN_ALIASES = {
    "ethereum": "eth",
    "mainnet": "eth",
    "arbitrum": "arb",
    "optimism": "op",
    "polygon": "matic",
    "pol": "matic",
}


def get_chain(name: str) -> ChainConfig:
    """Resolve a chain name or alias to its config."""
    key = name.strip().lower()
    key = CHAIN_ALIASES.get(key, key)
    if key not in CHAIN_CONFIGS:
        raise ValueError(
            f"Unknown chain '{name}'. Available: {', '.join(CHAIN_CONFIGS.keys())}"
        )
    return CHAIN_CONFIGS[key]


def parse_chains(chains_str: str) -> list[str]:
    """Parse a comma-separated chain list and validate each."""
    parts = [c.strip().lower() for c in chains_str.split(",") if c.strip()]
    resolved = []
    for p in parts:
        cfg = get_chain(p)
        key = p
        key = CHAIN_ALIASES.get(key, key)
        resolved.append(key)
    return resolved
