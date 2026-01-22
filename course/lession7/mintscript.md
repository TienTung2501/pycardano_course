
---

# 🎓 Lesson 8 — Mint Multiple NFTs with CIP-721 Metadata

> (Lưu ý: dù bạn ghi “Lesson 7”, về mặt nội dung đây **nên là Lesson 8** vì:
>
> * Lesson 6: FT
> * Lesson 7: Burn
> * Lesson 8: NFT + metadata)

---

## 1️⃣ Mục tiêu bài học

Sau bài này, học viên sẽ:

✅ Mint **nhiều NFT trong 1 transaction**
✅ Mỗi NFT có **metadata CIP-721 hợp lệ**
✅ Hiểu:

* Cấu trúc metadata 721
* Cách gắn metadata vào `auxiliary_data`
* Vì sao policy_id là “root namespace” của NFT

---

## 2️⃣ CIP-721 là gì? (Concept bắt buộc)

### 📌 CIP-721 = tiêu chuẩn metadata NFT Cardano

Ledger **KHÔNG quan tâm metadata**, nhưng:

* Marketplace
* Explorer
* Indexer

→ **chỉ đọc NFT nếu metadata đúng CIP-721**

---

### 🔑 Cấu trúc chuẩn

```json
{
  "721": {
    "<policy_id>": {
      "<asset_name>": {
        "name": "...",
        "image": "...",
        "...": "..."
      }
    }
  }
}
```

📌 Ghi nhớ:

* `721` = magic number
* `policy_id` = namespace
* `asset_name` = key cấp NFT

---

## 3️⃣ Tổng quan luồng xử lý

```text
.env
 ↓
Wallet keys
 ↓
Policy keys
 ↓
ScriptPubkey → ScriptAll → policy_id
 ↓
CIP-721 metadata
 ↓
MultiAsset (mỗi NFT = 1)
 ↓
min-ADA cho output
 ↓
build_and_sign (wallet + policy key)
 ↓
submit
```

---

## 4️⃣ Nạp biến môi trường

```python
load_dotenv()
network = os.getenv("BLOCKFROST_NETWORK")
wallet_mnemonic = os.getenv("MNEMONIC")
blockfrost_api_key = os.getenv("BLOCKFROST_PROJECT_ID")
```

👉 Không khác các lesson trước → **tái sử dụng pattern**

---

## 5️⃣ Chuẩn bị dữ liệu NFT (demo game-like)

```python
types = ["lion", "elephant", "panda", "sloth", "tiger", "wolf"]
```

```python
assets = [
    {
        "name": "Pycardano_test_NFT_001",
        "attack": "...",
        "speed": "...",
        "defense": "...",
        "health": "...",
        "type": "...",
    },
    ...
]
```

📌 Đây là:

* **off-chain metadata**
* Trong dự án thật: đọc từ DB / JSON / CSV

---

## 6️⃣ Map network

```python
if network == "testnet":
    base_url = ApiUrls.preview.value
    cardano_network = Network.TESTNET
```

📌 Preview testnet = best practice hiện tại

---

## 7️⃣ Derive ví phát hành NFT

```python
new_wallet = crypto.bip32.HDWallet.from_mnemonic(wallet_mnemonic)
```

```python
payment_key = new_wallet.derive_from_path("m/1852'/1815'/0'/0/0")
staking_key = new_wallet.derive_from_path("m/1852'/1815'/0'/2/0")
```

👉 Ví này:

* trả phí
* nhận NFT
* giữ UTxO chứa NFT

---

## 8️⃣ Kiểm tra UTxO (bắt buộc)

```python
utxos = api.address_utxos(main_address)
```

📌 Mint NFT **luôn cần ADA**:

* min-ADA
* fee
* change

---

## 9️⃣ ChainContext

```python
cardano = BlockFrostChainContext(
    project_id=blockfrost_api_key,
    base_url=base_url
)
```

---

## 🔟 Chuẩn bị policy keys

### Tạo thư mục `keys/`

```python
keys_dir = os.path.join(os.path.dirname(__file__), "keys")
os.makedirs(keys_dir, exist_ok=True)
```

