# ledger-flux

**EVM wallet activity exporter — pulls full tx history, decodes ERC-20/721 events, exports CSV/Parquet**

## Features

- **Multi-chain support**: Ethereum, Base, Arbitrum, Optimism, Polygon
- **ERC-20 & ERC-721 decoding**: Automatic Transfer event log decoding
- **Multiple export formats**: CSV, Parquet, JSON
- **CLI tool**: Quick exports from the command line
- **REST API**: Programmatic access via FastAPI
- **No API keys required**: Uses public RPC endpoints

## Installation

```bash
pip install -e .
```

## CLI Usage

```bash
# Export ETH activity
ledger-flux export 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --chains eth --format csv --output vitalik.csv

# Multi-chain export
ledger-flux export 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --chains eth,base,arb --format parquet --output wallet.parquet

# Specify block range
ledger-flux export 0xABC... --from-block 18000000 --to-block 18100000 --format json

# Summary view
ledger-flux summary 0xABC... --chains eth,base

# Override RPC URL
ledger-flux export 0xABC... --rpc-url https://my-rpc.example.com
```

## REST API

```bash
# Start the server
uvicorn ledger_flux.api:app --host 0.0.0.0 --port 8000

# Query transfers
curl http://localhost:8000/wallet/0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045/transfers?chains=eth,base

# Get summary
curl http://localhost:8000/wallet/0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045/summary?chains=eth
```

## Supported Chains

| Chain     | Key  | Chain ID | Native Token |
|-----------|------|----------|--------------|
| Ethereum  | eth  | 1        | ETH          |
| Base      | base | 8453     | ETH          |
| Arbitrum  | arb  | 42161    | ETH          |
| Optimism  | op   | 10       | ETH          |
| Polygon   | matic| 137      | MATIC        |

## Architecture

```
ledger_flux/
├── models.py     # Pydantic v2 data models
├── chains.py     # Multi-chain configuration
├── decoder.py    # ERC-20/721 Transfer event decoder
├── fetcher.py    # Core RPC fetcher (web3.py)
├── exporter.py   # CSV/Parquet/JSON export (pandas)
├── cli.py        # Typer CLI
└── api.py        # FastAPI REST API
```

## How It Works

1. **Fetcher** connects to EVM RPC endpoints via web3.py
2. **eth_getLogs** queries Transfer events (topic: `keccak256("Transfer(address,address,uint256)")`)
3. **Decoder** extracts from/to/value from indexed topics and ABI data
4. **Exporter** converts results to pandas DataFrames and writes CSV/Parquet/JSON
5. Batches queries in 2000-block ranges for efficiency

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest tests/ -v

# Run the API locally
uvicorn ledger_flux.api:app --reload
```

## Why This Matters for Xiaomi MiMo

Xiaomi MiMo represents a new generation of AI models focused on practical reasoning and tool use. Ledger-flux demonstrates exactly the kind of utility that MiMo-style models can leverage:

- **Structured data extraction**: Parsing blockchain logs is a complex structured data problem that tests real-world reasoning
- **Multi-step pipelines**: The fetch → decode → export pipeline mirrors agentic workflows where an AI must coordinate multiple tools
- **Real-world data**: Unlike synthetic benchmarks, blockchain data is immutable, verifiable, and adversarial — testing robustness
- **Tool integration**: The CLI and API make ledger-flux directly callable as a tool by AI agents, enabling wallet analysis as part of larger research tasks

Projects like ledger-flux serve as practical testbeds for evaluating how well models like MiMo handle domain-specific tool use, error recovery, and multi-chain reasoning in production-like environments.

## License

MIT
