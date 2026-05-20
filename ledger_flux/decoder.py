"""ERC-20 and ERC-721 Transfer event decoder."""
from __future__ import annotations
from typing import Dict, Any, Optional
from web3 import Web3


# Transfer(address indexed from, address indexed to, uint256 value)
ERC20_TRANSFER_TOPIC = Web3.keccak(text="Transfer(address,address,uint256)").hex()

# ERC-721 uses the same Transfer signature but value=tokenId
# We distinguish by checking if the log has no data (ERC-721) vs 32-byte data (ERC-20)
# In practice, ERC-721 Transfer events have data=[] or data with the tokenId
# Both share the same topic signature.


def get_transfer_topic() -> str:
    """Return the Transfer event topic hash."""
    return ERC20_TRANSFER_TOPIC


def decode_address_from_topic(topic: bytes) -> str:
    """Extract an address from a 32-byte indexed topic (last 20 bytes)."""
    return "0x" + topic[-20:].hex()


def decode_uint256(data: bytes) -> int:
    """Decode a uint256 from 32 bytes of ABI data."""
    return int.from_bytes(data[:32], byteorder="big") if len(data) >= 32 else 0


def decode_transfer_log(log: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Decode an ERC-20/ERC-721 Transfer event log.

    Returns a dict with from, to, value (for ERC-20) or token_id (for ERC-721),
    or None if the log is not a valid Transfer event.
    """
    topics = log.get("topics", [])
    if not topics:
        return None

    # First topic must match Transfer signature
    topic0 = topics[0]
    if isinstance(topic0, bytes):
        topic0_hex = "0x" + topic0.hex()
    else:
        topic0_hex = topic0

    if topic0_hex.lower() != ERC20_TRANSFER_TOPIC.lower():
        return None

    if len(topics) < 3:
        return None

    from_addr = decode_address_from_topic(
        topics[1] if isinstance(topics[1], bytes) else bytes.fromhex(topics[1][2:] if topics[1].startswith("0x") else topics[1])
    )
    to_addr = decode_address_from_topic(
        topics[2] if isinstance(topics[2], bytes) else bytes.fromhex(topics[2][2:] if topics[2].startswith("0x") else topics[2])
    )

    data = log.get("data", b"")
    if isinstance(data, str):
        if data.startswith("0x"):
            data = data[2:]
        data = bytes.fromhex(data) if data else b""

    contract_address = log.get("address", "")
    if isinstance(contract_address, bytes):
        contract_address = "0x" + contract_address.hex()

    log_index = log.get("logIndex", log.get("log_index", 0))
    if isinstance(log_index, str):
        log_index = int(log_index, 16) if log_index.startswith("0x") else int(log_index)

    block_number = log.get("blockNumber", log.get("block_number", 0))
    if isinstance(block_number, str):
        block_number = int(block_number, 16) if block_number.startswith("0x") else int(block_number)

    tx_hash = log.get("transactionHash", log.get("tx_hash", ""))
    if isinstance(tx_hash, bytes):
        tx_hash = "0x" + tx_hash.hex()

    result = {
        "tx_hash": tx_hash,
        "block_number": block_number,
        "log_index": log_index,
        "contract_address": contract_address,
        "from_address": from_addr,
        "to_address": to_addr,
    }

    # ERC-721: if data is empty or exactly 32 bytes containing a token ID
    # ERC-20: data is 32 bytes containing the value
    if len(data) >= 32:
        value = decode_uint256(data)
        result["value"] = str(value)
        # Heuristic: if there are exactly 3 topics (Transfer + from + to) and
        # no indexed tokenId in topic[3], it's ERC-20. If data represents
        # a token ID that is typically small, could be ERC-721.
        # For simplicity: ERC-721 has token_id in data when only 3 topics
        # We'll treat it as ERC-20 by default and mark ERC-721 if there's a 4th topic
        if len(topics) >= 4:
            # ERC-721 with indexed tokenId
            token_id_topic = topics[3]
            if isinstance(token_id_topic, bytes):
                token_id = int.from_bytes(token_id_topic, byteorder="big")
            else:
                s = token_id_topic
                if s.startswith("0x"):
                    s = s[2:]
                token_id = int(s, 16)
            result["token_id"] = str(token_id)
            result["token_type"] = "erc721"
            result["value"] = "1"
        else:
            result["token_type"] = "erc20"
    else:
        # Data is empty or too short - could be ERC-721 with indexed tokenId in topics
        if len(topics) >= 4:
            token_id_topic = topics[3]
            if isinstance(token_id_topic, bytes):
                token_id = int.from_bytes(token_id_topic, byteorder="big")
            else:
                s = token_id_topic
                if s.startswith("0x"):
                    s = s[2:]
                token_id = int(s, 16)
            result["token_id"] = str(token_id)
            result["token_type"] = "erc721"
            result["value"] = "1"
        else:
            result["value"] = "0"
            result["token_type"] = "erc20"

    return result


def decode_transfers_batch(logs: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """Decode a batch of logs, returning only valid Transfer events."""
    results = []
    for log in logs:
        decoded = decode_transfer_log(log)
        if decoded is not None:
            results.append(decoded)
    return results
