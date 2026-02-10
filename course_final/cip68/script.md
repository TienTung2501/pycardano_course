Xin chào mọi người! Chào mừng mọi người đã đến với video
tiếp theo trong khóa học lập trình Pycardano của chúng tôi.
Trong video này, chúng ta sẽ bắt đầu triển khai ví dụ cip 68
trong khóa học này của chúng ta trong phần hướng dẫn này mình
sẽ thực hiện hướng dẫn các bạn chi tiết các nội dung sau mình
đã giới thiệu khá chi tiết trong phần trình bày slide:
1. Thực hiện code và triển khai hợp đồng thông minh
2. Thưc hiện code offchain code để tương tác với các
tính năng của hợp đồng thông minh bao gồm: mint, update mêtadata
burn NFT
3. Triển khai một full dapp bao gồm frontend backend thực hiện
các tính năng mint, update metadata, burn NFT trực tiếp ngay
trên giao diện.
Và trong video này mình sẽ đi sâu và phần code hợp đồng thông minh
và triển khai nó trên testnet preprod
Bước đầu tiên:
Chúng ta sẽ thực hiện tại source code để code hợp đồng thông minh bằng Aiken
Để tạo source code thì điều kiện chúng ta phải thiết lập aiken cho máy tính
như trong bài giảng trước đó mình đã hướng dẫn khá chi tiết rồi nên trong phần 
này mình sẽ không lặp lại bước setup mà đi vào tạo dự án và code luôn
đầu tiên là tạo source code:
Dùng câu lệnh
aiken new cip68
cd cip68
aiken build

Tiếp đến chúng ta sẽ tạo file cip68.ak trong thư mục validator nơi chứa
các validator của dự án.
Chúng ta bắt đầu đi vào code

Sau khi code xong chúng ta sẽ thực hiện câu lệnh aiken check để kiểm tra xem
code của chúng ta đã chạy được và có biên dịch được không.

Mọi người chú ý tại thời điểm mình xây dựng khóa học mình sử dụng
thư phiên bản 
python 3.12
thư viện aiken :v1.1.19  và biên dịch ra plutus v3

Với file cấu hình aiken dưới đây:
name = "pycardano_course/cip68_dynamic_asset"(Chú ý phần này phụ thuộc vào vị trí source code trong máy của các bạn)
version = "0.0.1"
compiler = "v1.1.19"
plutus = "v3"
license = "MIT"
description = "CIP-68 Dynamic Asset Smart Contract for PyCardano Course"

[repository]
user = "pycardano_course"
project = "cip68_dynamic_asset"
platform = "github"

[[dependencies]]
name = "aiken-lang/stdlib"
version = "v2.2.0"
source = "github"

Sau khi đã triển khai thành công trên mạng cardano chúng sẽ có file plutus.json trong thư mục dự án
Đây là file mà chúng ta sẽ thực hiện sử dụng sau này trong quá trình phát triển.
