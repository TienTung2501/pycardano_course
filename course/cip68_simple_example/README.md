# Simple CIP-68 NFT Minting Example

This example demonstrates how to mint CIP-68 NFTs using PyCardano with a clean, simple implementation.

## Structure

```
cip68_simple_example/
├── contract/              # Aiken smart contracts
│   ├── validators/
│   │   ├── mint_policy.ak       # Minting policy
│   │   └── store_validator.ak   # Reference token store
│   ├── lib/
│   │   └── cip68.ak             # CIP-68 utilities
│   └── plutus.json              # Compiled contracts
│
└── off_chain/             # Python off-chain code
    ├── nft_manager.py           # 🌟 All-in-one CLI tool
    ├── mint_nft.py              # Mint new NFT
    ├── update_nft.py            # Update metadata
    ├── burn_nft.py              # Burn NFT pair
    ├── query_nft.py             # Query NFT info
    ├── config.py                # Configuration
    └── utils.py                 # Helper functions
```

## Quick Start

### 1. Build Smart Contracts

```bash
cd contract
aiken build
```

This generates `plutus.json` with the compiled validators.

### 2. Set Up Python Environment

```bash
pip install pycardano
```

### 3. Configure

Edit `off_chain/config.py`:
- Set your Blockfrost API key
- Configure wallet paths
- Set network (testnet/mainnet)

### 4. Mint NFT

```bash
cd off_chain

# Using the all-in-one manager (recommended)
python nft_manager.py mint

# Or use the individual script
python mint_nft.py
```

### 5. Other Operations

```bash
# Query NFT information
python nft_manager.py query <policy_id> <asset_name_hex>

# Update NFT metadata
python nft_manager.py update <policy_id> <asset_name_hex>

# Burn NFT (both tokens)
python nft_manager.py burn <policy_id> <asset_name_hex>

# List all NFTs
python nft_manager.py list
```

## How It Works

### CIP-68 Token Pair

Each NFT consists of TWO tokens:

1. **Reference Token (Label 100)**:
   - Token name: `0x00000064` + 28-byte asset name
   - Locked at store validator
   - Contains metadata as inline datum
   - Non-transferable

2. **User Token (Label 222)**:
   - Token name: `0x000000de` + 28-byte asset name  
   - Sent to user's wallet
   - Freely tradeable
   - NFT representation

### Minting Process

1. **Generate Keys**: Create issuer keys if not exist
2. **Build Validators**: Apply parameters (issuer PKH, store hash)
3. **Create Transaction**:
   - Mint 2 tokens (ref + user)
   - Send ref token to store with metadata datum
   - Send user token to user wallet
   - Sign with issuer key
4. **Submit**: Send to blockchain

### Metadata Format

```python
{
    "metadata": [
        ["name", "My NFT"],
        ["description", "A simple CIP-68 NFT"],
        ["image", "ipfs://..."],
    ],
    "version": 1,
    "extra": b""
}
```

## Key Differences from Complex Implementations

1. **No Option wrappers** - Direct enum types
2. **Simple parameter passing** - Via Aiken CLI
3. **Clear validation logic** - Easy to understand
4. **Minimal dependencies** - Only PyCardano + Blockfrost
5. **Well-documented** - Every step explained

## Files

### Smart Contracts (Aiken)
- `validators/mint_policy.ak`: Controls minting and burning
- `validators/store_validator.ak`: Manages reference token storage
- `lib/cip68.ak`: CIP-68 utility functions

### Off-chain Scripts (Python)
- `nft_manager.py`: 🌟 **Main CLI** - unified interface for all operations
- `mint_nft.py`: Mint new CIP-68 NFT pair
- `update_nft.py`: Update metadata of existing NFT
- `burn_nft.py`: Burn both reference and user tokens
- `query_nft.py`: Query NFT information from blockchain
- `config.py`: Configuration settings
- `utils.py`: Helper functions for:
  - Loading validators
  - Building token names
  - Creating datums
  - Applying parameters

## Examples

### 1. Mint a New NFT

```bash
python nft_manager.py mint
```

This will:
- Generate/load issuer and user keys
- Build parameterized validators
- Create CIP-68 metadata
- Mint reference token (to store) and user token (to user)
- Submit transaction

### 2. Query NFT Information

```bash
python nft_manager.py query 7212c8f7f86ba20db8fcb8f98c917af7551e117ba3f1733ecf8e0e3c fa162d668ccc93d272544f0e554b5783eccf8f42a59a87059d2e60b4
```

Shows:
- Token locations
- Current metadata
- UTxO information
- Explorer links

### 3. Update Metadata

```bash
python nft_manager.py update 7212c8f7... fa162d...
```

This will:
- Find the reference token at store
- Create new metadata
- Spend and recreate reference token with updated datum
- Keep user token unchanged

### 4. Burn NFT

```bash
python nft_manager.py burn 7212c8f7... fa162d...
```

This will:
- Find both reference and user tokens
- Burn both tokens (mint -1 of each)
- Remove from circulation permanently

## Troubleshooting

### Common Issues

1. **Build fails**: Make sure Aiken is installed and up to date
2. **Import errors**: Check Python dependencies
3. **Transaction fails**: Verify wallet has sufficient funds
4. **Evaluation errors**: Check metadata format and token names

### Debug Mode

Run with `--debug` flag to see detailed transaction info:

```bash
python mint_nft.py --debug
```

This shows:
- Transaction CBOR
- Redeemer data
- Datum structure  
- Execution units
- All outputs

## Next Steps

After minting:
- **Update metadata**: Modify reference token datum
- **Burn tokens**: Remove from circulation
- **Transfer user token**: Trade the NFT
- **Query metadata**: Read from blockchain

See the full course for advanced topics like:
- Dynamic metadata updates
- Batch minting
- Collection management
- Frontend integration
