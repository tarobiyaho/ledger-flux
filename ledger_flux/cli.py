"""Typer CLI for ledger-flux."""
from __future__ import annotations
from typing import Optional
import typer
from ledger_flux.chains import get_chain, parse_chains
from ledger_flux.fetcher import Fetcher
from ledger_flux.exporter import export_data
from ledger_flux.models import TxRecord, TokenTransfer

app = typer.Typer(
    name="ledger-flux",
    help="EVM wallet activity exporter — pulls full tx history, decodes ERC-20/721 events, exports CSV/Parquet",
)


@app.command()
def export(
    address: str = typer.Argument(help="EVM wallet address (0x...)"),
    chains: str = typer.Option("eth", help="Comma-separated chain names (eth,base,arb,op,matic)"),
    format: str = typer.Option("csv", "--format", "-f", help="Output format: csv, parquet, json"),
    output: str = typer.Option("wallet_export.csv", "--output", "-o", help="Output file path"),
    from_block: Optional[int] = typer.Option(None, help="Start block number"),
    to_block: Optional[int] = typer.Option(None, help="End block number"),
    rpc_url: Optional[str] = typer.Option(None, help="Override RPC URL for single chain"),
):
    """Export wallet activity to file."""
    # Validate address
    if not address.startswith("0x") or len(address) != 42:
        typer.echo(f"Error: Invalid address format: {address}", err=True)
        raise typer.Exit(1)

    chain_keys = parse_chains(chains)

    all_txs = []
    all_transfers = []

    for key in chain_keys:
        cfg = get_chain(key)
        if rpc_url and len(chain_keys) == 1:
            cfg.rpc_url = rpc_url
        typer.echo(f"Fetching from {cfg.name} ({cfg.rpc_url})...")
        fetcher = Fetcher(cfg)
        result = fetcher.fetch_all(address, from_block=from_block, to_block=to_block)
        txs = result["transactions"]
        transfers = result["transfers"]
        all_txs.extend(txs)
        all_transfers.extend(transfers)
        typer.echo(f"  Found {len(txs)} txs, {len(transfers)} token transfers")

    if not all_txs and not all_transfers:
        typer.echo("No activity found for this address in the specified range.")
        raise typer.Exit(0)

    result = export_data(all_txs, all_transfers, output, format)
    typer.echo(f"\nExported to {result.output_path}")
    typer.echo(f"  Format: {result.format}")
    typer.echo(f"  Transactions: {result.transaction_count}")
    typer.echo(f"  Token transfers: {result.transfer_count}")
    typer.echo(f"  File size: {result.file_size_bytes} bytes")


@app.command()
def summary(
    address: str = typer.Argument(help="EVM wallet address (0x...)"),
    chains: str = typer.Option("eth", help="Comma-separated chain names"),
):
    """Show a summary of wallet activity."""
    if not address.startswith("0x") or len(address) != 42:
        typer.echo(f"Error: Invalid address format: {address}", err=True)
        raise typer.Exit(1)

    chain_keys = parse_chains(chains)
    total_txs = 0
    total_transfers = 0

    for key in chain_keys:
        cfg = get_chain(key)
        typer.echo(f"Scanning {cfg.name}...")
        fetcher = Fetcher(cfg)
        result = fetcher.fetch_all(address)
        txs = result["transactions"]
        transfers = result["transfers"]
        total_txs += len(txs)
        total_transfers += len(transfers)
        typer.echo(f"  {len(txs)} txs, {len(transfers)} transfers")

    typer.echo(f"\nTotal: {total_txs} transactions, {total_transfers} token transfers")


if __name__ == "__main__":
    app()