---

### Tạo hoặc tải policy key

```python
if not exists(policy_skey_path):
    payment_key_pair = PaymentKeyPair.generate()
```

📌 **Policy key sống lâu hơn code**

* Dùng lại để burn
* Dùng lại để remint (nếu cho phép)

---

## 1️⃣1️⃣ Dựng Native Script & Policy ID

```python
pub_key_policy = ScriptPubkey(policy_verification_key.hash())
policy = ScriptAll([pub_key_policy])
policy_id = policy.hash()
policy_id_hex = policy_id.payload.hex()
```

👉 **policy_id = identity NFT collection**

---

## 1️⃣2️⃣ Chuẩn bị Asset & MultiAsset

```python
my_asset = Asset()
my_nft = MultiAsset()
```

---

### Mint mỗi NFT = 1

```python
nft1 = AssetName(asset_name.encode("utf-8"))
my_asset[nft1] = 1
```

📌 NFT:

* quantity = **1**
* > 1 → không còn là NFT

---

## 1️⃣3️⃣ Dựng metadata CIP-721

### Root metadata

```python
metadata = {721: {policy_id_hex: {}}}
```

📌 Đây là **khung bắt buộc**

---

### Gắn metadata từng NFT

```python
metadata[721][policy_id_hex][asset_name] = {
    "name": asset_name,
    "type": asset["type"],
    "attack": asset["attack"],
    "speed": asset["speed"],
    "defense": asset["defense"],
    "health": asset["health"],
}
```

👉 Marketplace đọc **chính xác key này**

---

## 1️⃣4️⃣ Gắn metadata vào transaction

```python
auxiliary_data = AuxiliaryData(
    AlonzoMetadata(metadata=Metadata(metadata))
)
builder.auxiliary_data = auxiliary_data
```

📌 Cardano era ≥ Alonzo:

* metadata nằm trong `auxiliary_data`
* **không ảnh hưởng validation**

---

## 1️⃣5️⃣ Gắn mint + script

```python
builder.native_scripts = native_scripts
builder.mint = my_nft
```

🔥 Thiếu 1 trong 2 → mint fail

---

## 1️⃣6️⃣ Tính min-ADA cho output chứa NHIỀU NFT

```python
min_val = min_lovelace(
    cardano,
    output=TransactionOutput(main_address, Value(0, my_nft))
)
```

📌 Min-ADA tăng theo:

* số NFT
* độ dài asset name
* số policy

---

## 1️⃣7️⃣ Thêm output trả NFT về ví

```python
builder.add_output(
    TransactionOutput(main_address, Value(min_val, my_nft))
)
```

👉 Toàn bộ NFT nằm trong **1 UTxO**

---

## 1️⃣8️⃣ Input & build/sign

```python
builder.add_input_address(main_address)
```

```python
signed_tx = builder.build_and_sign(
    [payment_skey, policy_signing_key],
    change_address=main_address
)
```

📌 **2 chữ ký bắt buộc**:

* payment key → chi ADA
* policy key → hợp lệ mint

---

## 1️⃣9️⃣ Submit transaction

```python
tx_id = cardano.submit_tx(signed_tx.to_cbor())
```

🎉 NFT xuất hiện trên:

* explorer
* wallet
* marketplace (sau index)

---

## 2️⃣0️⃣ Các lỗi rất hay gặp

| Lỗi                             | Nguyên nhân      |
| ------------------------------- | ---------------- |
| MetadataTooLarge                | metadata > 16KB  |
| AssetNameTooLong                | > 32 bytes       |
| ScriptWitnessNotValidatingUTXOW | thiếu policy key |
| ValueNotConservedUTxO           | sai min-ADA      |

---

## 🧠 Tổng kết Lesson 8

✔ Biết mint **nhiều NFT / 1 tx**
✔ Hiểu cấu trúc **CIP-721 chuẩn marketplace**
✔ Phân biệt **on-chain asset vs off-chain metadata**
✔ Code đạt mức **production-ready NFT project**

---
