"""Tests for Pydantic models."""
import pytest
from ledger_flux.models import (
    TxRecord, TokenTransfer, ExportResult, WalletSummary, ChainConfig
)


class TestTxRecord:
    def test_create_basic(self):
        tx = TxRecord(
            chain="Ethereum",
            tx_hash="0xabc",
            block_number=12345,
            from_address="0x" + "a" * 40,
        )
        assert tx.chain == "Ethereum"
        assert tx.block_number == 12345
        assert tx.status == 1

    def test_address_normalization(self):
        tx = TxRecord(
            chain="ETH",
            tx_hash="0xabc",
            block_number=1,
            from_address="0x" + "A" * 40,
        )
        assert tx.from_address == "0x" + "a" * 40

    def test_invalid_address(self):
        with pytest.raises(ValueError):
            TxRecord(
                chain="ETH",
                tx_hash="0xabc",
                block_number=1,
                from_address="not_an_address",
            )

    def test_optional_to_address(self):
        tx = TxRecord(
            chain="ETH",
            tx_hash="0xabc",
            block_number=1,
            from_address="0x" + "a" * 40,
            to_address=None,
        )
        assert tx.to_address is None

    def test_model_dump(self):
        tx = TxRecord(
            chain="ETH",
            tx_hash="0xabc",
            block_number=1,
            from_address="0x" + "a" * 40,
        )
        d = tx.model_dump()
        assert "chain" in d
        assert "tx_hash" in d


class TestTokenTransfer:
    def test_create_erc20(self):
        t = TokenTransfer(
            chain="Ethereum",
            tx_hash="0xabc",
            block_number=100,
            log_index=0,
            contract_address="0x" + "b" * 40,
            from_address="0x" + "a" * 40,
            to_address="0x" + "c" * 40,
            value="1000000000000000000",
        )
        assert t.token_type == "erc20"
        assert t.value == "1000000000000000000"

    def test_create_erc721(self):
        t = TokenTransfer(
            chain="Ethereum",
            tx_hash="0xabc",
            block_number=100,
            log_index=1,
            token_type="erc721",
            contract_address="0x" + "b" * 40,
            from_address="0x" + "a" * 40,
            to_address="0x" + "c" * 40,
            token_id="42",
        )
        assert t.token_type == "erc721"
        assert t.token_id == "42"

    def test_invalid_token_type(self):
        with pytest.raises(ValueError):
            TokenTransfer(
                chain="ETH",
                tx_hash="0xabc",
                block_number=1,
                log_index=0,
                token_type="erc1155",
                contract_address="0x" + "b" * 40,
                from_address="0x" + "a" * 40,
                to_address="0x" + "c" * 40,
            )


class TestExportResult:
    def test_create(self):
        r = ExportResult(
            format="csv",
            output_path="/tmp/test.csv",
            transaction_count=10,
            transfer_count=5,
            chains=["eth", "base"],
            file_size_bytes=1024,
        )
        assert r.format == "csv"
        assert r.transaction_count == 10


class TestWalletSummary:
    def test_create(self):
        s = WalletSummary(
            address="0x" + "a" * 40,
            chains=["eth"],
            total_transactions=5,
            total_transfers=3,
            erc20_transfers=2,
            erc721_transfers=1,
            unique_tokens=2,
        )
        assert s.total_transactions == 5


class TestChainConfig:
    def test_create(self):
        c = ChainConfig(
            name="Ethereum",
            chain_id=1,
            rpc_url="https://eth.llamarpc.com",
        )
        assert c.chain_id == 1
        assert c.native_symbol == "ETH"
