# CIP-68 Dynamic NFT - Off-chain Scripts

Complete Python implementation for CIP-68 NFT operations with full metadata support.

## 📋 Features

- ✅ **Mint NFT** with rich metadata (name, image, description, attributes, media_type, files)
- ✅ **Query NFT** metadata from blockchain with full CBOR decoding
- ✅ **Update NFT** metadata (validator ready, awaiting testnet protocol fix)
- ✅ **Burn NFT** user tokens via native script

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Install dependencies
pip install -r requirements.txt

# Configure Blockfrost
cp .env.example .env
# Edit .env with your BLOCKFROST_PROJECT_ID
```

### 2. Mint NFT

```bash
# Simple metadata

# Rich metadata from JSON file
python mint_nft.py --name "DragonNFT" --metadata-file ../examples/metadata-dragon.json
```

**Output:**
```
✓ Transaction submitted!
Policy ID: 1f32f479d71fe11a22ab3406912704ec570e6fb3046269b0e4cd04c2
Reference token: 100DragonNFT (locked at validator)
User token: 222DragonNFT (sent to user wallet)
```

### 3. Query NFT

```bash
python query_nft.py --policy-id 1f32f479d71fe11a22ab3406912704ec570e6fb3046269b0e4cd04c2 --name DragonNFT
```

**Output:**
```
✓ Metadata found:
Name:        DragonNFT
Image:       ipfs://QmYx6GsYAKnNzZ9A6NvEKV9nf1VaDzJrqDR4kmCKp8JvCE
Description: A rare legendary fire dragon with immense power.
Media Type:  image/png

Attributes:
  - Element: Fire
  - Rarity: Legendary
  - Power: 95
```

### 4. Update NFT (Coming Soon)

```bash
python update_nft.py --policy-id 1f32f479d71fe11a22ab3406912704ec570e6fb3046269b0e4cd04c2 --name DragonNFT --metadata-file ../examples/metadata-dragon-updated.json
```

**Status:** Validator logic complete, blocked by Conway era protocol issue on testnet.

### 5. Burn NFT

```bash
python burn_nft.py --policy-id <POLICY_ID> --name DragonNFT
```

## 📁 File Structure

```
off_chain/
├── mint_nft.py           # Mint CIP-68 NFT pairs
├── query_nft.py          # Query NFT metadata from blockchain
├── update_nft.py         # Update NFT metadata (via validator)
├── burn_nft.py           # Burn user tokens
├── verify_wallets.py     # Check wallet balances
├── config.py             # Network and parameter configuration
├── .env                  # Blockfrost API configuration
├── requirements.txt      # Python dependencies
├── utils/
│   └── helpers.py        # Shared utility functions
├── wallets/              # Mnemonic wallet storage
└── policy/               # Native script policy keys
```

## 🎨 Metadata Structure

### Full CIP-68 Metadata (6 fields)

```json
{
  "name": "NFT Name",
  "image": "ipfs://QmHash...",
  "description": "Description (max 64 bytes on-chain)",
  "attributes": [
    {"trait_type": "Element", "value": "Fire"},
    {"trait_type": "Rarity", "value": "Legendary"}
  ],
  "media_type": "image/png",
  "files": ["ipfs://QmFile1"]
}
```

### ⚠️ Important Limitations

**Cardano CBOR Limit:** All fields limited to 64 bytes
- Keep descriptions concise
- Use IPFS for full content
- Store summary on-chain

## 📝 Example Metadata Files

See `../examples/` directory:
- `metadata-dragon.json` - Gaming/Fantasy NFT
- `metadata-achievement.json` - Educational certificates
- `metadata-realestate.json` - Virtual land/metaverse

## 💰 Wallet Management

Wallets are auto-generated on first use. Mnemonics saved in `wallets/` directory.

### Check Balances

```bash
python verify_wallets.py
```

## ✅ Successful Transactions

| Operation | TX Hash | Explorer |
|-----------|---------|----------|
| Mint (Full Metadata) | `6be40d7c...` | [View](https://preview.cardanoscan.io/transaction/6be40d7c3fbaa5c29afc1dffa6f10652b193d5fcd1d13a719b75eff85327b84e) |
| Burn User Token | `c5348f29...` | [View](https://preview.cardanoscan.io/transaction/c5348f2931a48b4c61315347924c316ef5adf7ea519b6e0cfb5104d8ac24a6b5) |

## ⚙️ Configuration

### Network Settings (`config.py`)

```python
NETWORK_NAME = "preview"  # or "mainnet", "preprod"
BLOCKFROST_URL = "https://cardano-preview.blockfrost.io/api"
MIN_ADA_OUTPUT = 2_000_000  # 2 ADA minimum
```

### Blockfrost API (`.env`)

```bash
BLOCKFROST_PROJECT_ID=preview<YOUR_PROJECT_ID>
```

Get your API key at [blockfrost.io](https://blockfrost.io)

## 🔧 Troubleshooting

### "Reference token not found"
Wait 30-60 seconds for transaction confirmation on testnet.

### "ByteString exceeds 64 bytes"
Shorten description or use IPFS reference. All PlutusData fields limited to 64 bytes.

### "PPViewHashesDontMatch" (Update only)
Conway era protocol issue on Preview testnet. Validator code is correct.

## 🏗️ Architecture

```
CIP-68 NFT Flow:
1. Mint → Creates reference (100) + user (222) token pair
2. Reference token → Locked at validator with inline datum
3. User token → Sent to owner's wallet (proves ownership)
4. Update → Spends reference, updates datum, returns to script
5. Burn → Burns user token via native script
```

## 🧪 Development

### Run Tests

```bash
# Test complete workflow
python mint_nft.py --name Test --metadata-file ../examples/metadata-dragon.json
python query_nft.py --policy-id <ID> --name Test
python burn_nft.py --policy-id <ID> --name Test
```

### Rebuild Validator

```bash
cd ../contracts
aiken build
```

## ✅ Production Checklist

- [ ] Update `.env` with mainnet Blockfrost API
- [ ] Change `config.py` NETWORK_NAME to "mainnet"
- [ ] Backup wallet mnemonics securely
- [ ] Test on testnet first
- [ ] Keep descriptions under 64 bytes
- [ ] Use IPFS for images and files

---

**Status:** Production-ready for Mint, Query, and Burn operations.  
**Update:** Validator complete, awaiting testnet protocol fix.

```bash
cd ../contracts
aiken build
cd ../off_chain
```

### 4. Get Test ADA

Request từ faucet:
- Preview: https://docs.cardano.org/cardano-testnets/tools/faucet/
- Preprod: https://docs.cardano.org/cardano-testnets/tools/faucet/

Scripts sẽ tự động generate wallet nếu chưa có.

## 📝 Usage Examples

### Mint NFT

```bash
python mint_nft.py \
  --name "Dragon001" \
  --image "ipfs://QmYourImageHash" \
  --desc "Legendary fire dragon"
