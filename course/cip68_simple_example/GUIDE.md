# CIP-68 Simple Example - Complete Tutorial

**Một implementation đơn giản, dễ hiểu về CIP-68 NFT trên Cardano**

## 🎯 Mục đích

Dự án này được tạo ra để:
1. ✅ Minh họa cách xây dựng CIP-68 NFT từ đầu đến cuối
2. ✅ Code rõ ràng, dễ đọc hơn các implementation phức tạp
3. ✅ Làm tài liệu tham khảo cho người mới học
4. ✅ Tránh các lỗi thường gặp (token name encoding, redeemer wrapping, etc.)

## 📁 Cấu trúc dự án

```
cip68_simple_example/
│
├── contract/                    # Smart contracts (Aiken)
│   ├── validators/
│   │   ├── mint_policy.ak      # Minting policy - kiểm soát việc mint/burn
│   │   └── store_validator.ak  # Store validator - lưu trữ reference token
│   ├── lib/
│   │   └── cip68.ak            # Utilities cho CIP-68 (labels, token names)
│   ├── aiken.toml
│   ├── plutus.json             # Output sau khi build
│   └── README.md
│
├── off_chain/                   # Python off-chain code  
│   ├── mint_nft.py             # Script chính để mint NFT
│   ├── config.py               # Configuration
│   ├── utils.py                # Helper functions
│   └── __init__.py
│
└── README.md                    # File này
```

## 🚀 Quick Start

### Bước 1: Build Smart Contracts

```bash
cd contract
aiken build
```

Lệnh này sẽ:
- Compile các validators từ Aiken → Plutus
- Tạo file `plutus.json` chứa compiled code
- Verify tất cả type checks pass

### Bước 2: Cài đặt Dependencies

```bash
# Python dependencies
pip install pycardano

# Aiken (nếu chưa có)
# https://aiken-lang.org/installation-instructions
```

### Bước 3: Cấu hình

Tạo hoặc edit `off_chain/config.py`:

```python
NETWORK = "preprod"  # hoặc "mainnet"
BLOCKFROST_PROJECT_ID = "your_blockfrost_project_id"
```

Lấy Blockfrost API key miễn phí tại: https://blockfrost.io/

### Bước 4: Sử dụng NFT Manager!

```bash
cd off_chain

# Mint NFT mới
python nft_manager.py mint

# Query thông tin NFT
python nft_manager.py query <policy_id> <asset_name>

# Update metadata
python nft_manager.py update <policy_id> <asset_name>

# Burn NFT
python nft_manager.py burn <policy_id> <asset_name>
```

## 💡 CIP-68 là gì?

CIP-68 định nghĩa một chuẩn cho NFTs trên Cardano với **2 tokens**:

### 1. Reference Token (Label 100)
- Token name: `0x00000064` + 28 bytes asset name
- **Locked** tại store validator
- Chứa **metadata** dưới dạng inline datum
- **Không thể transfer** - chỉ có thể update hoặc burn

### 2. User Token (Label 222)
- Token name: `0x000000de` + cùng 28 bytes asset name
- Gửi đến **user's wallet**
- **Freely tradeable** - đại diện cho quyền sở hữu NFT
- Metadata được link qua reference token

### Tại sao lại dùng 2 tokens?

- **Reference token**: Lưu trữ metadata on-chain, immutable hoặc controlled update
- **User token**: Đại diện ownership, có thể trade tự do
- **Separation of concerns**: Metadata logic tách biệt khỏi ownership logic

## 🔍 Chi tiết Technical

### Token Name Format

```
[4 bytes: label (big-endian)][28 bytes: asset name] = 32 bytes total
```

Ví dụ:
- Ref token: `0x00000064` + `fa162d...` = `00000064fa162d...` (32 bytes)
- User token: `0x000000de` + `fa162d...` = `000000defa162d...` (32 bytes)

⚠️ **Critical**: Labels phải là 4-byte big-endian integers!

```python
# ✓ ĐÚNG
label = 100
label_bytes = label.to_bytes(4, byteorder='big')  # 0x00000064

# ✗ SAI
label_bytes = bytes([100, 0])  # Chỉ 2 bytes!
```

### Metadata Datum Structure

```aiken
pub type Metadata {
  metadata: List<(ByteArray, ByteArray)>,  // Key-value pairs
  version: Int,                             // Version number
  extra: ByteArray,                        // Extra data
}
```

Trong Python (PyCardano):

```python
@dataclass
class CIP68Datum(PlutusData):
    CONSTR_ID = 0
    metadata: List[List[bytes]]  # [[key1, val1], [key2, val2], ...]
    version: int
    extra: bytes
```

### Validator Parameters

#### Mint Policy

Parameters:
```aiken
pub type MintParams {
  store_validator_hash: ByteArray,  // Hash của store validator
  issuer_pkh: ByteArray,            // Public key hash của issuer
}
```

Validation khi Mint:
1. ✅ Exactly 2 tokens minted (quantities = 1 each)
2. ✅ One has label 100 (ref), one has label 222 (user)
3. ✅ Both share same 28-byte asset name suffix
4. ✅ Ref token goes to store validator with inline datum
5. ✅ Transaction signed by issuer

