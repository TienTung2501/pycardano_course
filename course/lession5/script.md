
---

# 🎓 Lesson 5 — Consolidate UTxOs (Gộp UTxO)

## 1️⃣ Mục tiêu bài học

**Consolidate UTxO** = gộp **nhiều UTxO nhỏ** của một địa chỉ → **1 UTxO lớn duy nhất**

### Vì sao cần làm điều này?

Trong Cardano:

* Mỗi **UTxO = 1 input**
* Càng nhiều input →
  ❌ phí cao
  ❌ giao dịch phức tạp
  ❌ dễ fail khi build tx lớn

👉 Các ví, quỹ, bot giao dịch **luôn định kỳ consolidate UTxO**

---

## 2️⃣ Điểm mấu chốt của bài này

⚠️ **KHÔNG dùng**:

```python
builder.add_input_address(address)
```

Vì:

* PyCardano sẽ **tự chọn UTxO tối ưu**
* ❌ không đảm bảo gom hết

✅ **Cách đúng khi consolidate**:

> Chủ động **add từng UTxO làm input**
> → “ăn sạch” toàn bộ UTxO hiện có

---

## 3️⃣ Chuẩn bị môi trường

### 📦 Cài thư viện

```bash
pip install pycardano blockfrost-python python-dotenv
```

---

## 4️⃣ Chuẩn bị file `.env`

📄 **File `.env` (BẮT BUỘC)**

```env
# Blockfrost project ID
BLOCKFROST_PROJECT_ID=your_blockfrost_key_here

# Chọn network
# testnet | preview | preprod | mainnet
BLOCKFROST_NETWORK=testnet

# Mnemonic ví (24 từ)
MNEMONIC=daring hybrid aerobic pair history dentist park race nothing twist leave autumn notice animal spring safe render matter exact wasp hole cotton drift evil

# (không dùng trong bài này, để sẵn cho các lesson sau)
IPFS_API=.....
```

⚠️ **Lưu ý quan trọng cho học viên**

* `.env` **KHÔNG commit lên Git**
* mnemonic = toàn bộ tài sản của bạn

---

## 5️⃣ Import thư viện

```python
import os
import sys
from blockfrost import ApiError, ApiUrls, BlockFrostApi
from dotenv import load_dotenv
from pycardano import *
```

### Giải thích:

| Thư viện     | Mục đích                 |
| ------------ | ------------------------ |
| `dotenv`     | Load biến môi trường     |
| `blockfrost` | Query UTxO, submit tx    |
| `pycardano`  | Build & sign transaction |

---

## 6️⃣ Load biến môi trường

```python
load_dotenv()

network = os.getenv("BLOCKFROST_NETWORK")
wallet_mnemonic = os.getenv("MNEMONIC")
blockfrost_api_key = os.getenv("BLOCKFROST_PROJECT_ID")
```

👉 Script **KHÔNG hard-code secrets**

---

## 7️⃣ Chọn mạng Cardano

```python
if network == "testnet":
    base_url = ApiUrls.preview.value
    cardano_network = Network.TESTNET
else:
    base_url = ApiUrls.mainnet.value
    cardano_network = Network.MAINNET
```

### Giải thích:

* Blockfrost **preview = testnet mới**
* `Network.TESTNET` ảnh hưởng:

  * address format
  * fee
  * tx validation

---

## 8️⃣ Khôi phục khóa từ mnemonic (CỰC QUAN TRỌNG)

```python
new_wallet = crypto.bip32.HDWallet.from_mnemonic(wallet_mnemonic)
```

👉 Cardano dùng chuẩn **CIP-1852**

---

### 🔑 Derive payment key

```python
payment_key = new_wallet.derive_from_path(
    "m/1852'/1815'/0'/0/0"
)
```

| Thành phần | Ý nghĩa           |
| ---------- | ----------------- |
| 1852'      | HD wallet Cardano |
| 1815'      | Coin type ADA     |
| 0'         | Account           |
| 0          | Payment           |
| 0          | Index             |

---

### 🔑 Derive staking key

```python
staking_key = new_wallet.derive_from_path(
    "m/1852'/1815'/0'/2/0"
)
```

---

### Chuyển sang signing key

