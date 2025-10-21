Tuyệt vời 💪
Dưới đây là file **`README.md`** hoàn chỉnh, được viết bằng **tiếng Việt**, cực kỳ chi tiết — đủ để người mới có thể hiểu, cài đặt, và chạy được dự án của bạn.

---

## 🧾 `README.md`

```markdown
# 🚀 PyCardano Course – Dự án học thực hành Cardano Blockchain với Python

Một dự án học tập hoàn chỉnh giúp bạn làm quen với **Cardano Blockchain** thông qua thư viện **PyCardano** và **Blockfrost API**.  
Dự án được tổ chức theo cấu trúc mô-đun, mỗi mô-đun tương ứng với một bài học trong khoá học thực chiến.

---

## 🌐 Tổng quan dự án

**PyCardano Course** giúp bạn:

- Kết nối với **Cardano Testnet** qua **Blockfrost API**
- Quản lý **ví (wallet)** bằng mnemonic hoặc file khóa
- Thực hiện **giao dịch gửi ADA**, **mint Fungible Token (FT)**, **mint NFT**, **Dynamic NFT (CIP-68)**
- Làm việc với **smart contract (Plutus / Aiken)**
- Lưu trữ dữ liệu trên **IPFS**
- Tích hợp **AI utils** (ví dụ: sinh metadata NFT bằng AI)
- Viết code có cấu trúc rõ ràng, dễ mở rộng và tái sử dụng

---
````

## 🏗️ Cấu trúc thư mục

````

pycardano_course/
│
├── .env                        # File cấu hình môi trường (API keys, network, paths)
├── requirements.txt             # Danh sách thư viện cần cài
├── main.py                      # File chạy chính (demo toàn hệ thống)
│
├── config/                      # ⚙️ Cấu hình Blockfrost, logging, settings
│   ├── blockfrost.py
│   ├── settings.py
│   ├── logging_config.py
│   └── **init**.py
│
├── wallet/                      # 👛 Quản lý ví, khóa, mnemonic
│   ├── wallet_manager.py
│   └── **init**.py
│
├── services/                    # 💼 Các dịch vụ blockchain
│   ├── transaction_service.py
│   ├── mint_service.py
│   ├── query_service.py
│   ├── nft_service.py
│   └── **init**.py
│
├── contracts/                   # 📜 Hợp đồng thông minh (Aiken/Plutus)
│   ├── helloworld/
│   ├── vesting/
│   └── **init**.py
│
├── utils/                       # 🧰 Tiện ích phụ (IPFS, AI, file handling)
│   ├── ipfs_utils.py
│   ├── ai_utils.py
│   ├── file_utils.py
│   └── **init**.py
│
├── data/                        # 💾 Chứa dữ liệu, metadata, ví, policy
│
├── module1/ ... module4/        # 🎓 Các bài học cụ thể
│   ├── setup_env.py
│   ├── send_ada.py
│   ├── mint_ft.py
│   ├── mint_nft.py
│   ├── smart_contract_demo.py
│
└── README.md                    # 📘 Tài liệu hướng dẫn (bạn đang đọc file này)

````

---

## ⚙️ Cài đặt môi trường

### 1️⃣ Clone dự án:
```bash
git clone https://github.com/<your-username>/pycardano_course.git
cd pycardano_course
````

### 2️⃣ Tạo và kích hoạt môi trường ảo:

```bash
python -m venv venv
source venv/bin/activate     # macOS / Linux
.\venv\Scripts\activate        # Windows

--> (venv) PS D:\Code\Catalyst Project\pycardano_course>
```

### 3️⃣ Cài đặt thư viện cần thiết:

```bash
python -m pip install -r requirements.txt
```

---

## 🔑 Cấu hình môi trường `.env`

Tạo file `.env` trong thư mục gốc, ví dụ:

```
# Blockfrost API
BLOCKFROST_PROJECT_ID=your_blockfrost_key_here
NETWORK=testnet   # hoặc mainnet

# Wallet
MNEMONIC="your wallet seed phrase here"

# Logging
LOG_LEVEL=INFO
```

👉 **Lưu ý:**

