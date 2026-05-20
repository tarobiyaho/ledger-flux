"""Tests for the decoder module."""
import pytest
from ledger_flux.decoder import (
    get_transfer_topic,
    decode_address_from_topic,
    decode_uint256,
    decode_transfer_log,
    decode_transfers_batch,
    ERC20_TRANSFER_TOPIC,
)


class TestTransferTopic:
    def test_topic_format(self):
        topic = get_transfer_topic()
        assert topic.startswith("0x")
        assert len(topic) == 66  # 0x + 64 hex chars

    def test_known_value(self):
        # Transfer(address,address,uint256) = 0xddf252ad...
        topic = get_transfer_topic()
        assert topic == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


class TestDecodeAddressFromTopic:
    def test_decode(self):
        # Address 0x1234... padded to 32 bytes
        addr_bytes = b"\x00" * 12 + bytes.fromhex("aabbccddee" * 4)
        result = decode_address_from_topic(addr_bytes)
        assert result.startswith("0x")
        assert len(result) == 42

    def test_known_address(self):
        addr = "0xabcdef0123456789abcdef0123456789abcdef01"
        padded = b"\x00" * 12 + bytes.fromhex(addr[2:])
        result = decode_address_from_topic(padded)
        assert result == addr


class TestDecodeUint256:
    def test_zero(self):
        assert decode_uint256(b"\x00" * 32) == 0

    def test_one(self):
        data = b"\x00" * 31 + b"\x01"
        assert decode_uint256(data) == 1

    def test_large_value(self):
        # 1 ETH in wei = 10^18
        val = 10**18
        data = val.to_bytes(32, byteorder="big")
        assert decode_uint256(data) == val

    def test_short_data(self):
        assert decode_uint256(b"\x01") == 0


class TestDecodeTransferLog:
    def _make_erc20_log(self, from_addr, to_addr, value, contract_addr="0x" + "b" * 40):
        """Helper to create a mock ERC-20 Transfer log."""
        from_padded = b"\x00" * 12 + bytes.fromhex(from_addr[2:])
        to_padded = b"\x00" * 12 + bytes.fromhex(to_addr[2:])
        topic0 = bytes.fromhex(ERC20_TRANSFER_TOPIC[2:])
        data = value.to_bytes(32, byteorder="big")
        return {
            "topics": [topic0, from_padded, to_padded],
            "data": data,
            "address": contract_addr,
            "logIndex": 5,
            "blockNumber": 12345,
            "transactionHash": "0x" + "aa" * 32,
        }

    def test_erc20_decode(self):
        from_addr = "0x" + "a" * 40
        to_addr = "0x" + "c" * 40
        log = self._make_erc20_log(from_addr, to_addr, 10**18)
        result = decode_transfer_log(log)
        assert result is not None
        assert result["from_address"] == from_addr
        assert result["to_address"] == to_addr
        assert result["value"] == str(10**18)
        assert result["token_type"] == "erc20"

    def test_erc721_decode(self):
        from_addr = "0x" + "a" * 40
        to_addr = "0x" + "c" * 40
        from_padded = b"\x00" * 12 + bytes.fromhex(from_addr[2:])
        to_padded = b"\x00" * 12 + bytes.fromhex(to_addr[2:])
        token_id_padded = b"\x00" * 31 + b"\x2a"  # 42
        topic0 = bytes.fromhex(ERC20_TRANSFER_TOPIC[2:])
        log = {
            "topics": [topic0, from_padded, to_padded, token_id_padded],
            "data": b"",
            "address": "0x" + "b" * 40,
            "logIndex": 0,
            "blockNumber": 100,
            "transactionHash": "0x" + "ff" * 32,
        }
        result = decode_transfer_log(log)
        assert result is not None
        assert result["token_type"] == "erc721"
        assert result["token_id"] == "42"
        assert result["value"] == "1"

    def test_invalid_topic(self):
        log = {"topics": [b"\x00" * 32], "data": b""}
        assert decode_transfer_log(log) is None

    def test_no_topics(self):
        assert decode_transfer_log({"topics": []}) is None
        assert decode_transfer_log({}) is None

    def test_string_topics(self):
        """Test with hex string topics (as returned by some RPCs)."""
        from_addr = "0x" + "a" * 40
        to_addr = "0x" + "c" * 40
        log = {
            "topics": [
                ERC20_TRANSFER_TOPIC,
                "0x" + "0" * 24 + from_addr[2:],
                "0x" + "0" * 24 + to_addr[2:],
            ],
            "data": "0x" + "0" * 63 + "1",  # value = 1
            "address": "0x" + "b" * 40,
            "logIndex": "0x0",
            "blockNumber": "0x100",
            "transactionHash": "0x" + "aa" * 32,
        }
        result = decode_transfer_log(log)
        assert result is not None
        assert result["value"] == "1"


class TestDecodeTransfersBatch:
    def test_batch(self):
        # Create two logs: one valid, one invalid
        valid = {
            "topics": [
                bytes.fromhex(ERC20_TRANSFER_TOPIC[2:]),
                b"\x00" * 12 + bytes.fromhex("a" * 40),
                b"\x00" * 12 + bytes.fromhex("c" * 40),
            ],
            "data": (10**18).to_bytes(32, "big"),
            "address": "0x" + "b" * 40,
            "logIndex": 0,
            "blockNumber": 100,
            "transactionHash": "0x" + "aa" * 32,
        }
        invalid = {"topics": [b"\x00" * 32], "data": b""}
        results = decode_transfers_batch([valid, invalid])
        assert len(results) == 1

    def test_empty_batch(self):
        assert decode_transfers_batch([]) == []