```python
payment_skey = ExtendedSigningKey.from_hdwallet(payment_key)
staking_skey = ExtendedSigningKey.from_hdwallet(staking_key)
```

👉 Signing key = thứ **ký giao dịch**

---

## 9️⃣ Tạo địa chỉ ví chính

```python
main_address = Address(
    payment_part=payment_skey.to_verification_key().hash(),
    staking_part=staking_skey.to_verification_key().hash(),
    network=cardano_network,
)
```

📌 Đây là **địa chỉ sẽ gom UTxO về**

```python
print(f"Địa chỉ được tạo: {main_address}")
```

---

## 🔟 Lấy toàn bộ UTxO của địa chỉ

```python
api = BlockFrostApi(
    project_id=blockfrost_api_key,
    base_url=base_url
)
```

```python
utxos = api.address_utxos(main_address)
```

### Xử lý lỗi thường gặp

```python
if e.status_code == 404:
    print("Địa chỉ không có UTxO nào.")
```

👉 404 = address rỗng

---

## 1️⃣1️⃣ ChainContext (bắt buộc với pycardano)

```python
cardano = BlockFrostChainContext(
    project_id=blockfrost_api_key,
    base_url=base_url
)
```

👉 Cung cấp:

* protocol params
* slot
* fee rules

---

## 1️⃣2️⃣ TransactionBuilder cho consolidate

```python
builder = TransactionBuilder(cardano)
```

---

## 1️⃣3️⃣ Add TẤT CẢ UTxO làm input

🔥 **Đây là phần quan trọng nhất của bài**

```python
for utxo in utxos:
```

---

### Tạo input

```python
tx_input = TransactionInput.from_primitive(
    [utxo.tx_hash, utxo.tx_index]
)
```

---

### Xử lý Value (ADA + multi-asset)

```python
value = Value.from_primitive(
    [int(utxo.amount[0].quantity)] +
    [
        (asset.unit, int(asset.quantity))
        for asset in utxo.amount[1:]
        if asset.unit != "lovelace"
    ]
)
```

📌 Giải thích:

* `amount` luôn là **list**
* phần tử đầu = `lovelace`
* phần sau = native assets / NFT

---

### Tạo output giả để wrap thành UTxO

```python
tx_output = TransactionOutput(main_address, value)
utxo_obj = UTxO(tx_input, tx_output)
```

---

### Add input

```python
builder.add_input(utxo_obj)
```

🔥 Kết quả:

> TẤT CẢ UTxO → input

---

## 1️⃣4️⃣ Build & sign transaction

```python
signed_tx = builder.build_and_sign(
    [payment_skey],
    change_address=main_address
)
```

📌 PyCardano sẽ:

* tự tính fee
* tạo **1 output đổi**
* gom toàn bộ value

---

## 1️⃣5️⃣ Thống kê trước khi submit

### Tổng ADA

```python
balance_lovelace = sum(
    int(a.quantity)
    for u in utxos
    for a in u.amount
    if a.unit == "lovelace"
)
```

---

### In thông tin

```python
print(f"Số dư địa chỉ:\t {balance_lovelace / 1_000_000} ADA")
print(f"Số đầu vào:\t {len(signed_tx.transaction_body.inputs)}")
print(f"Số đầu ra:\t {len(signed_tx.transaction_body.outputs)}")
print(f"Phí:\t\t {signed_tx.transaction_body.fee / 1_000_000} ADA")
```

---

## 1️⃣6️⃣ Submit giao dịch

```python
tx_id = cardano.submit_tx(signed_tx.to_cbor())
print(f"Giao dịch đã gửi! ID: {tx_id}")
```

---

## 1️⃣7️⃣ Các lỗi thường gặp

| Lỗi                   | Nguyên nhân       |
| --------------------- | ----------------- |
| BadInputsUTxO         | UTxO đã bị tiêu   |
| ValueNotConservedUTxO | Tx không cân bằng |
| InsufficientFee       | Quá nhiều input   |

---

## 🧠 Tổng kết bài học

✔ Hiểu rõ bản chất **UTxO model**
✔ Biết cách **chủ động gom UTxO**
✔ Hiểu cách xử lý **multi-asset**
✔ Viết script **chuẩn production**

---
