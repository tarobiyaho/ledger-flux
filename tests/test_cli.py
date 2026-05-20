"""Tests for the CLI module."""
import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from ledger_flux.cli import app
from ledger_flux.models import TxRecord, TokenTransfer, ExportResult

runner = CliRunner()


class TestCLI:
    def test_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "ledger-flux" in result.output.lower() or "export" in result.output.lower()

    def test_export_help(self):
        result = runner.invoke(app, ["export", "--help"])
        assert result.exit_code == 0
        assert "address" in result.output.lower()

    def test_invalid_address(self):
        result = runner.invoke(app, ["export", "not_an_address"])
        assert result.exit_code == 1

    def test_invalid_address_short(self):
        result = runner.invoke(app, ["export", "0xabc"])
        assert result.exit_code == 1

    @patch("ledger_flux.cli.Fetcher")
    @patch("ledger_flux.cli.export_data")
    def test_export_no_activity(self, mock_export, mock_fetcher_cls):
        """Test export when no activity is found."""
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_all.return_value = {"transactions": [], "transfers": []}
        mock_fetcher_cls.return_value = mock_fetcher

        result = runner.invoke(app, [
            "export", "0x" + "a" * 40, "--chains", "eth"
        ])
        assert result.exit_code == 0
        assert "No activity found" in result.output

    @patch("ledger_flux.cli.Fetcher")
    @patch("ledger_flux.cli.export_data")
    def test_export_success(self, mock_export, mock_fetcher_cls, tmp_path):
        """Test successful export."""
        import tempfile
        output_path = str(tmp_path / "test_output.csv")

        mock_fetcher = MagicMock()
        mock_fetcher.fetch_all.return_value = {
            "transactions": [MagicMock()],
            "transfers": [MagicMock()],
        }
        mock_fetcher_cls.return_value = mock_fetcher

        mock_export.return_value = ExportResult(
            format="csv",
            output_path=output_path,
            transaction_count=1,
            transfer_count=1,
            chains=["Ethereum"],
            file_size_bytes=100,
        )

        result = runner.invoke(app, [
            "export", "0x" + "a" * 40,
            "--chains", "eth",
            "--output", output_path,
        ])
        assert result.exit_code == 0
        assert "Exported to" in result.output

    def test_summary_help(self):
        result = runner.invoke(app, ["summary", "--help"])
        assert result.exit_code == 0
