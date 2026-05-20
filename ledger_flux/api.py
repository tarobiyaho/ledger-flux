"""FastAPI REST API + web UI for ledger-flux."""
from __future__ import annotations
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from ledger_flux.chains import get_chain, parse_chains
from ledger_flux.fetcher import Fetcher
from ledger_flux.models import TxRecord, TokenTransfer, WalletSummary

app = FastAPI(
    title="Ledger Flux",
    description="EVM wallet activity explorer — multi-chain transaction & token transfer tracker",
    version="0.2.0",
)

TEMPLATE_DIR = Path(__file__).parent / "templates"


class TransferResponse(BaseModel):
    address: str
    chains: List[str]
    transactions: List[TxRecord]
    transfers: List[TokenTransfer]


class SummaryResponse(BaseModel):
    address: str
    chains: List[str]
    total_transactions: int
    total_transfers: int
    erc20_transfers: int
    erc721_transfers: int
    unique_tokens: int


@app.get("/", response_class=HTMLResponse)
def index():
    """Serve the web UI."""
    html_path = TEMPLATE_DIR / "index.html"
    return HTMLResponse(content=html_path.read_text())


@app.get("/wallet/{address}/transfers", response_model=TransferResponse)
def get_wallet_transfers(
    address: str,
    chains: str = Query("eth", description="Comma-separated chain names"),
    from_block: Optional[int] = Query(None),
    to_block: Optional[int] = Query(None),
):
    """Get token transfers and transactions for a wallet address."""
    if not address.startswith("0x") or len(address) != 42:
        raise HTTPException(status_code=400, detail="Invalid address format")

    try:
        chain_keys = parse_chains(chains)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    all_txs = []
    all_transfers = []

    for key in chain_keys:
        cfg = get_chain(key)
        fetcher = Fetcher(cfg)
        result = fetcher.fetch_all(address)
        all_txs.extend(result["transactions"])
        all_transfers.extend(result["transfers"])

    return TransferResponse(
        address=address,
        chains=chain_keys,
        transactions=all_txs,
        transfers=all_transfers,
    )


@app.get("/wallet/{address}/summary", response_model=SummaryResponse)
def get_wallet_summary(
    address: str,
    chains: str = Query("eth", description="Comma-separated chain names"),
):
    """Get a summary of wallet activity."""
    if not address.startswith("0x") or len(address) != 42:
        raise HTTPException(status_code=400, detail="Invalid address format")

    try:
        chain_keys = parse_chains(chains)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    all_txs = []
    all_transfers = []

    for key in chain_keys:
        cfg = get_chain(key)
        fetcher = Fetcher(cfg)
        result = fetcher.fetch_all(address)
        all_txs.extend(result["transactions"])
        all_transfers.extend(result["transfers"])

    erc20 = sum(1 for t in all_transfers if t.token_type == "erc20")
    erc721 = sum(1 for t in all_transfers if t.token_type == "erc721")
    unique_tokens = len(set(t.contract_address for t in all_transfers))

    return SummaryResponse(
        address=address,
        chains=chain_keys,
        total_transactions=len(all_txs),
        total_transfers=len(all_transfers),
        erc20_transfers=erc20,
        erc721_transfers=erc721,
        unique_tokens=unique_tokens,
    )


@app.get("/health")
def health():
    return {"status": "ok"}