```

**Output:**
- Reference token (100) → script address với inline datum
- User token (222) → user wallet
- Policy ID và asset IDs
- Explorer link

### Update NFT

```bash
python update_nft.py \
  --name "Dragon001" \
  --policy "7fd86d5ade2db175fd2e491e117ac1fed4989c6ae5bf48c1be0a6b37" \
  --image "ipfs://QmNewImageHash" \
  --desc "Updated: Dragon evolved!"
```

**Requires:**
- You own user token (222)
- Reference token exists at script

### Query NFT

```bash
# Query all NFTs of policy
python query_nft.py \
  --policy "7fd86d5ade2db175fd2e491e117ac1fed4989c6ae5bf48c1be0a6b37"

# Check ownership
python query_nft.py \
  --policy "7fd86d5a..." \
  --owner "addr_test1qqdpq8qm24gh27..."

# Filter by name
python query_nft.py \
  --policy "7fd86d5a..." \
  --name "Dragon"
```

**Output:**
- All reference tokens at script
- Decoded metadata
- Ownership status
- Locked ADA amount
- Full asset IDs

### Burn NFT

```bash
python burn_nft.py \
  --name "Dragon001" \
  --policy "7fd86d5ade2db175fd2e491e117ac1fed4989c6ae5bf48c1be0a6b37"
```

**Effect:**
- Burns reference token (100)
- Burns user token (222)
- Reclaims locked ADA from script
- Returns to user wallet

## 🔑 Wallet Management

Scripts tự động manage wallets:

**First run:**
```
No wallet found. Generating new wallet...
Mnemonic: word1 word2 word3 ... word24
SAVE THIS MNEMONIC SAFELY!
Wallet saved to: issuer.mnemonic
```

**Subsequent runs:**
```
Loading existing wallet from issuer.mnemonic
```

**Files generated:**
- `issuer.mnemonic` - Issuer wallet (mint, burn operations)
- `user.mnemonic` - User wallet (receive, update operations)
- `policy.skey` - Policy signing key (native script)
- `policy.vkey` - Policy verification key

⚠️ **IMPORTANT:** 
- Backup mnemonics safely
- Never share or commit to git
- Files added to `.gitignore`

## 🏗️ Architecture

### Token Naming (PPBL Approach)

```python
# Reference token (locked at script)
ref_token = "100" + name  # e.g., "100Dragon001"

