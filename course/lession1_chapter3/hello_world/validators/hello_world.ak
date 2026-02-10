"""
Xin chào mọi người! Chào mừng mọi người đã đến với video
tiếp theo trong khóa học lập trình Pycardano của chúng tôi.
Trong video này, chúng ta sẽ xây dựng một validator đơn giản
kiểu "Hello, World!" để minh họa cách hoạt động của validators
trong Aiken và sử dụng Pycardano để tương tác với chúng.

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

## CÀI ĐẶT AIKEN---


### Windows (PowerShell)

```powershell
irm https://install.aiken-lang.org/windows.ps1 | iex
```

### macOS / Linux

```bash
curl -fsSL https://install.aiken-lang.org | bash
```

Restart terminal
Kiểm tra:

```bash
aiken --version
```

Thấy version = **xong 100%**

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


"""
// Bước 1: Tạo file validator hello_world.ak trong thư mục validators
// Bước 2: Bắt đầu viết code validator
// 1: Import các module cần thiết
use aiken/collection/list
use aiken/crypto.{VerificationKeyHash}
use cardano/transaction.{OutputReference, Transaction}
// 2: Định nghĩa Datum và Redeemer
pub type Datum {
  owner: VerificationKeyHash, // Địa chỉ người sở hữu
}

pub type Redeemer {
  msg: ByteArray, // Định nghĩa thông điệp
}
// 3: Viết validator
validator hello_world {
  // Hàm kiểm tra điều kiện khi chi tiêu UTXO
  spend( // Tham số hàm
    datum: Option<Datum>, // datum từ UTXO
    redeemer: Redeemer, //  redeemer từ giao dịch
    _own_ref: OutputReference,// Tham chiếu đến UTXO hiện tại không sử dụng
    self: Transaction, // Giao dịch hiện tại 
  ) {
    expect Some(Datum { owner }) = datum // Giải nén datum để lấy owner
    const PROJECT_SALT = #"cip68_nfts_example_v1" // Mỗi một lần build, 
    //tạo một PROJECT_SALT khác nhau để tránh trùng lặp tạo ra cùng một địa chỉ validator
    let _ = PROJECT_SALT
    let must_say_hello = redeemer.msg == "Hello, World!" // Kiểm tra thông điệp
    let must_be_signed = list.has(self.extra_signatories, owner) // Kiểm tra chữ ký
    must_say_hello && must_be_signed // Trả về true nếu cả hai điều kiện đều đúng
  }
}
