# CIP-68 NFT Operations Guide

Hướng dẫn chi tiết về các operations có thể thực hiện với CIP-68 NFTs.

---

## 📋 Table of Contents

1. [Mint - Tạo NFT mới](#1-mint---tạo-nft-mới)
2. [Query - Xem thông tin NFT](#2-query---xem-thông-tin-nft)
3. [Update - Cập nhật metadata](#3-update---cập-nhật-metadata)
4. [Burn - Xóa NFT](#4-burn---xóa-nft)

---

## 1. Mint - Tạo NFT mới

### Mục đích
Tạo một CIP-68 NFT pair mới (reference token + user token).

### Command

```bash
python nft_manager.py mint [--debug] [--no-submit]
```

### Hoặc

```bash
python mint_nft.py [--debug] [--no-submit]
```

### Flow

1. **Load/Generate Keys**
   - Issuer key (sign transaction, có quyền mint/burn)
   - User key (nhận user token)

2. **Build Validators**
   - Store validator (parameterized với issuer PKH)
   - Mint policy (parameterized với store hash + issuer PKH)

3. **Create Token Names**
   - Generate unique 28-byte asset name
   - Build ref token: `0x00000064` + asset_name
   - Build user token: `0x000000de` + asset_name

4. **Create Metadata Datum**
   ```python
   {
       "metadata": [
           ["name", "My NFT"],
           ["description", "..."],
           ["image", "ipfs://..."]
       ],
       "version": 1,
       "extra": b""
   }
   ```

5. **Build Transaction**
   - Input: Issuer's UTXOs
   - Mint: +1 ref token, +1 user token
   - Output 1: Ref token → store (with inline datum)
   - Output 2: User token → user wallet
   - Redeemer: `MintAction.Mint` (CONSTR_ID = 0)
   - Required signers: issuer + user

6. **Submit**
   - Sign with both keys
   - Submit to blockchain
   - Return transaction hash

### Output Example

```
============================================================
CIP-68 Simple NFT Minting Example
============================================================

[1] Setting up blockchain context...
[2] Loading keys...
   Issuer PKH: 5eef17b99d519b52bca5f60ab82263bfdaf61573c5258279e298db0e
   User PKH: f07cb499e2a01e35faa74c105500045d38cea56bd0276e2732c89e66
   
[3] Building parameterized validators...
   Store Hash: 3985838f092d1a55a55949cdbcd3975116692d3afbaf46867dc15424
   Policy ID: 7212c8f7f86ba20db8fcb8f98c917af7551e117ba3f1733ecf8e0e3c
   
[4] Creating token names...
   Ref token name: 00000064fa162d668ccc93d272544f0e554b5783eccf8f42a59a87059d2e60b4
   User token name: 000000defa162d668ccc93d272544f0e554b5783eccf8f42a59a87059d2e60b4
   
[5] Creating metadata...
[6] Building transaction...
[7] Signing transaction...
   Transaction ID: abc123...
   
[8] Submitting transaction...
   ✓ Transaction submitted successfully!
   TX Hash: abc123...
   
   View on explorer:
   https://preprod.cardanoscan.io/transaction/abc123...
   
   Your NFT tokens:
   - Reference token: 7212c8f7....00000064fa162d...
   - User token: 7212c8f7....000000defa162d...
```

### Validator Checks (On-chain)

Mint policy validates:
1. ✅ Exactly 2 tokens minted (qty = 1 each)
2. ✅ One has label 100, one has label 222
3. ✅ Both share same 28-byte suffix
4. ✅ Ref token goes to store address
5. ✅ Ref token has inline datum
6. ✅ Issuer signed transaction

---

## 2. Query - Xem thông tin NFT

### Mục đích
Lấy thông tin về một NFT đã mint, bao gồm metadata, locations, và UTxO details.

### Command

```bash
python nft_manager.py query <policy_id> <asset_name_hex>
```

### Hoặc

```bash
python query_nft.py <policy_id> <asset_name_hex>
```

### Parameters

- `policy_id`: Policy ID của NFT (hex, 56 characters)
- `asset_name_hex`: 28-byte asset name suffix (hex, 56 characters)

### Example

```bash
python nft_manager.py query 7212c8f7f86ba20db8fcb8f98c917af7551e117ba3f1733ecf8e0e3c fa162d668ccc93d272544f0e554b5783eccf8f42a59a87059d2e60b4
```

### Flow

1. **Connect to blockchain**
2. **Rebuild validators** (to get store address)
3. **Build token names** from asset_name
4. **Search for reference token** at store address
5. **Decode metadata** from inline datum
6. **Display information**

### Output Example

```
======================================================================
CIP-68 NFT Query
======================================================================

[1] Connecting to blockchain...
[2] Rebuilding validators...
   Store Address: addr_test1wquctqu0pyk354d9t9yum0xnjag3v6fd8ta6735x0hq4gfqp2w9qx

[3] Token Information:
   Policy ID: 7212c8f7f86ba20db8fcb8f98c917af7551e117ba3f1733ecf8e0e3c
   Asset Name Suffix: fa162d668ccc93d272544f0e554b5783eccf8f42a59a87059d2e60b4
   Reference Token: 00000064fa162d668ccc93d272544f0e554b5783eccf8f42a59a87059d2e60b4
   User Token: 000000defa162d668ccc93d272544f0e554b5783eccf8f42a59a87059d2e60b4

[4] Searching for tokens...

======================================================================
RESULTS
======================================================================

📍 Reference Token (Label 100):
   ✓ Found at: addr_test1wquctqu0pyk354d9t9yum0xnjag3v6fd8ta6735x0hq4gfqp2w9qx
   UTxO: 8e22fd01a8aba91804f469ca6f13046bf38b4d5715e41f834f594b21d6cc8dc6#0
   ADA Amount: 2.000000 ADA

📋 Metadata:
{
  "metadata": [
    {"name": "My Simple CIP-68 NFT"},
    {"description": "A simple CIP-68 NFT created with PyCardano"},
    {"image": "ipfs://QmExample123456789"},
    {"artist": "Aiken & PyCardano Tutorial"}
  ],
  "version": 1,
  "extra": ""
}

👤 User Token (Label 222):
   ℹ User token location unknown (could be in any wallet after transfer)
   Full asset ID: 7212c8f7...000000defa162d...
   Check on explorer or use wallet to locate

======================================================================

💡 Tip: View full details on Cardano explorer:
   https://preprod.cardanoscan.io/token/7212c8f7...00000064fa162d...
======================================================================
```

---

## 3. Update - Cập nhật metadata

### Mục đích
Update metadata của NFT bằng cách spend reference token và recreate với datum mới.

### Command

```bash
python nft_manager.py update <policy_id> <asset_name_hex> [--debug] [--no-submit]
```

### Hoặc

```bash
python update_nft.py <policy_id> <asset_name_hex> [--debug] [--no-submit]
```

### Parameters

- `policy_id`: Policy ID của NFT
- `asset_name_hex`: 28-byte asset name suffix

### Flow

1. **Load issuer key** (cần để sign)
2. **Rebuild validators**
3. **Find reference token UTxO** at store address
4. **Create new metadata datum**
5. **Build transaction:**
   - Input: Issuer's UTXOs + reference token UTxO
   - Spend reference token from store (with Update redeemer)
   - Output: Reference token back to store with NEW datum
   - Required signer: issuer

6. **Submit transaction**

### Validator Checks

Store validator validates:
- ✅ Issuer signed transaction (Update action)

### Output Example

```
============================================================
CIP-68 NFT Metadata Update
============================================================

[1] Setting up...
   Issuer PKH: 5eef17b9...

[2] Rebuilding validators...
   Store Address: addr_test1wquctqu0...

[3] Finding reference token UTxO...
   Policy ID: 7212c8f7...
   Ref token name: 00000064fa162d...
   Looking for UTxO at: addr_test1wquctqu0...
   ✓ Found reference token at:
     TxHash: 8e22fd01a8aba91804f469ca6f13046bf38b4d5715e41f834f594b21d6cc8dc6
     Index: 0

[4] Creating new metadata...
   New metadata: {
       "name": "Updated CIP-68 NFT",
       "description": "Metadata updated via PyCardano",
       "image": "ipfs://QmNewHash123456789",
       "updated_at": "2024-11-01",
       "version": "2.0"
   }

[5] Building update transaction...
[6] Signing transaction...
   Transaction ID: def456...

[7] Submitting transaction...
   ✓ Metadata updated successfully!
   TX Hash: def456...
   
   View on explorer:
   https://preprod.cardanoscan.io/transaction/def456...
```

### Important Notes

- ⚠️ **Chỉ reference token bị affect** - User token không thay đổi
- ⚠️ **Cần issuer signature** - Chỉ issuer mới có quyền update
- ⚠️ **Reference token tetap ở store** - Địa chỉ không đổi
- ℹ️ **User có thể trade user token** - Ownership transfer không affect metadata

---

## 4. Burn - Xóa NFT

### Mục đích
Permanently remove cả reference và user tokens khỏi circulation.

### Command

```bash
python nft_manager.py burn <policy_id> <asset_name_hex> [--debug] [--no-submit]
```

### Hoặc

```bash
python burn_nft.py <policy_id> <asset_name_hex> [--debug] [--no-submit]
```

### Parameters

- `policy_id`: Policy ID của NFT
- `asset_name_hex`: 28-byte asset name suffix

### Flow

1. **Load keys** (issuer + user)
2. **Rebuild validators**
3. **Find both tokens:**
   - Reference token at store address
   - User token at user wallet
4. **Build transaction:**
   - Inputs: Issuer's UTXOs + ref token UTxO + user token UTxO
   - Spend ref token from store (Burn redeemer)
   - Spend user token from user wallet
   - Mint: -1 ref token, -1 user token (burn)
   - Mint redeemer: `MintAction.Burn` (CONSTR_ID = 1)
   - Required signers: issuer + user

5. **Submit transaction**

### Validator Checks

- **Store validator**: Issuer signed (Burn action)
- **Mint policy**: Issuer signed (Burn action)

### Output Example

```
============================================================
CIP-68 NFT Burn
============================================================

[1] Setting up...
   Issuer Address: addr_test1qrc8edye...
   User Address: addr_test1qrc8edye...

[2] Rebuilding validators...
   Policy ID: 7212c8f7f86ba20db8fcb8f98c917af7551e117ba3f1733ecf8e0e3c
   Store Address: addr_test1wquctqu0...

[3] Finding tokens to burn...
   Ref token: 00000064fa162d...
   User token: 000000defa162d...
   ✓ Found reference token at: 8e22fd01...#0
   ✓ Found user token at: abc123...#1

[4] Building burn transaction...
[5] Signing transaction...
   Transaction ID: xyz789...

[6] Submitting transaction...
   ✓ Tokens burned successfully!
   TX Hash: xyz789...
   
   View on explorer:
   https://preprod.cardanoscan.io/transaction/xyz789...
   
   Both tokens have been removed from circulation.
```

### Important Notes

- ⚠️ **Irreversible operation** - Không thể undo sau khi burn
- ⚠️ **Cần cả 2 tokens** - Phải có access đến cả ref và user token
- ⚠️ **Cần cả 2 signatures** - Issuer + user phải sign
- ℹ️ **ADA được return** - Min ADA locked với tokens sẽ được trả về
- ⚠️ **Policy vẫn tồn tại** - Chỉ tokens bị remove, có thể mint tokens khác với cùng policy

---

## 🔍 Troubleshooting Common Issues

### Issue 1: "Reference token not found"

**Nguyên nhân:**
- Token đã bị burn
- Sai policy ID hoặc asset name
- Token bị move khỏi store address

**Giải pháp:**
```bash
# Verify token trên explorer
https://preprod.cardanoscan.io/token/<policy_id><token_name>

# Query lại với đúng parameters
python nft_manager.py query <correct_policy_id> <correct_asset_name>
```

### Issue 2: "User token not found"

**Nguyên nhân:**
- User đã transfer token đi
- Token ở wallet khác

**Giải pháp:**
- Check wallet history trên explorer
- Nếu đã transfer, cần người đang hold token thực hiện burn

### Issue 3: "Transaction failed: Issuer signature missing"

**Nguyên nhân:**
- Issuer key không đúng
- Key file bị corrupt

**Giải pháp:**
```bash
# Check issuer PKH
cat issuer.mnemonic  # Verify có mnemonic

# Hoặc regenerate keys (⚠️ chỉ nếu chưa mint NFT nào)
rm issuer.mnemonic
python nft_manager.py mint  # Sẽ tạo key mới
```

### Issue 4: "Evaluation failed"

**Nguyên nhân:**
- Validator logic không pass
- Token names sai format
- Datum structure không đúng

**Giải pháp:**
```bash
# Run với --debug để xem chi tiết
python nft_manager.py mint --debug --no-submit

# Check token names có đúng 32 bytes không
# Check labels có đúng big-endian 4 bytes không
```

---

## 📊 Operation Summary Table

| Operation | Ref Token | User Token | Requires | On-chain Action |
|-----------|-----------|------------|----------|-----------------|
| **Mint** | Created at store | Created at user wallet | Issuer + User sign | Mint +1 each, send to addresses |
| **Query** | Read from store | Check location | None (read-only) | No transaction |
| **Update** | Spent & recreated | Unchanged | Issuer sign | Spend + recreate ref token |
| **Burn** | Spent & burned | Spent & burned | Issuer + User sign | Mint -1 each, remove from circulation |

---

## 🎯 Best Practices

1. **Always query before update/burn** - Verify token tồn tại
2. **Use --no-submit for testing** - Build transaction nhưng không submit
3. **Keep mnemonic files safe** - Backup issuer.mnemonic và user.mnemonic
4. **Verify on explorer** - Check transaction status sau khi submit
5. **Use meaningful metadata** - Dễ identify NFT sau này
6. **Test on preprod first** - Đừng test trực tiếp trên mainnet

---

**Happy Building! 🚀**
