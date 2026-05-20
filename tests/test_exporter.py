"""Tests for the exporter module."""
import os
import pytest
import tempfile
import pandas as pd
from ledger_flux.models import TxRecord, TokenTransfer
from ledger_flux.exporter import (
    transactions_to_dataframe,
    transfers_to_dataframe,
    export_data,
)


@pytest.fixture
def sample_txs():
    return [
        TxRecord(
            chain="Ethereum",
            tx_hash="0xabc123",
            block_number=12345,
            timestamp=1700000000,
            from_address="0x" + "a" * 40,
            to_address="0x" + "b" * 40,
            value_wei="1000000000000000000",
            gas_used=21000,
            gas_price_wei="20000000000",
            status=1,
        ),
        TxRecord(
            chain="Ethereum",
            tx_hash="0xdef456",
            block_number=12346,
            from_address="0x" + "b" * 40,
            to_address="0x" + "c" * 40,
            value_wei="500000000000000000",
        ),
    ]


@pytest.fixture
def sample_transfers():
    return [
        TokenTransfer(
            chain="Ethereum",
            tx_hash="0xabc123",
            block_number=12345,
            log_index=0,
            contract_address="0x" + "d" * 40,
            from_address="0x" + "a" * 40,
            to_address="0x" + "b" * 40,
            value="1000000000000000000",
        ),
        TokenTransfer(
            chain="Ethereum",
            tx_hash="0xabc124",
            block_number=12346,
            log_index=1,
            token_type="erc721",
            contract_address="0x" + "e" * 40,
            from_address="0x" + "a" * 40,
            to_address="0x" + "b" * 40,
            token_id="42",
        ),
    ]


class TestTransactionsToDataframe:
    def test_basic(self, sample_txs):
        df = transactions_to_dataframe(sample_txs)
        assert len(df) == 2
        assert "tx_hash" in df.columns
        assert "chain" in df.columns

    def test_empty(self):
        df = transactions_to_dataframe([])
        assert len(df) == 0
        assert "tx_hash" in df.columns


class TestTransfersToDataframe:
    def test_basic(self, sample_transfers):
        df = transfers_to_dataframe(sample_transfers)
        assert len(df) == 2
        assert "token_type" in df.columns

    def test_empty(self):
        df = transfers_to_dataframe([])
        assert len(df) == 0


class TestExportData:
    def test_csv(self, sample_txs, sample_transfers):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            path = f.name
        try:
            result = export_data(sample_txs, sample_transfers, path, "csv")
            assert result.format == "csv"
            assert result.transaction_count == 2
            assert result.transfer_count == 2
            assert result.file_size_bytes > 0
            df = pd.read_csv(path)
            assert len(df) == 4  # 2 txs + 2 transfers
            assert "record_type" in df.columns
        finally:
            os.unlink(path)

    def test_parquet(self, sample_txs, sample_transfers):
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
            path = f.name
        try:
            result = export_data(sample_txs, sample_transfers, path, "parquet")
            assert result.format == "parquet"
            df = pd.read_parquet(path)
            assert len(df) == 4
        finally:
            os.unlink(path)

    def test_json(self, sample_txs, sample_transfers):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            path = f.name
        try:
            result = export_data(sample_txs, sample_transfers, path, "json")
            assert result.format == "json"
            assert result.file_size_bytes > 0
            df = pd.read_json(path, lines=True)
            assert len(df) == 4
        finally:
            os.unlink(path)

    def test_invalid_format(self, sample_txs, sample_transfers):
        with pytest.raises(ValueError):
            export_data(sample_txs, sample_transfers, "/tmp/test.xml", "xml")

    def test_empty_export(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            path = f.name
        try:
            result = export_data([], [], path, "csv")
            assert result.transaction_count == 0
            assert result.transfer_count == 0
        finally:
            os.unlink(path)
