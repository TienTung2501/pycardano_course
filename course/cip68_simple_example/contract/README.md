# Simple CIP-68 Smart Contract

This is a simplified CIP-68 NFT implementation for educational purposes.

## Overview

CIP-68 defines a standard for NFTs with:
- **Reference Token (100)**: Locked at validator, contains metadata as inline datum
- **User Token (222)**: Sent to user's wallet, tradeable

## Components

### 1. Minting Policy (`mint_policy.ak`)

**Parameters:**
- `store_validator_hash`: Hash of the store validator
- `issuer_pkh`: Public key hash of authorized minter

**Redeemer:**
- `Mint`: Mint new CIP-68 token pair
- `Burn`: Burn existing tokens

**Validation (Mint):**
1. ✅ Exactly 2 tokens minted (quantities = 1 each)
2. ✅ One has label 100 (ref), one has label 222 (user)
3. ✅ Both tokens share same 28-byte asset name suffix
4. ✅ Reference token goes to store validator with inline datum
5. ✅ Transaction signed by issuer

### 2. Store Validator (`store_validator.ak`)

**Parameters:**
- `issuer_pkh`: Public key hash of authorized updater

**Datum:**
- `Metadata`: Contains key-value metadata, version, extra data

**Redeemer:**
- `Update`: Update metadata in datum
- `Burn`: Allow burning of reference token

**Validation:**
- Issuer must sign the transaction

### 3. CIP-68 Utilities (`lib/cip68.ak`)

Helper functions for:
- Token name construction (4-byte label + 28-byte asset name)
- Label validation
- Asset name extraction

## Token Name Format

```
[4 bytes: label][28 bytes: asset name] = 32 bytes total
```

- Reference token: `0x00000064` + asset_name (100 in big-endian)
- User token: `0x000000de` + asset_name (222 in big-endian)

## Building

```bash
cd contract
aiken build
```

This generates `plutus.json` with the compiled validators.

## Key Differences from Complex Implementations

1. **No Option wrapper complexity** - Direct enum types
2. **Simple metadata structure** - Just key-value pairs
3. **Clear validation logic** - Easy to understand checks
4. **Minimal dependencies** - Only stdlib functions
5. **Well-commented** - Every check explained

## Usage Flow

1. **Setup**: Generate issuer keys, build validators with parameters
2. **Mint**: Create reference + user token pair
3. **Update**: Change metadata in reference token datum
4. **Burn**: Remove both tokens from circulation
