# CIP-68 Simple Example - Scripts Reference

Quick reference cho tất cả scripts available.

---

## 🎯 Main CLI Tool

### nft_manager.py
**All-in-one NFT management tool**

```bash
# Mint new NFT
python nft_manager.py mint [--debug] [--no-submit]

# Query NFT info
python nft_manager.py query <policy_id> <asset_name>

# Update metadata
python nft_manager.py update <policy_id> <asset_name> [--debug] [--no-submit]

# Burn NFT
python nft_manager.py burn <policy_id> <asset_name> [--debug] [--no-submit]

# List NFTs (coming soon)
python nft_manager.py list
```

**Recommended:** Sử dụng tool này cho tất cả operations!

---

## 📜 Individual Scripts

### mint_nft.py
**Mint a new CIP-68 NFT pair**

```bash
python mint_nft.py [--debug] [--no-submit]
```

**What it does:**
- Generates/loads issuer and user keys
- Builds parameterized validators
- Creates reference token (to store) + user token (to user)
- Submits transaction

**Output:**
- Policy ID
- Asset name
- Token names (ref + user)
- Transaction hash

---

### update_nft.py
**Update NFT metadata**

```bash
python update_nft.py <policy_id> <asset_name> [--debug] [--no-submit]
```

**Parameters:**
- `policy_id`: NFT's policy ID (56 hex chars)
- `asset_name`: 28-byte asset name suffix (56 hex chars)

**What it does:**
- Finds reference token at store
- Spends it with Update redeemer
- Recreates it with new metadata
- User token unchanged

**Requires:**
- Issuer signature

---

### burn_nft.py
**Burn both tokens permanently**

```bash
python burn_nft.py <policy_id> <asset_name> [--debug] [--no-submit]
```

**Parameters:**
- `policy_id`: NFT's policy ID (56 hex chars)
- `asset_name`: 28-byte asset name suffix (56 hex chars)

**What it does:**
- Finds both ref and user tokens
- Spends both UTxOs
- Mints -1 of each (burn)
- Removes from circulation

**Requires:**
- Issuer + User signatures
- Access to both tokens

---

### query_nft.py
**Query NFT information**

```bash
python query_nft.py <policy_id> <asset_name>
```

**Parameters:**
- `policy_id`: NFT's policy ID (56 hex chars)
- `asset_name`: 28-byte asset name suffix (56 hex chars)

**What it does:**
- Finds reference token at store
- Decodes metadata from datum
- Shows token locations
- Displays UTxO info

**Output:**
- Token information
- Metadata (decoded)
- UTxO details
- Explorer links

**No transaction:** Read-only operation

---

## 🛠️ Utility Modules

### config.py
**Configuration settings**

```python
NETWORK = "preprod"  # or "mainnet"
BLOCKFROST_PROJECT_ID = "your_api_key"

# Paths
PLUTUS_FILE = "../contract/plutus.json"
ISSUER_MNEMONIC_FILE = "issuer.mnemonic"
USER_MNEMONIC_FILE = "user.mnemonic"

# Constants
LABEL_100 = 0x00000064  # Reference token
LABEL_222 = 0x000000de  # User token
```

**Edit this file** to change network or API keys.

---

### utils.py
**Helper functions**

```python
# Load Plutus script from blueprint
load_plutus_script(validator_title)

# Apply parameters using Aiken CLI
apply_params_to_script(validator_title, params)

# Build CIP-68 token name
build_token_name(label, asset_name_suffix)

# Create CIP-68 metadata datum
create_cip68_datum(metadata_dict)
```

**Used by all scripts** for common operations.

---

## 📝 Common Usage Patterns

### Pattern 1: Complete NFT Lifecycle

```bash
# 1. Mint
python nft_manager.py mint
# → Get policy_id and asset_name from output

# 2. Query
python nft_manager.py query <policy_id> <asset_name>

# 3. Update
python nft_manager.py update <policy_id> <asset_name>

# 4. Query again to verify
python nft_manager.py query <policy_id> <asset_name>

# 5. Burn when done
python nft_manager.py burn <policy_id> <asset_name>
```

### Pattern 2: Test Without Submitting

```bash
# Build transaction but don't submit
python nft_manager.py mint --no-submit --debug

# Check transaction details
# If looks good, run without --no-submit
python nft_manager.py mint
```

### Pattern 3: Batch Operations

```bash
# Mint multiple NFTs
for i in {1..5}; do
    python nft_manager.py mint
    sleep 60  # Wait for confirmation
done

# Query all (need to track policy_id + asset_names)
python nft_manager.py query <policy1> <asset1>
python nft_manager.py query <policy2> <asset2>
# etc.
```

---

## 🔧 Flags Reference

### --debug
Enable verbose debug output:
- Transaction CBOR hex
- All inputs/outputs
- Redeemer data
- Datum structure

**Example:**
```bash
python nft_manager.py mint --debug
```

### --no-submit
Build transaction but don't submit to blockchain:
- Useful for testing
- Verify transaction structure
- Check fees

**Example:**
```bash
python nft_manager.py mint --no-submit
```

### Combining Flags
```bash
python nft_manager.py mint --debug --no-submit
```

---

## 📂 Generated Files

### issuer.mnemonic
**Issuer's wallet mnemonic**
- Generated on first run
- 24 words
- **KEEP SAFE** - Controls minting/burning
- **BACKUP** - Cannot recover if lost

### user.mnemonic
**User's wallet mnemonic**
- Generated on first run
- 24 words
- Receives user tokens
- **BACKUP** - Cannot recover if lost

### Contract Output

#### plutus.json
**Compiled validators**
- Generated by `aiken build`
- Contains mint policy + store validator
- Updated when parameters applied

---

## 🚨 Important Notes

### Security
- ⚠️ **Never share mnemonic files**
- ⚠️ **Backup before deleting**
- ⚠️ **Use preprod for testing**

### Requirements
- ✅ Aiken installed and in PATH
- ✅ Python 3.8+
- ✅ PyCardano installed
- ✅ Blockfrost API key configured
- ✅ Sufficient ADA in issuer wallet

### Costs (Preprod)
- Mint: ~2-3 ADA (locked in outputs)
- Update: ~0.2-0.5 ADA (transaction fees)
- Burn: ~0.2-0.5 ADA (returns locked ADA)
- Query: Free (no transaction)

---

## 📚 See Also

- **GUIDE.md** - Complete tutorial
- **OPERATIONS.md** - Detailed operation docs
- **README.md** - Quick start
- **contract/README.md** - Smart contract docs

---

**Need help?** Check troubleshooting in OPERATIONS.md!
