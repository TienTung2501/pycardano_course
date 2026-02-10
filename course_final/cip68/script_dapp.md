Xin chào mọi người! Chào mừng mọi người đã đến với video
tiếp theo trong khóa học lập trình Pycardano của chúng tôi.
Trong video này, chúng ta sẽ tiếp tục triển khai ví dụ cip 68
của chúng ta và trong nội lần hướng dẫn này mình sẽ tiếp tục
hướng dẫn Thưc hiện code offchain code để tương tác với các
tính năng của hợp đồng thông minh bao gồm: mint, update mêtadata
burn NFT
3. Triển khai một full dapp bao gồm frontend backend thực hiện
các tính năng mint, update, metadata, burn NFT trực tiếp ngay
trên giao diện.
Và trong video này mình sẽ đi sâu và phần code full dapp để thực
demo tương tác trực tiếp trên giao diện

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

Oke bắt đầu chúng ta sẽ thực hiện đi xây backend trước
Xây backend thì sẽ phải đáp ứng được các yêu cầu tư frontend
bao gồm conver address -> bech32, get script info, query thông tin ví, , list NFT, thực hiện mint, update, burn, submit, get metadata, list token





