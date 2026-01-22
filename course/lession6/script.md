---

# 🎓 Lesson 6 — Mint Fungible Token (FT) with Native Script

---

## 1️⃣ Mục tiêu bài học

Trong bài này, học viên sẽ:

✅ Phát hành **100 Fungible Token (FT)**
✅ Dùng **Native Script (không Plutus)**
✅ Policy kiểm soát bằng **public key (ScriptPubkey)**
✅ Hiểu rõ:

* Policy ID là gì
* Vì sao mint phải ký **2 khóa**
* Min-ADA cho token được tính thế nào

---

## 2️⃣ Native Token trên Cardano — Nhận thức nền tảng

### Cardano KHÔNG có smart contract khi mint token

👉 Token Cardano:

* Không cần Plutus
* Không cần contract
* **Native Asset = ledger-level**

### Native Script = luật phát hành token

Ví dụ:

* “Chỉ ai giữ private key X mới được mint/burn”
* “Chỉ được mint trước slot Y”

Trong bài này, ta dùng **luật đơn giản nhất**:

> 🔐 **Ai giữ policy signing key thì được mint**

---

## 3️⃣ Tổng quan luồng xử lý (mental model)

```text
.env
 ↓
Wallet keys (payment / staking)
 ↓
Policy keys (riêng cho token)
 ↓
ScriptPubkey → ScriptAll → policy_id
 ↓
MultiAsset (policy_id + asset_name + quantity)
 ↓
TransactionBuilder
 ↓
mint + native_scripts + output
 ↓
build_and_sign (wallet key + policy key)
 ↓
submit
```

---

## 4️⃣ Nạp .env & thiết lập mạng

```python
load_dotenv()
network = os.getenv("BLOCKFROST_NETWORK")
wallet_mnemonic = os.getenv("MNEMONIC")
blockfrost_api_key = os.getenv("BLOCKFROST_PROJECT_ID")
```

📌 **Tách config khỏi code**

* Dễ deploy
* Dễ đổi ví / network
* An toàn

---

### Chọn network

```python
if network == "testnet":
    base_url = ApiUrls.preview.value
    cardano_network = Network.TESTNET
else:
    base_url = ApiUrls.mainnet.value
    cardano_network = Network.MAINNET
```

👉 `Network.TESTNET` ảnh hưởng:

* format address
* tx fee rules
* slot, epoch

---

## 5️⃣ Khôi phục ví từ mnemonic

```python
new_wallet = crypto.bip32.HDWallet.from_mnemonic(wallet_mnemonic)
```

### Derive payment key

```python
payment_key = new_wallet.derive_from_path("m/1852'/1815'/0'/0/0")
```

### Derive staking key

```python
staking_key = new_wallet.derive_from_path("m/1852'/1815'/0'/2/0")
```

📌 Đây là **chuẩn CIP-1852**

---

### Chuyển sang signing key

```python
payment_skey = ExtendedSigningKey.from_hdwallet(payment_key)
staking_skey = ExtendedSigningKey.from_hdwallet(staking_key)
```

---

## 6️⃣ Tạo địa chỉ ví phát hành token

```python
main_address = Address(
    payment_part=payment_skey.to_verification_key().hash(),
    staking_part=staking_skey.to_verification_key().hash(),
    network=cardano_network,
)
```

👉 Địa chỉ này:

* trả phí
* nhận token
* nhận ADA đổi

---

## 7️⃣ Kiểm tra UTxO & số dư ADA

```python
utxos = api.address_utxos(main_address)
```

### Tính tổng ADA

```python
total_ada = sum(int(utxo.amount[0].quantity) for utxo in utxos)
```

📌 Lưu ý:

* `amount[0]` luôn là `lovelace`
* Native asset nằm ở `amount[1:]`

---

## 8️⃣ ChainContext — bắt buộc cho pycardano

```python
cardano = BlockFrostChainContext(
    project_id=blockfrost_api_key,
    base_url=base_url
)
```

👉 PyCardano cần:

* protocol params
* fee model
* slot hiện tại

---

## 9️⃣ Chuẩn bị policy keys (CỰC KỲ QUAN TRỌNG)

### Tạo thư mục `keys/`

```python
keys_dir = os.path.join(os.path.dirname(__file__), "keys")
os.makedirs(keys_dir, exist_ok=True)
```

📌 Trong thực tế:

* `keys/` **KHÔNG commit**
* backup offline

---

### Định nghĩa file policy

```python
policy_skey_path = os.path.join(keys_dir, "policy.skey")
policy_vkey_path = os.path.join(keys_dir, "policy.vkey")
```

---

### Tạo policy key nếu chưa tồn tại

```python
if not exists(policy_skey_path) or not exists(policy_vkey_path):
    payment_key_pair = PaymentKeyPair.generate()
```

📌 **Policy key ≠ wallet key**

👉 Bạn có thể:

