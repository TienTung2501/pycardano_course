---

# 🎓 Lesson 7 — Burn NFTs (Đốt NFT)

---

## 1️⃣ Mục tiêu bài học

Trong bài này, học viên sẽ:

✅ Burn (đốt) **một danh sách NFT đã mint trước đó**
✅ Dùng **đúng policy key** đã dùng khi mint
✅ Hiểu rõ:

* Burn NFT thực chất là gì trong ledger
* Vì sao **số lượng âm = burn**
* Vì sao **phải ký policy signing key**

---

## 2️⃣ Burn NFT trên Cardano — Sự thật kỹ thuật

### ❗ Cardano không có “delete token”

👉 **Burn = mint với số lượng âm**

| Hành động | Ledger |
| --------- | ------ |
| Mint      | `+1`   |
| Burn      | `-1`   |

Ví dụ:

```python
my_asset[nft] = -1
```

📌 Sau tx:

* Tổng cung NFT = 0
* NFT **biến mất vĩnh viễn**

---

## 3️⃣ Điều kiện bắt buộc để burn

| Điều kiện              | Bắt buộc |
| ---------------------- | -------- |
| Có policy signing key  | ✅        |
| NFT tồn tại trong UTxO | ✅        |
| Policy giống lúc mint  | ✅        |

❌ Không có policy key → **KHÔNG burn được**

---

## 4️⃣ Tổng quan luồng xử lý

```text
.env
 ↓
Wallet keys (payment / staking)
 ↓
Load policy keys (đã mint)
 ↓
ScriptPubkey → ScriptAll → policy_id
 ↓
MultiAsset (asset_name → -1)
 ↓
TransactionBuilder
 ↓
mint (burn) + native_scripts
 ↓
build_and_sign (wallet key + policy key)
 ↓
submit
```

---

## 5️⃣ Nạp biến môi trường

```python
load_dotenv()
network = os.getenv("BLOCKFROST_NETWORK")
wallet_mnemonic = os.getenv("MNEMONIC")
blockfrost_api_key = os.getenv("BLOCKFROST_PROJECT_ID")
```

📌 Nhắc lại:

* mnemonic = quyền sở hữu ví
* policy key = quyền kiểm soát token

---

## 6️⃣ Danh sách NFT cần burn

```python
assets = [
    {"name": "Pycardano_test_NFT_001"},
    {"name": "Pycardano_test_NFT_002"},
    {"name": "Pycardano_test_NFT_003"},
    {"name": "Pycardano_test_NFT_004"},
    {"name": "Pycardano_test_NFT_005"},
]
```

👉 Có thể:

* burn 1 NFT
* burn hàng loạt
* burn theo danh sách động

---

## 7️⃣ Map network

```python
if network == "testnet":
    base_url = ApiUrls.preview.value
    cardano_network = Network.TESTNET
else:
    base_url = ApiUrls.mainnet.value
    cardano_network = Network.MAINNET
```

---

## 8️⃣ Derive ví chủ sở hữu NFT

```python
new_wallet = crypto.bip32.HDWallet.from_mnemonic(wallet_mnemonic)
```

```python
payment_key = new_wallet.derive_from_path("m/1852'/1815'/0'/0/0")
staking_key = new_wallet.derive_from_path("m/1852'/1815'/0'/2/0")
```

📌 Ví này:

* trả phí
* ký UTxO
* **KHÔNG nhất thiết phải là ví mint**

---

## 9️⃣ Địa chỉ chứa NFT

```python
main_address = Address(
    payment_part=payment_skey.to_verification_key().hash(),
    staking_part=staking_skey.to_verification_key().hash(),
    network=cardano_network,
)
```

👉 NFT phải nằm trong UTxO của địa chỉ này

---

## 🔟 Kiểm tra UTxO

```python
utxos = api.address_utxos(main_address)
```

📌 Nếu ví không có NFT → burn fail

---

## 1️⃣1️⃣ ChainContext

```python
cardano = BlockFrostChainContext(
    project_id=blockfrost_api_key,
    base_url=base_url
)
```

---

## 1️⃣2️⃣ Load policy keys (CỰC QUAN TRỌNG)

```python
policy_skey_path = "keys/policy.skey"
policy_vkey_path = "keys/policy.vkey"
```

```python
policy_signing_key = PaymentSigningKey.load(policy_skey_path)
policy_verification_key = PaymentVerificationKey.load(policy_vkey_path)
```

🔥 **Phải là policy key lúc mint**

❌ Tạo key mới → policy_id khác → burn fail

---

## 1️⃣3️⃣ Dựng Native Script & Policy ID

```python
pub_key_policy = ScriptPubkey(
    policy_verification_key.hash()
)
```

```python
policy = ScriptAll([pub_key_policy])
policy_id = policy.hash()
```

👉 Policy ID **KHÔNG đổi**

---

## 1️⃣4️⃣ Tạo MultiAsset để burn

### Asset container

```python
my_asset = Asset()
my_nft = MultiAsset()
```

---

### Thêm NFT với số lượng âm

```python
for asset in assets:
    asset_name = asset["name"]
    nft = AssetName(asset_name.encode("utf-8"))
    my_asset[nft] = -1
```

📌 Mỗi NFT:

* burn đúng **1 đơn vị**
* không thể burn > số đang tồn tại

---

### Gắn vào policy

```python
my_nft[policy_id] = my_asset
```

---

## 1️⃣5️⃣ Gắn script & mint (burn)

```python
builder.native_scripts = [policy]
builder.mint = my_nft
```

👉 `mint` dùng cho **cả mint & burn**

---

## 1️⃣6️⃣ Input để trả phí

```python
builder.add_input_address(main_address)
```

📌 Builder:

* tự chọn UTxO ADA
* **không tự chọn UTxO chứa NFT**

---

## 1️⃣7️⃣ Build & sign (2 chữ ký)

```python
signed_tx = builder.build_and_sign(
    [payment_skey, policy_signing_key],
    change_address=main_address
)
```

| Khóa         | Vai trò       |
| ------------ | ------------- |
| payment_skey | chi UTxO      |
| policy_skey  | hợp lệ policy |

---

## 1️⃣8️⃣ Submit giao dịch

```python
tx_id = cardano.submit_tx(signed_tx.to_cbor())
```

🎉 NFT bị **burn vĩnh viễn**

---

## 1️⃣9️⃣ Thông tin giao dịch

```python
print(f"Fee: {signed_tx.transaction_body.fee/1_000_000} ADA")
```

📌 Burn NFT:

* vẫn tốn phí
* **không thu lại min-ADA**

---

## 2️⃣0️⃣ Các lỗi thường gặp (thực chiến)

| Lỗi                             | Nguyên nhân              |
| ------------------------------- | ------------------------ |
| ScriptWitnessNotValidatingUTXOW | thiếu policy key         |
| AssetNotPresent                 | NFT không có trong input |
| ValueNotConservedUTxO           | sai ADA/min-ADA          |
| BadInputsUTxO                   | UTxO đã bị dùng          |

---

## 🧠 Tổng kết Lesson 7

✔ Burn = mint số lượng âm
✔ Policy ID **bất biến**
✔ Mất policy key = mất quyền burn
✔ Burn hoàn tất vòng đời NFT

---