#### Store Validator

Parameters:
```aiken
pub type StoreParams {
  issuer_pkh: ByteArray,  // Ai được phép update/burn
}
```

Validation:
- Update: Issuer must sign
- Burn: Issuer must sign

## 📝 Code Examples

### 1. Mint NFT (Full Flow)

```bash
python nft_manager.py mint
```

Hoặc sử dụng script riêng:

```python
from off_chain import mint_nft

# Script tự động handle mọi thứ:
# - Key generation/loading
# - Validator parameterization  
# - Token name construction
# - Datum creation
# - Transaction building
# - Submission

mint_nft.main()
```

### 2. Query NFT Information

```bash
python nft_manager.py query 7212c8f7f86ba20db8fcb8f98c917af7551e117ba3f1733ecf8e0e3c fa162d668ccc93d272544f0e554b5783eccf8f42a59a87059d2e60b4
```

Output sẽ hiển thị:
- Reference token location và metadata
- User token information
- UTxO details
- Explorer links

### 3. Update Metadata

```bash
python nft_manager.py update 7212c8f7... fa162d...
```

Flow:
1. Tìm reference token tại store address
2. Spend reference token UTxO
3. Tạo datum mới với metadata updated
4. Send reference token back to store với datum mới
5. User token không thay đổi

### 4. Burn NFT

```bash
python nft_manager.py burn 7212c8f7... fa162d...
```

Flow:
1. Tìm cả reference token (tại store) và user token (tại user wallet)
2. Spend cả hai UTxOs
3. Mint -1 của mỗi token (burn)
4. Tokens bị remove khỏi circulation vĩnh viễn

### 5. Tạo Custom Metadata

```python
metadata = {
    "name": "My Awesome NFT",
    "description": "Created with Aiken + PyCardano",
    "image": "ipfs://Qm...",
    "attributes": "custom_data_here",
}

datum = utils.create_cip68_datum(metadata)
```

### 6. Build Token Names

```python
import hashlib
from off_chain.config import LABEL_100, LABEL_222, ASSET_NAME_LENGTH

# Unique 28-byte identifier
asset_name = hashlib.sha256(b"MyUniqueNFT").digest()[:ASSET_NAME_LENGTH]

# Build CIP-68 token names
ref_token = utils.build_token_name(LABEL_100, asset_name)
user_token = utils.build_token_name(LABEL_222, asset_name)
```

## 🐛 Troubleshooting

### Build errors

```bash
# Nếu Aiken báo lỗi module không tìm thấy
cd contract
rm -rf build/
aiken build
```

### Transaction fails với "ScriptFailures"

Kiểm tra:
1. Token names có đúng 32 bytes không? (4-byte label + 28-byte suffix)
2. Labels có đúng big-endian không? (`label.to_bytes(4, byteorder='big')`)
3. Reference token có được gửi đến store address không?
4. Inline datum có được set đúng không?
5. Required signers có bao gồm issuer không?

### Import errors

```bash
# Đảm bảo bạn ở trong directory chứa config.py và utils.py
cd off_chain
python mint_nft.py
```

## 🎓 Learning Path

Nếu bạn mới bắt đầu, đọc theo thứ tự:

1. **`contract/README.md`** - Hiểu smart contracts
2. **`contract/lib/cip68.ak`** - CIP-68 utilities
3. **`contract/validators/mint_policy.ak`** - Minting logic
4. **`contract/validators/store_validator.ak`** - Store logic
5. **`off_chain/config.py`** - Configuration
6. **`off_chain/utils.py`** - Off-chain helpers
7. **`off_chain/mint_nft.py`** - Minting flow
8. **`off_chain/update_nft.py`** - Update flow
9. **`off_chain/burn_nft.py`** - Burn flow
10. **`off_chain/query_nft.py`** - Query flow
11. **`off_chain/nft_manager.py`** - Unified CLI tool

## 🔄 Complete Workflow Example

```bash
# 1. Mint một NFT
python nft_manager.py mint
# Output: Policy ID: 7212c8f7...
#         Asset name: fa162d...

# 2. Query để xem thông tin
python nft_manager.py query 7212c8f7... fa162d...
# Shows: metadata, locations, UTxOs

# 3. Update metadata
python nft_manager.py update 7212c8f7... fa162d...
# Reference token datum updated

# 4. Query lại để verify
python nft_manager.py query 7212c8f7... fa162d...
# Shows: NEW metadata

# 5. Burn khi không cần nữa
python nft_manager.py burn 7212c8f7... fa162d...
# Both tokens removed from circulation
```

## 🔗 Resources

- [CIP-68 Specification](https://cips.cardano.org/cips/cip68/)
- [Aiken Documentation](https://aiken-lang.org/)
- [PyCardano Documentation](https://pycardano.readthedocs.io/)
- [Blockfrost API](https://docs.blockfrost.io/)

## ⚖️ License

MIT License - Free to use for learning and production

## 🙏 Credits

Created as a simple, educational example for the PyCardano + Aiken community.

---

**Happy Building! 🚀**

Nếu bạn gặp issues hoặc có questions, feel free to open an issue hoặc contribute!
