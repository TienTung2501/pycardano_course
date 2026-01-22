"""
Lesson 5 — Consolidate UTxOs

Mục tiêu: gộp tất cả UTxO của địa chỉ về một UTxO đổi duy nhất (giúp giảm số lượng
UTxO và tối ưu phí ở các lần giao dịch sau).

Mọi người có thể hiểu đơn giản như sau:
Hãy tưởng tượng ví của các bạn giống như một con heo đất.
Mỗi lần ai đó chuyển tiền cho bạn, họ nhét vào một tờ tiền.
Nếu bạn nhận 100 lần mỗi lần 1 ADA, trong heo đất sẽ có 100 tờ 1 ADA.
Khi bạn muốn mua một món đồ giá 90 ADA, bạn phải lôi 90 tờ tiền đó ra để trả.
Việc đếm 90 tờ tiền tốn thời gian và công sức.
Trong Blockchain, việc 'đếm' này tốn phí giao dịch (Fee) và dung lượng mạng.
Bài hôm nay, chúng ta sẽ học cách gom tất cả tiền lẻ đổi thành một tờ tiền mệnh giá lớn duy nhất. 
Kỹ thuật này gọi là Consolidate UTxO.

Bước 1: Khởi tạo môi trường ảo
Chạy lệnh sau để tạo thư mục venv chứa môi trường riêng:
python3 -m venv venv


Bước 2: Kích hoạt môi trường (Activate)
Đây là điểm khác biệt chính so với Windows. Trên Linux/Ubuntu, bạn dùng lệnh source:
source venv/bin/activate


Khi thành công, bạn sẽ thấy tên môi trường (venv) xuất hiện phía trước dấu nhắc lệnh (prompt) trong terminal.
Bước 3. Cài đặt thư viện PyCardano
Khi đã ở trong môi trường (venv), việc cài đặt thư viện diễn ra rất nhanh chóng và an toàn.
Chạy lệnh:
pip install pycardano blockfrost-python

"""

