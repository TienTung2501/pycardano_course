"""
Xin chào mọi người! Chào mừng mọi người đã đến với video
tiếp theo trong khóa học lập trình Pycardano của chúng tôi.
Trong video này, chúng ta sẽ xây dựng một validator đơn giản
kiểu "Hello, World!" để minh họa cách hoạt động của validators
trong Aiken và sử dụng Pycardano để tương tác với chúng.

## CÀI ĐẶT AIKEN---

---

# 🔥 DÙNG DUY NHẤT INSTALLER SCRIPT – HƯỚNG DẪN FULL

> Áp dụng cho **Aiken v1.1.19** (prebuilt binary) lý do không dùng phiên bản mới nhất
Để chạy ổn định chúng ta nên dùng phiên bản gần nhất nhưng không phải phiên bản mới nhất

---

## 🪟 WINDOWS (PowerShell)

---

### 1️⃣ Mở PowerShell

👉 Chuột phải → **Run as Administrator** (khuyến nghị)

---

### 2️⃣ Chạy DUY NHẤT 1 lệnh

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://github.com/aiken-lang/aiken/releases/download/v1.1.19/aiken-installer.ps1 | iex"
```

Script này sẽ:

* Tải `aiken.exe`
* Copy vào thư mục user
* Tự thêm PATH

---

### 3️⃣ Đóng PowerShell → mở lại

---

### 4️⃣ Kiểm tra

```powershell
aiken --version
```

👉 Nếu ra `1.1.19` → **HOÀN TẤT**

---

### 5️⃣ Test nhanh

```powershell
aiken new hello_aiken
cd hello_aiken
aiken build
```

---


# 🐧 UBUNTU (Shell)

### 0️⃣ Chuẩn bị

```bash
sudo apt update
sudo apt install -y curl ca-certificates
```

---

### 1️⃣ Chạy DUY NHẤT 1 lệnh

```bash
curl --proto '=https' --tlsv1.2 -LsSf https://github.com/aiken-lang/aiken/releases/download/v1.1.19/aiken-installer.sh | sh
```

Script này sẽ:

* Detect Ubuntu + CPU
* Download binary
* Copy vào `/usr/local/bin/aiken`
* Set executable

---

### 2️⃣ Reload shell

```bash
exec $SHELL
```

---

### 3️⃣ Kiểm tra

```bash
aiken --version
```

👉 Thấy `1.1.19` → **HOÀN TẤT**

---

### 4️⃣ Test nhanh

```bash
aiken new hello_aiken
cd hello_aiken
aiken build
```

---

### ⚠️ Nếu lỗi

* Network timeout
* Permission denied
* Script fail giữa chừng

👉 **Chuyển sang cài thủ công từ GitHub binary**

---

## 🧠 BẠN ĐANG LÀM GÌ THẬT SỰ?

Installer script = **shortcut** cho các bước này:

```
Download binary
→ chmod +x
→ move to PATH
→ done
```

Không có magic gì cả.

---


## KHỞI TẠO PROJECT

```bash
aiken new my_contract(thay tên project của bạn)
cd my_contract 
```

Cấu trúc chuẩn:

```
my_contract/
├─ aiken.toml
├─ lib/
│  └─ validator.ak
├─ tests/
```

---

## VIẾT & BUILD SMART CONTRACT

```bash
aiken build
```

Output dùng để deploy:

```
Tạo ra file plutus.json trong thư mục
```

---

## TEST

```bash
aiken check
```
// Bước 1: Tạo file validator hello_world.ak trong thư mục validators
// Bước 2: Bắt đầu viết code validator
Bước 1: Khởi tạo môi trường ảo
Chạy lệnh sau để tạo thư mục venv chứa môi trường riêng:
python -m venv venv


Bước 2: Kích hoạt môi trường (Activate)
Đây là điểm khác biệt chính so với Windows. Trên Linux/Ubuntu, bạn dùng lệnh source:
.\venv\Scripts\Activate.ps1


Khi thành công, bạn sẽ thấy tên môi trường (venv) 
xuất hiện phía trước dấu nhắc lệnh (prompt) trong terminal.
Bước 3. Cài đặt thư viện PyCardano
Khi đã ở trong môi trường (venv), 
việc cài đặt thư viện diễn ra rất nhanh chóng và an toàn.
Chạy lệnh:
pip install pycardano blockfrost-python python-dotenv

Bước 4 : Tạo file .env và điền biến môi trường
Trước tiên là phần chuẩn bị môi trường. Hãy chắc chắn rằng
bạn đã cài đặt Aiken và Pycardano. Bạn có thể làm theo hướng
dẫn cài đặt trong tài liệu chính thức của Aiken để cài aiken
cho máy tính của bạn. 

Đầu tiên chúng ta sẽ thực hiện kích hoạt môi trường ảo
giống như các bài giảng trước đó



"""