# User token (sent to wallet)
user_token = "222" + name  # e.g., "222Dragon001"
```

### Datum Structure

```python
@dataclass
class CIP68Datum(PlutusData):
    CONSTR_ID = 0
    image_url: bytes      # Image URL (IPFS or HTTP)
    description: bytes    # NFT description
```

**Example:**
```python
datum = CIP68Datum(
    image_url=b"ipfs://QmExample123",
    description=b"My awesome NFT"
)
```

### Minting Policy (Native Script)

```json
{
  "type": "all",
  "scripts": [
    {
      "type": "sig",
      "keyHash": "policy_key_hash"
    }
  ]
}
```

- Signature-based (không phải Plutus)
- Đơn giản và efficient
- Policy key required để mint/burn

### Update Validator (Plutus V3)

**Checks:**
1. ✓ Datum structure valid
2. ✓ Reference token in input
3. ✓ Reference token in output (same token)
4. ✓ User token included (proof of ownership)

**Parameters:**
- `policy_id`: NFT policy ID (applied at deployment)

## 🐛 Troubleshooting

### Error: "Address does not have any UTxOs"

**Solution:** Request tADA from faucet
```bash
# Get your address
python -c "from utils.helpers import generate_or_load_wallet; _, _, _, addr = generate_or_load_wallet('issuer.mnemonic'); print(addr)"
```

### Error: "plutus.json not found"

**Solution:** Build Aiken contracts
```bash
cd ../contracts
aiken build
```

### Error: "Reference token not found"

**Causes:**
- NFT chưa được mint
- Wrong policy ID
- Wrong token name

**Solution:** Query trước khi update/burn
```bash
python query_nft.py --policy "your_policy_id"
```

### Error: "PPViewHashesDontMatch"

**Cause:** Protocol params changed between build và submit

**Solution:** Scripts tự động handle - retry nếu fail

### Error: "FeeTooSmallUTxO"

**Cause:** Output có datum cần nhiều ADA hơn

**Solution:** Increase `MIN_ADA_SCRIPT_OUTPUT` in `config.py`
```python
MIN_ADA_SCRIPT_OUTPUT = 3_000_000  # 3 ADA
```

## 📚 Code Structure

```
off_chain/
├── mint_nft.py          # Mint CIP-68 NFT pair
├── update_nft.py        # Update metadata
├── query_nft.py         # Query NFT info
├── burn_nft.py          # Burn NFT pair
├── config.py            # Configuration
├── requirements.txt     # Dependencies
├── .env.example         # Environment template
├── .gitignore           # Git ignore rules
└── utils/
    └── helpers.py       # Utility functions
```

### Helper Functions

**`helpers.py`:**
```python
# Wallet operations
generate_or_load_wallet(filename) -> (skey, vkey, pkh, addr)

# Policy operations
create_or_load_policy_keys() -> (skey, vkey, key_hash)

# Token operations
build_token_name(label, name) -> str  # "100" + name
create_cip68_datum(image, desc) -> PlutusData

# Script operations
load_plutus_script(validator_name) -> PlutusV3Script
apply_params_to_script(validator_name, *params) -> PlutusV3Script
```

## 🔐 Security Best Practices

1. **Mnemonics:**
   - Generate strong mnemonics (24 words)
   - Store offline backup
   - Never share publicly

2. **Keys:**
   - Keep `*.skey`, `*.mnemonic` private
   - Use `.gitignore` to prevent commits
   - Separate keys for different environments

3. **Environment:**
   - Use `.env` for configuration
   - Different API keys per network
   - Test on Preview/Preprod first

4. **Transactions:**
   - Always check on explorer
   - Verify metadata before update
   - Test with small amounts first

## 📖 Further Reading

- [CIP-68 Specification](https://cips.cardano.org/cips/cip68/)
- [PyCardano Documentation](https://pycardano.readthedocs.io/)
- [Blockfrost API Docs](https://docs.blockfrost.io/)
- [Aiken Documentation](https://aiken-lang.org/)

## 💡 Tips

**Performance:**
- Use `--no-submit` để test build without submitting
- Cache protocol parameters khi build nhiều TXs
- Reuse same context instance

**Development:**
- Test trên Preview testnet trước
- Use descriptive NFT names
- Keep metadata concise

**Production:**
- Switch to Preprod for final testing
- Use dedicated Blockfrost project
- Monitor transaction confirmation

## 🤝 Contributing

Educational project - contributions welcome!

**Areas:**
- Improve error messages
- Add more examples
- Performance optimizations
- Documentation improvements

---

**Need help?** Check the main [README](../README.md) hoặc [Documentation](../docs/)