* Bạn có thể lấy `BLOCKFROST_PROJECT_ID` tại [https://blockfrost.io](https://blockfrost.io).
* Dự án mặc định dùng **Testnet**, không dùng tiền thật.
* Nếu bạn chưa có ví, có thể tạo bằng script trong `wallet/wallet_manager.py`.


---

### 🔍 Vậy nếu bạn *chưa có ví* thì nên làm gì?

Bạn **chưa có mnemonic**, nên file này vẫn hữu ích — chỉ cần **gọi hàm tạo mnemonic mới** có sẵn trong class này:

---

## 🪙 Tạo ví mới bằng file `wallet_manager.py` hiện tại

### 🔧 Bước 1 — Mở terminal tại thư mục dự án và chạy:

```bash
python wallet/wallet_manager.py
```

Nếu chưa có `.env` hoặc chưa khai báo `MNEMONIC`, bạn sẽ thấy thông báo lỗi:

```
Lỗi khi khởi tạo WalletManager: MNEMONIC chưa được cung cấp...
```

Không sao cả — vì bạn sẽ **tạo mnemonic mới** ngay sau đây.

---

### 🪄 Bước 2 — Sinh mnemonic mới (ngẫu nhiên 24 từ)

Chạy lệnh Python sau (trực tiếp trong terminal hoặc Python shell):

```python
from wallet.wallet_manager import WalletManager

new_mnemonic = WalletManager.generate_new_mnemonic()
print("🪄 Mnemonic mới của bạn:")
print(new_mnemonic)
```

Ví dụ kết quả:

```
🪄 Mnemonic mới của bạn:
ocean design tornado symbol major pigeon apple ... (24 từ)
```

---

### 📋 Bước 3 — Lưu mnemonic vào `.env`

Mở file `.env` ở thư mục gốc và thêm dòng này:

```
MNEMONIC="ocean design tornado symbol major pigeon apple ..."
NETWORK=testnet
BLOCKFROST_PROJECT_ID=your_blockfrost_key_here
```

> ⚠️ **CẢNH BÁO:**
>
> * Không chia sẻ mnemonic này công khai.
> * Chỉ dùng cho testnet, không dùng ví mainnet thật.
> * Không commit file `.env` lên GitHub.

---

### 🧩 Bước 4 — Kiểm tra ví hoạt động

Sau khi lưu `.env`, bạn chạy lại:

```bash
python wallet/wallet_manager.py
```

Kết quả ví dụ:

```
Wallet address: addr_test1qp5lm...
Mnemonic (KEEP SECRET): ocean design tornado symbo...
```

→ Giờ bạn đã có ví testnet hoạt động! 🎉
Bạn có thể dùng địa chỉ này để nhận ADA từ faucet:
🔗 [https://testnets.cardano.org/en/testnets/cardano/tools/faucet/](https://testnets.cardano.org/en/testnets/cardano/tools/faucet/)

---

### 💡 Gợi ý mở rộng

Nếu bạn muốn có một **CLI tiện dụng** cho người học (để tạo ví mới nhanh),
mình có thể giúp bạn tạo thêm file:

```
module1/create_wallet.py
```

Khi chạy:

```bash
python module1/create_wallet.py
```

→ Nó sẽ tự sinh mnemonic mới, hiển thị địa chỉ, và tự ghi sẵn vào `.env`.

---

👉 Bạn có muốn mình viết luôn file `module1/create_wallet.py` đó cho bạn không?
(rất hữu ích để người học dùng trong bài học đầu tiên của khoá học PyCardano).
```

---

## 💰 Nhận test ADA (Cardano Testnet)

1. Truy cập [Cardano Testnet Faucet](https://testnets.cardano.org/en/testnets/cardano/tools/faucet/)
2. Dán địa chỉ ví testnet của bạn.
3. Nhấn **Request funds** để nhận ADA test.

---

## 🧠 Cách chạy thử

### 🪙 Gửi ADA:

```bash
python module1/send_ada.py
```

### 🧾 Mint Fungible Token (FT):

```bash
python module2/mint_ft.py
```

### 🖼️ Mint NFT cơ bản:

```bash
python module3/mint_nft.py
```

### 🧠 Mint NFT động (CIP-68):

```bash
python module3/mint_dynamic_nft.py
```

### ⚙️ Demo Smart Contract:

```bash
python module4/smart_contract_demo.py
```

---

## 🧰 Tích hợp IPFS và AI

Dự án có các tiện ích để lưu trữ metadata trên **IPFS** (qua Pinata, NFT.Storage, v.v.),
và sinh dữ liệu metadata NFT bằng **AI (OpenAI API)**.

Ví dụ:

```python
from utils.ipfs_utils import upload_to_ipfs
from utils.ai_utils import generate_nft_metadata

metadata = generate_nft_metadata(prompt="Một chú mèo AI vui vẻ trong không gian")
ipfs_link = upload_to_ipfs("image.png")
```

---

## 🧩 Các dịch vụ chính

| Service              | Mô tả                                      |
| -------------------- | ------------------------------------------ |
| `TransactionService` | Tạo và gửi giao dịch ADA                   |
| `MintService`        | Mint Fungible Tokens (FT)                  |
| `NFTService`         | Mint, cập nhật, burn NFT (CIP-25 & CIP-68) |
| `QueryService`       | Truy vấn thông tin ví, giao dịch, block    |
| `WalletManager`      | Tạo, load, quản lý ví bằng mnemonic        |
| `BlockfrostConfig`   | Tạo context kết nối tới Blockfrost API     |
| `LoggingConfig`      | Cấu hình logging chuyên nghiệp             |

---

## 🧱 Smart Contract

Các ví dụ Plutus/Aiken nằm trong thư mục `contracts/`, gồm:

* `helloworld/`: hợp đồng cơ bản in ra “Hello, Cardano!”
* `vesting/`: hợp đồng vesting mẫu với thời gian khóa.

---

## 🧑‍💻 Đóng góp & phát triển thêm

Nếu bạn muốn mở rộng dự án:

* Thêm module mới (ví dụ: stake pool, voting, dApp backend)
* Kết nối với frontend React hoặc Streamlit dashboard
* Tích hợp AI sinh NFT tự động từ prompt

---

## 🧹 Dọn dẹp & reset môi trường

```bash
rm -rf __pycache__ data/policies data/wallets
```

---

## 📚 Tài liệu tham khảo

* [PyCardano Documentation](https://pycardano.readthedocs.io/en/latest/)
* [Blockfrost API Docs](https://docs.blockfrost.io/)
* [Cardano CIP Registry](https://cips.cardano.org/)
* [Aiken Documentation](https://aiken-lang.org/docs/)

---

## 🧡 Giấy phép

MIT License © 2025 – Dự án học tập và chia sẻ kiến thức Cardano.

```
Bạn có muốn mình **tạo file `README.md` thật (để tải về .zip hoặc copy nguyên thư mục)** không?  
Nếu có, mình sẽ **đóng gói toàn bộ project** (gồm các file bạn đã có + README) để bạn tải trực tiếp.
```
