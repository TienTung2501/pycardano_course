# Module 3: Off-chain Scripts với PyCardano

## 3.1. Overview

Module này hướng dẫn cách viết off-chain scripts để tương tác với CIP-68 NFT:
- **Mint**: Tạo token pair (100 + 222)
- **Update**: Thay đổi metadata
- **Query**: Đọc thông tin NFT
- **Burn**: Destroy tokens

---

## 3.2. Setup Environment

### Bước 1: Cài đặt Python dependencies
```bash
cd off_chain
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### Bước 2: Configure environment
```bash
cp .env.example .env
# Edit .env file
```

**.env file:**
```bash
NETWORK=preview
BLOCKFROST_PROJECT_ID=your_api_key_here
```

### Bước 3: Build Aiken contracts
```bash
cd ../contracts
aiken build
# Generates plutus.json
```

---

## 3.3. Mint CIP-68 NFT

### Command
```bash
python mint_nft.py \
  --name "MyNFT001" \
  --image "ipfs://QmExample123..." \
  --desc "My first CIP-68 NFT"
```

### Workflow chi tiết

#### Step 1: Load wallets
```python
# Generate hoặc load từ mnemonic
issuer_skey, issuer_vkey, _, _ = generate_or_load_wallet("issuer.mnemonic")
user_skey, user_vkey, _, _ = generate_or_load_wallet("user.mnemonic")
```

#### Step 2: Create policy (Native Script)
```python
# Load policy keys
policy_skey, policy_vkey, policy_key_hash = create_or_load_policy_keys()

# Build native script
pub_key_policy = ScriptPubkey(policy_key_hash)
native_script = ScriptAll([pub_key_policy])
policy_id = native_script.hash()
```

**Native Script structure:**
```json
{
  "type": "all",
  "scripts": [
    {
      "type": "sig",
      "keyHash": "abc123..."
    }
  ]
}
```

#### Step 3: Build token names
```python
# PPBL approach: string concatenation
ref_token_name = "100" + "MyNFT001"  # "100MyNFT001"
user_token_name = "222" + "MyNFT001" # "222MyNFT001"
```

#### Step 4: Get script address
```python
# Load validator
validator = load_plutus_script("update_metadata.update_metadata")

# Apply policy_id parameter
parameterized_validator = apply_params_to_script(
    "update_metadata.update_metadata",
    policy_id.hex()
)

# Get address
script_hash = plutus_script_hash(parameterized_validator)
script_addr = Address(script_hash, network=Network.TESTNET)
```

#### Step 5: Create datum
```python
datum = create_cip68_datum(
    image_url="ipfs://QmExample123...",
    description="My first CIP-68 NFT"
)
```

**Datum structure:**
```python
@dataclass
class CIP68Datum(PlutusData):
    CONSTR_ID = 0
    image_url: bytes
    description: bytes
```

#### Step 6: Build transaction
```python
builder = TransactionBuilder(context)
builder.add_input_address(issuer_addr)

# Mint tokens
builder.mint = MultiAsset({
    policy_id: Asset({
        ref_token_name: 1,
        user_token_name: 1,
    })
})

# Add native script
builder.native_scripts = [native_script]

# Output 1: Reference token → script
builder.add_output(
    TransactionOutput(
        address=script_addr,
        amount=Value(
            coin=3_000_000,  # 3 ADA (có datum)
            multi_asset={policy_id: Asset({ref_token_name: 1})}
        ),
        datum=datum,
    )
)

# Output 2: User token → user wallet
builder.add_output(
    TransactionOutput(
        address=user_addr,
        amount=Value(
            coin=2_000_000,  # 2 ADA
            multi_asset={policy_id: Asset({user_token_name: 1})}
        ),
    )
)

# Set TTL
builder.ttl = context.last_block_slot + 1000
```

#### Step 7: Sign và submit
```python
# Sign với issuer + policy key
signed_tx = builder.build_and_sign(
    signing_keys=[issuer_skey, policy_skey],
    change_address=issuer_addr
)

# Submit
tx_hash = context.submit_tx(signed_tx.to_cbor())
```

### Output example
```
============================================================
CIP-68 NFT Minting (PPBL Approach - Native Script)
============================================================

[1] Connecting to Cardano network...
    Network: preview

[2] Loading wallets...
    Issuer: addr_test1qp0w79aen4gek54u5hmq4wpzvwla4as4w0zjtqneu2vdkrh5...
    User:   addr_test1qqdpq8qm24gh27mkjkrmpc5nkdnm8lexejxsqqk7t6lschh...

