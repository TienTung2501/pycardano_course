Xin chào mọi người! Chào mừng mọi người đã đến với video
tiếp theo trong khóa học lập trình Pycardano của chúng tôi.
Trong video này, chúng ta sẽ tiếp tục triển khai ví dụ cip 68
của chúng ta cụ thể là phần 
2. Thưc hiện code offchain code để tương tác với các
tính năng của hợp đồng thông minh bao gồm: mint, update metadata
burn NFT

Sau khi chúng ta đã triển khai xong hợp đồng thông minh trong video
trước đó.

Đầu tiên chúng ta vẫn cần thực hiện setup môi trường ảo và tạo biến môi trường
như các bài học thực hành trước đây.
Bước 1: Khởi tạo môi trường ảo
Chạy lệnh sau để tạo thư mục venv chứa môi trường riêng:
python -m venv venv


Bước 2: Kích hoạt môi trường (Activate)
Trên windows:
.\venv\Scripts\Activate.ps1


Khi thành công, bạn sẽ thấy tên môi trường (venv) 
xuất hiện phía trước dấu nhắc lệnh (prompt) trong terminal.
Bước 3. Cài đặt thư viện PyCardano
Khi đã ở trong môi trường (venv), 
việc cài đặt thư viện diễn ra rất nhanh chóng và an toàn.
Chạy lệnh:
pip install -r requirements.txt

Bước 4 : Tạo file .env và điền biến môi trường

Sau khi đã chuẩn bị xong rồi mình sẽ mô tả một chút về một số công việc
sẽ thực hiện trong phần code offchain này
Chúng ta sẽ thực hiện tạo các script để thực hiện tương tác
với các tính năng của hợp đồng thông minh bao gồm mint, update, burn

Đầu tiên chúng ta sẽ thực hiện code trước một số các hàm cần thiết
tạo file cip68_utils.py trong file này chúng ta sẽ thực hiện định nghĩa kiểu dữ liệu, các biến cần thiết và các hàm cần thiết

Bao gồm:
CIP68_REFERENCE_PREFIX
CIP68_USER_PREFIX

redeem data:MintToken, BurnToken, UpdateMetadata

datum data: CIP68Datum

load_scripts : load script
load_mint_script , load_store_script: load từng script
