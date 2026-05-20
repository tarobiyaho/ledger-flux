"""CSV / Parquet / JSON export via pandas."""
from __future__ import annotations
import os
from typing import List, Literal
from pathlib import Path
import pandas as pd
from ledger_flux.models import TxRecord, TokenTransfer, ExportResult


def transactions_to_dataframe(txs: List[TxRecord]) -> pd.DataFrame:
    """Convert a list of TxRecord to a DataFrame."""
    if not txs:
        return pd.DataFrame(columns=[
            "chain", "tx_hash", "block_number", "timestamp",
            "from_address", "to_address", "value_wei",
            "gas_used", "gas_price_wei", "status", "method_id",
        ])
    return pd.DataFrame([tx.model_dump() for tx in txs])


def transfers_to_dataframe(transfers: List[TokenTransfer]) -> pd.DataFrame:
    """Convert a list of TokenTransfer to a DataFrame."""
    if not transfers:
        return pd.DataFrame(columns=[
            "chain", "tx_hash", "block_number", "timestamp", "log_index",
            "token_type", "contract_address", "from_address", "to_address",
            "value", "token_id",
        ])
    return pd.DataFrame([t.model_dump() for t in transfers])


ExportFormat = Literal["csv", "parquet", "json"]


def export_data(
    txs: List[TxRecord],
    transfers: List[TokenTransfer],
    output_path: str,
    fmt: ExportFormat = "csv",
) -> ExportResult:
    """
    Export transactions and transfers to the specified format.
    Two sheets: 'transactions' and 'transfers' (for parquet/csv they're combined
    into a single file with separate sheets if the format supports it,
    or separate files).
    """
    df_tx = transactions_to_dataframe(txs)
    df_tf = transfers_to_dataframe(transfers)

    # For CSV/JSON, combine into one file with a type column
    df_tx = df_tx.assign(record_type="transaction")
    df_tf = df_tf.assign(record_type="transfer")

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    if fmt == "csv":
        combined = pd.concat([df_tx, df_tf], ignore_index=True)
        combined.to_csv(str(out), index=False)
    elif fmt == "parquet":
        # Use separate sheets isn't supported in parquet, so combine
        combined = pd.concat([df_tx, df_tf], ignore_index=True)
        combined.to_parquet(str(out), index=False, engine="pyarrow")
    elif fmt == "json":
        combined = pd.concat([df_tx, df_tf], ignore_index=True)
        combined.to_json(str(out), orient="records", lines=True)
    else:
        raise ValueError(f"Unsupported format: {fmt}")

    file_size = os.path.getsize(str(out))
    chains = list(set(t.chain for t in txs) | set(t.chain for t in transfers))

    return ExportResult(
        format=fmt,
        output_path=str(out.resolve()),
        transaction_count=len(txs),
        transfer_count=len(transfers),
        chains=chains,
        file_size_bytes=file_size,
    )
