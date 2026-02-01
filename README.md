# USDm Minting Client

A lightweight Python library and CLI for minting and redeeming USDm via RFQ endpoints.

## Installation

```bash
pip install .
```

## Configuration

Configuration is loaded from environment variables (with `USDM_` prefix) or a `.env` file.

### Required

| Variable | Description |
|----------|-------------|
| `USDM_RPC_URL` | Ethereum RPC endpoint URL |
| `USDM_PRIVATE_KEY` | Private key for signing (0x-prefixed, 64 hex chars) |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `USDM_API_URL` | RFQ API base URL | `https://public.api.megausd.money/` |
| `USDM_MINTING_CONTRACT` | USDm minting contract address (used for EIP-712 and allowances) | `0xE0406beE6D58bCd7C1cA78191b6fde9CA060F6f2` |

### Example `.env`

```bash
USDM_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY
USDM_PRIVATE_KEY=0x...
```

## CLI Usage

### Mint USDm

```bash
usdm mint --size 1000
```

### Redeem USDm

```bash
usdm redeem --size 1000
```

### Auto-Approve Allowance

Automatically approve the required allowance before minting/redeeming:

```bash
usdm mint --size 1000 --auto-approve
usdm redeem --size 1000 --auto-approve
```

### Dry Run

Build and sign an order without submitting:

```bash
usdm mint --size 1000 --dry-run
usdm redeem --size 1000 --dry-run
```

### Check/Approve Allowance

```bash
usdm allowance check --token 0x...
usdm allowance approve --token 0x... --amount 1000000000
```

## Library Usage

### Installation

Install from git:

```bash
pip install git+https://github.com/ethena-labs/usdm-minting-client.git
```

Or add to `requirements.txt`:

```
usdm-minting-client @ git+https://github.com/ethena-labs/usdm-minting-client.git
```

Or add to `pyproject.toml`:

```toml
dependencies = [
    "usdm-minting-client @ git+https://github.com/ethena-labs/usdm-minting-client.git",
]
```

### Example

```python
from usdm.config import Settings
from usdm.rfq.client import RfqClient
from usdm.rfq.order import build_order
from usdm.signer import sign_order

settings = Settings()
client = RfqClient(settings)

# Get quote
quote = client.get_quote(side="mint", size=1000)

# Build and sign order
order = build_order(quote)
signed = sign_order(order, settings.private_key)

# Submit
result = client.submit_order(signed)
```

## Requirements

- Python >= 3.10
- Ethereum mainnet RPC access
- Private key for signing

## License

MIT