[3] Setting up minting policy (Native Script)...
    Policy Key Hash: abc123def456...
    Policy ID: 7fd86d5ade2db175fd2e491e117ac1fed4989c6ae5bf48c1be0a6b37

[4] Building token names...
    Reference token: 100MyNFT001
    User token:      222MyNFT001

[5] Getting validator script address...
    Applying policy ID parameter to validator...
    Script address: addr_test1wzftspa9w7erqrz5x8xxnrx7yk7lhp9harcmc2cgkr4ra9...

[6] Creating CIP-68 datum...
    Image: ipfs://QmExample123...
    Description: My first CIP-68 NFT

[7] Building mint transaction...

[8] Signing transaction...
    Transaction ID: a1b2c3d4...
    Size: 1856 bytes
    Fee: 0.23 ADA

[9] Submitting transaction...
    ✓ Transaction submitted!
    TX Hash: a1b2c3d4e5f6...
    
    View on explorer:
    https://preview.cardanoscan.io/transaction/a1b2c3d4e5f6...
    
    Your CIP-68 NFT:
    - Policy ID: 7fd86d5ade2db175fd2e491e117ac1fed4989c6ae5bf48c1be0a6b37
    - Reference token: 7fd86d5a...100MyNFT001
    - User token:      7fd86d5a...222MyNFT001
    
    Reference token locked at: addr_test1wzftspa9w7erqr...
    User token sent to: addr_test1qqdpq8qm24gh27mkjk...

============================================================
Done!
============================================================
```

---

## 3.4. Update Metadata

*(Script update_nft.py sẽ được tạo trong phần tiếp theo)*

### Workflow update:
1. Find reference token UTxO at script address
2. Build redeemer với new metadata
3. Spend reference UTxO
4. Create new UTxO với same token + new datum
5. Include user token (222) to prove ownership
6. Sign và submit

---

## 3.5. Query NFT Info

```python
# Query script address
script_utxos = context.utxos(script_addr)

for utxo in script_utxos:
    # Check if contains reference token
    for policy_id, assets in utxo.output.amount.multi_asset.items():
        for asset_name, quantity in assets.items():
            if asset_name.payload.startswith(b'100'):
                # Found reference token
                datum = utxo.output.datum
                # Decode datum
                ...
```

---

## 3.6. Common Issues & Solutions

### Issue 1: "Address does not have any UTxOs"
**Solution:** Request tADA from faucet
- Preview: https://docs.cardano.org/cardano-testnets/tools/faucet/
- Cần ít nhất 10 tADA cho mint transaction

### Issue 2: "plutus.json not found"
**Solution:** Build Aiken contracts
```bash
cd contracts
aiken build
```

### Issue 3: "PPViewHashesDontMatch"
**Solution:** Đảm bảo dùng same context cho build và submit
```python
# Good
context = BlockFrostChainContext(...)
builder = TransactionBuilder(context)
tx = builder.build(...)
context.submit_tx(tx)

# Bad - different contexts
context1 = BlockFrostChainContext(...)
builder = TransactionBuilder(context1)
context2 = BlockFrostChainContext(...)
context2.submit_tx(tx)  # ✗ Fails
```

### Issue 4: "FeeTooSmallUTxO"
**Solution:** Tăng min ADA cho outputs có datum
```python
# Reference output cần nhiều ADA hơn (vì có datum)
MIN_ADA_SCRIPT_OUTPUT = 3_000_000  # 3 ADA
```

---

## 3.7. Best Practices

### 1. Wallet Management
```python
# Lưu mnemonic an toàn
# Không commit lên git
# Add to .gitignore:
*.mnemonic
.env
```

### 2. Error Handling
```python
try:
    tx_hash = context.submit_tx(signed_tx)
except TransactionFailedException as e:
    # Parse error message
    if "FeeTooSmall" in str(e):
        print("Increase fee")
    elif "BadInputs" in str(e):
        print("UTxO already spent")
    ...
```

### 3. Transaction Monitoring
```python
# Wait for confirmation
import time

print(f"Waiting for confirmation...")
for i in range(30):
    try:
        tx_info = context._api.transaction(tx_hash)
        if tx_info:
            print(f"✓ Confirmed in block {tx_info.block_height}")
            break
    except:
        pass
    time.sleep(10)
```

---

**Next:** [Module 4: Frontend với Next.js + Mesh](./04-frontend-guide.md)
