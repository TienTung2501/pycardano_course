# Lesson 5 — Consolidate UTxOs

Mục tiêu: gộp (consolidate) tất cả UTxO của một địa chỉ về một UTxO duy nhất để dễ quản lý, giảm phí về sau.

File chính: `consolidate.py`

## Luồng xử lý trong mã
- Đọc `.env` để lấy `BLOCKFROST_PROJECT_ID`, `MNEMONIC`, `BLOCKFROST_NETWORK`.
- Lập địa chỉ ví từ mnemonic theo path `1852H/1815H/0H/0/0` (payment) và `.../2/0` (staking).
- Gọi Blockfrost API `address_utxos` để lấy toàn bộ UTxO của địa chỉ.
- Khởi tạo `BlockFrostChainContext` và `TransactionBuilder`.
- Thay vì `add_input_address`, script duyệt mọi UTxO, tự chuyển thành `UTxO` và `add_input(utxo)` — đảm bảo "ăn" hết toàn bộ UTxO.
- Không thêm output cố định; để `build_and_sign([...], change_address=main_address)` tự cân bằng (phí + output đổi). Kết quả là một UTxO đổi duy nhất chứa toàn bộ giá trị còn lại (sau khi trừ phí).
- Gửi giao dịch và in thông tin đầu vào/đầu ra/fee.

## Chạy thử (yêu cầu ví có tADA)
- Cập nhật `.env` ở gốc repo: `BLOCKFROST_PROJECT_ID`, `MNEMONIC`, `BLOCKFROST_NETWORK=testnet`.
- Chạy script bằng Python trong venv hiện tại.

## Lưu ý & lỗi thường gặp
- Nếu `BadInputsUTxO`: một số UTxO vừa bị tiêu bởi tx khác; thử lại.
- Nếu `ValueNotConservedUTxO`: giao dịch không cân bằng; đảm bảo không push output thủ công sai.
- Tài khoản cần đủ ADA để trả phí sau khi "gom".
