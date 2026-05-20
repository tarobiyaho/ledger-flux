"""Tests for chain configs."""
import pytest
from ledger_flux.chains import CHAIN_CONFIGS, get_chain, parse_chains, CHAIN_ALIASES


class TestChainConfigs:
    def test_eth_config(self):
        cfg = CHAIN_CONFIGS["eth"]
        assert cfg.chain_id == 1
        assert cfg.rpc_url == "https://eth.llamarpc.com"
        assert cfg.explorer_api == "https://api.etherscan.io"
        assert cfg.native_symbol == "ETH"

    def test_base_config(self):
        cfg = CHAIN_CONFIGS["base"]
        assert cfg.chain_id == 8453
        assert cfg.rpc_url == "https://base-rpc.publicnode.com"

    def test_arb_config(self):
        cfg = CHAIN_CONFIGS["arb"]
        assert cfg.chain_id == 42161
        assert cfg.rpc_url == "https://arb1.arbitrum.io/rpc"

    def test_op_config(self):
        cfg = CHAIN_CONFIGS["op"]
        assert cfg.chain_id == 10
        assert cfg.rpc_url == "https://mainnet.optimism.io"

    def test_matic_config(self):
        cfg = CHAIN_CONFIGS["matic"]
        assert cfg.chain_id == 137
        assert cfg.rpc_url == "https://polygon-rpc.com"
        assert cfg.native_symbol == "MATIC"

    def test_all_chains_present(self):
        expected = {"eth", "base", "arb", "op", "matic"}
        assert expected == set(CHAIN_CONFIGS.keys())


class TestGetChain:
    def test_direct_key(self):
        cfg = get_chain("eth")
        assert cfg.chain_id == 1

    def test_alias(self):
        cfg = get_chain("ethereum")
        assert cfg.chain_id == 1

    def test_alias_arbitrum(self):
        cfg = get_chain("arbitrum")
        assert cfg.chain_id == 42161

    def test_unknown_chain(self):
        with pytest.raises(ValueError, match="Unknown chain"):
            get_chain("solana")

    def test_case_insensitive(self):
        cfg = get_chain("ETH")
        assert cfg.chain_id == 1


class TestParseChains:
    def test_single(self):
        assert parse_chains("eth") == ["eth"]

    def test_multiple(self):
        result = parse_chains("eth,base,arb")
        assert result == ["eth", "base", "arb"]

    def test_with_spaces(self):
        result = parse_chains("eth, base , arb")
        assert result == ["eth", "base", "arb"]

    def test_with_aliases(self):
        result = parse_chains("ethereum,arbitrum")
        assert result == ["eth", "arb"]

    def test_invalid_in_list(self):
        with pytest.raises(ValueError):
            parse_chains("eth,solana")
