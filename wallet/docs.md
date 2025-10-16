Tuyệt vời. Dưới đây là file **`README.md`** hoàn chỉnh cho module `wallet_manager` – đúng chuẩn tài liệu dự án (Markdown đẹp, dễ hiểu, có hướng dẫn setup, sử dụng CLI, và phần giải thích chi tiết).
Bạn chỉ cần lưu nội dung này vào file `wallet/README.md`.

---

# 💼 PyCardano Wallet Manager

Quản lý ví Cardano bằng **PyCardano** + **Blockfrost API**.
Cung cấp các chức năng HD Wallet đầy đủ: tạo mnemonic, sinh khóa, tạo địa chỉ Shelley, kiểm tra số dư và UTxO.

---

## 🚀 Tính năng chính

| Chức năng         | Mô tả                                       |
| ----------------- | ------------------------------------------- |
| 🔐 Tạo HD Wallet  | Sinh mnemonic (BIP39), derive khóa CIP-1852 |
| 💾 Xuất khóa      | Xuất Payment / Stake key ra file `.key`     |
| 🏦 Tạo địa chỉ    | Tạo địa chỉ Shelley (payment + stake)       |
| 🔍 Kiểm tra số dư | Lấy balance từ Blockfrost                   |
| 📦 Lấy UTxO       | Truy vấn UTxO hiện có của ví                |
| ⚙️ CLI tiện dụng  | Có thể chạy lệnh trực tiếp từ terminal      |

---

## 📂 Cấu trúc thư mục

```
project_root/
 ├─ wallet/
 │   ├─ wallet_manager.py
 │   ├─ README.md
 │   └─ __init__.py
 ├─ config/
 │   └─ settings.py
 ├─ .env
 └─ requirements.txt
```

---

## ⚙️ Cấu hình môi trường `.env`

Tạo file `.env` tại thư mục gốc và thêm thông tin sau:

```bash
# 24 từ mnemonic testnet hoặc mainnet
MNEMONIC="twelve words of your test wallet ..."

# Project ID của Blockfrost (tạo trên https://blockfrost.io)
BLOCKFROST_PROJECT_ID="preprod123456..."

# Mạng lưới: TESTNET hoặc MAINNET
NETWORK="TESTNET"
```

---

## 🧠 Cài đặt & Chuẩn bị

```bash
# 1. Cài đặt thư viện
pip install pycardano blockfrost-python python-dotenv

# 2. Kiểm tra cấu hình
python -m wallet.wallet_manager
```

---

## 💡 Cách sử dụng CLI

Chạy trực tiếp bằng Python module:

```bash
python -m wallet.wallet_manager <command>
```

### Danh sách lệnh

| Lệnh                | Mô tả                                                                |
| ------------------- | -------------------------------------------------------------------- |
| `generate_mnemonic` | Sinh mnemonic mới                                                    |
| `get_address`       | In ra địa chỉ ví (bech32)                                            |
| `get_stake`         | Lấy stake address                                                    |
| `export_keys`       | Xuất khóa payment/stake ra thư mục `wallet_data/`                    |
| `get_balance`       | Kiểm tra số dư ví qua Blockfrost                                     |
| `get_utxos`         | Truy vấn danh sách UTxO của địa chỉ                                  |
| `show_mnemonic`     | Hiển thị mnemonic hiện tại (⚠️ không dùng cho môi trường production) |

---

## 🧩 Ví dụ sử dụng

### 1️⃣ Tạo mnemonic mới

```bash
python -m wallet.wallet_manager generate_mnemonic
```

Kết quả:

```
zebra tourist visual arena... (24 từ)
```

---

### 2️⃣ Lấy địa chỉ ví

```bash
python -m wallet.wallet_manager get_address
```

Kết quả:

```
addr_test1qz9... (địa chỉ bech32)
```

---

### 3️⃣ Xuất khóa ra file

```bash
python -m wallet.wallet_manager export_keys
```

Tạo thư mục `wallet_data/`:

```
wallet_data/
 ├─ payment.skey
 ├─ payment.vkey
 ├─ stake.skey
 └─ stake.vkey
```

---

### 4️⃣ Kiểm tra số dư

```bash
python -m wallet.wallet_manager get_balance
```

Kết quả:

```
Số dư: 3200000 Lovelace
```

---

### 5️⃣ Lấy danh sách UTxO

```bash
python -m wallet.wallet_manager get_utxos
```

Ví dụ:

```
- TX Hash: 1a2b3c4d... Amount: 2000000
- TX Hash: 9e8f7a6b... Amount: 1200000
```

---

## 🧱 Cấu trúc khóa HD (CIP-1852)

| Thành phần  | Path                   | Mục đích                    |
| ----------- | ---------------------- | --------------------------- |
| Payment key | `m/1852'/1815'/0'/0/0` | Giao dịch thanh toán        |
| Stake key   | `m/1852'/1815'/0'/2/0` | Đăng ký stake / nhận thưởng |

---

## 🌐 Blockfrost API

Tích hợp qua [blockfrost-python](https://github.com/blockfrost/blockfrost-python):

* `get_balance()` → Gọi endpoint `/address/{address}`
* `get_utxos()` → Gọi endpoint `/address/{address}/utxos`
* Hỗ trợ **preprod / mainnet** tự động theo biến `NETWORK`

---

## 🧩 Mô hình hoạt động

```
+-------------+        +-------------------+         +---------------------+
|  Wallet CLI | <----> |  WalletManager.py | <-----> | Blockfrost API Node |
+-------------+        +-------------------+         +---------------------+
         |                        |
         |                        |
         v                        v
   Local Key Files          Blockchain Data
```

---

## 🔒 Lưu ý bảo mật

* **Không commit file `.env` hoặc các khóa `.skey` lên Git.**
* Mnemonic và private key chỉ nên dùng cho **ví testnet** trong quá trình phát triển.
* Nếu cần ví mainnet → nên sinh khóa offline bằng [cardano-cli](https://docs.cardano.org).

---

## 🧭 Đóng góp & Phát triển thêm

Các tính năng có thể mở rộng trong tương lai:

* [ ] Tạo policy script & minting key
* [ ] Gửi giao dịch từ ví (build + sign + submit)
* [ ] Đăng ký stake / delegation
* [ ] Tích hợp với ví phần cứng (Ledger, Trezor)

---

## 👨‍💻 Tác giả

**Cardano Vietnam Dev Education Project**
PyCardano Demo Series – Milestone 2: *Setup & Wallet Integration*

---

Bạn có muốn mình thêm phần **🎬 Video Script (7 phút, voice hướng dẫn + lời thoại)** cho phần này luôn không?
Nó sẽ bám theo format milestone trước (“Setup môi trường PyCardano”) và nối tiếp vào “Tạo ví + Kết nối Blockfrost”.
