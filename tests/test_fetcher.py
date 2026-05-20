"""Tests for the fetcher module — uses mocked web3 responses."""
import pytest
from unittest.mock import MagicMock, patch
from ledger_flux.fetcher import Fetcher
from ledger_flux.models import ChainConfig


@pytest.fixture
def chain_config():
    return ChainConfig(
        name="Ethereum",
        chain_id=1,
        rpc_url="https://eth.llamarpc.com",
    )


@pytest.fixture
def fetcher(chain_config):
    return Fetcher(chain_config)


class TestFetcherInit:
    def test_init(self, chain_config):
        f = Fetcher(chain_config)
        assert f.config.name == "Ethereum"
        assert f.config.chain_id == 1

    def test_w3_created(self, fetcher):
        assert fetcher.w3 is not None


class TestFetcherGetBlockRange:
    def test_defaults(self, fetcher):
        with patch.object(fetcher, "get_latest_block", return_value=10000):
            fb, tb = fetcher.get_block_range("0x" + "a" * 40)
            assert fb == 9000
            assert tb == 10000

    def test_explicit_range(self, fetcher):
        fb, tb = fetcher.get_block_range("0x" + "a" * 40, from_block=100, to_block=200)
        assert fb == 100
        assert tb == 200