* chuyển policy cho DAO
* multisig
* governance

---

## 🔑 Vì sao policy key quan trọng?

| Ai giữ policy key | Có quyền    |
| ----------------- | ----------- |
| Bạn               | mint / burn |
| Người khác        | ❌ không     |

👉 **Mất policy.skey = mất quyền kiểm soát token**

---

## 🔟 Dựng Native Script & Policy ID

### Load policy keys

```python
policy_signing_key = PaymentSigningKey.load(policy_skey_path)
policy_verification_key = PaymentVerificationKey.load(policy_vkey_path)
```

---

### ScriptPubkey

```python
pub_key_policy = ScriptPubkey(
    policy_verification_key.hash()
)
```

👉 Luật:

> “Transaction PHẢI được ký bởi key này”

---

### ScriptAll

```python
policy = ScriptAll([pub_key_policy])
```

📌 ScriptAll = **tất cả điều kiện phải đúng**

---

### Policy ID

```python
policy_id = policy.hash()
policy_id_hex = policy_id.payload.hex()
```

👉 **Policy ID = hash(script)**
👉 Token **sống cùng policy**

---

## 1️⃣1️⃣ Định nghĩa token (MultiAsset)

### Tên token

```python
asset_name = "Pycardano_test_COINP_003"
token = AssetName(asset_name.encode("utf-8"))
```

📌 Asset name:

* max 32 bytes
* UTF-8 → bytes

---

### MultiAsset

```python
new_asset = Asset()
new_asset[token] = 100
```

```python
multiasset = MultiAsset()
multiasset[policy_id] = new_asset
```

👉 Cấu trúc:

```text
policy_id
 └── asset_name → quantity
```

---

## 1️⃣2️⃣ TransactionBuilder cho mint

```python
builder = TransactionBuilder(cardano)
builder.add_input_address(main_address)
```

👉 **Mint token không cần gom UTxO**

* builder tự chọn input tối ưu

---

### Gắn native script & mint

```python
builder.native_scripts = [policy]
builder.mint = multiasset
```

📌 Nếu thiếu:

* `native_scripts` → ❌ script invalid
* `mint` → ❌ không mint

---

## 1️⃣3️⃣ Tính min-ADA cho output chứa token

```python
min_val = min_lovelace(
    cardano,
    output=TransactionOutput(main_address, Value(0, multiasset))
)
```

### Vì sao cần min-ADA?

👉 Cardano **KHÔNG cho phép UTxO chỉ chứa token**

* Token **phải đi kèm ADA**
* Số ADA phụ thuộc:

  * số token
  * độ dài asset name
  * số policy

---

## 1️⃣4️⃣ Kiểm tra đủ ADA không

```python
if total_ada < min_val + 2_000_000:
```

📌 2 ADA dự phòng:

* phí tx
* UTxO đổi

---

## 1️⃣5️⃣ Thêm output chứa token

```python
builder.add_output(
    TransactionOutput(
        main_address,
        Value(min_val, multiasset)
    )
)
```

👉 Token + ADA tối thiểu → về ví phát hành

---

## 1️⃣6️⃣ TTL (Time To Live)

```python
builder.ttl = cardano.last_block_slot + 1000
```

📌 TTL:

* chống replay
* tx hết hạn nếu không confirm

---

## 1️⃣7️⃣ Build & sign (ĐIỂM QUAN TRỌNG)

```python
signed_tx = builder.build_and_sign(
    [payment_skey, policy_signing_key],
    change_address=main_address
)
```

🔥 **PHẢI ký 2 khóa**:

| Khóa         | Vì sao        |
| ------------ | ------------- |
| payment_skey | chi UTxO      |
| policy_skey  | hợp lệ policy |

❌ Thiếu 1 khóa → tx invalid

---

## 1️⃣8️⃣ In thông tin giao dịch

```python
print(f"Token phát hành: 100 {asset_name}")
print(f"ADA tối thiểu: {min_val / 1_000_000} ADA")
```

---

## 1️⃣9️⃣ Submit giao dịch

```python
tx_id = cardano.submit_tx(signed_tx.to_cbor())
```

🎉 **Token được mint vĩnh viễn trên Cardano ledger**

---

## 2️⃣0️⃣ Các lỗi thường gặp

| Lỗi                             | Nguyên nhân      |
| ------------------------------- | ---------------- |
| ScriptWitnessNotValidatingUTXOW | thiếu policy key |
| ValueNotConservedUTxO           | sai min-ADA      |
| AssetNameTooLong                | >32 bytes        |
| InsufficientFunds               | không đủ ADA     |

---

## 🧠 Tổng kết Lesson 6

✔ Hiểu **Native Token = ledger-level**
✔ Phân biệt **wallet key vs policy key**
✔ Biết dựng **ScriptPubkey / ScriptAll**
✔ Biết mint FT **đúng chuẩn production**

---
