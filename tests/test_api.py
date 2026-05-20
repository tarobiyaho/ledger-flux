"""Tests for the FastAPI API."""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from ledger_flux.api import app
from ledger_flux.models import TxRecord, TokenTransfer

client = TestClient(app)


class TestHealth:
    def test_health(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestTransfers:
    def test_invalid_address(self):
        resp = client.get("/wallet/not_valid/transfers")
        assert resp.status_code == 400

    def test_invalid_chain(self):
        resp = client.get(f"/wallet/0x{'a'*40}/transfers?chains=solana")
        assert resp.status_code == 400

    @patch("ledger_flux.api.Fetcher")
    def test_valid_request_empty(self, mock_fetcher_cls):
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_all.return_value = {"transactions": [], "transfers": []}
        mock_fetcher_cls.return_value = mock_fetcher

        resp = client.get(f"/wallet/0x{'a'*40}/transfers?chains=eth")
        assert resp.status_code == 200
        data = resp.json()
        assert data["address"] == "0x" + "a" * 40
        assert data["transactions"] == []
        assert data["transfers"] == []


class TestSummary:
    def test_invalid_address(self):
        resp = client.get("/wallet/invalid/summary")
        assert resp.status_code == 400

    @patch("ledger_flux.api.Fetcher")
    def test_summary_empty(self, mock_fetcher_cls):
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_all.return_value = {"transactions": [], "transfers": []}
        mock_fetcher_cls.return_value = mock_fetcher

        resp = client.get(f"/wallet/0x{'a'*40}/summary?chains=eth")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_transactions"] == 0
        assert data["total_transfers"] == 0
        assert data["erc20_transfers"] == 0
        assert data["erc721_transfers"] == 0
        assert data["unique_tokens"] == 0

    @patch("ledger_flux.api.Fetcher")
    def test_summary_with_data(self, mock_fetcher_cls):
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_all.return_value = {
            "transactions": [
                TxRecord(chain="Ethereum", tx_hash="0xabc", block_number=1,
                         from_address="0x" + "a" * 40)
            ],
            "transfers": [
                TokenTransfer(
                    chain="Ethereum", tx_hash="0xabc", block_number=1,
                    log_index=0, contract_address="0x" + "b" * 40,
                    from_address="0x" + "a" * 40,
                    to_address="0x" + "c" * 40,
                    value="1000",
                ),
                TokenTransfer(
                    chain="Ethereum", tx_hash="0xdef", block_number=2,
                    log_index=0, token_type="erc721",
                    contract_address="0x" + "e" * 40,
                    from_address="0x" + "a" * 40,
                    to_address="0x" + "c" * 40,
                    token_id="5",
                ),
            ],
        }
        mock_fetcher_cls.return_value = mock_fetcher

        resp = client.get(f"/wallet/0x{'a'*40}/summary?chains=eth")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_transactions"] == 1
        assert data["total_transfers"] == 2
        assert data["erc20_transfers"] == 1
        assert data["erc721_transfers"] == 1
        assert data["unique_tokens"] == 2
