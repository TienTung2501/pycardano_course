# Lesson 6 — Mint Fungible Token (FT)

Mục tiêu: phát hành một FT (token có số lượng) bằng Native Script Policy (khóa công khai).

File chính: `mint_token.py`

## Luồng xử lý trong mã
- Đọc `.env` (`BLOCKFROST_PROJECT_ID`, `MNEMONIC`, `BLOCKFROST_NETWORK`). Map `testnet` → Blockfrost preview.
- Tạo ví (payment/staking) từ mnemonic, dựng địa chỉ chính.
- Tạo/thử tải policy keys (khoá ký chính sách) tại `course/lession6/keys/policy.(skey|vkey)`.
- Tạo `ScriptPubkey` từ policy vkey → `ScriptAll([pub_key_policy])` → `policy_id`.
- Chỉ định tên token (`Pycardano_test_COINP_003`) và số lượng (100), dựng `AssetName`, `Asset`, `MultiAsset`.
- `TransactionBuilder`:
  - `add_input_address(main_address)` để chọn UTxO phù hợp.
  - `builder.native_scripts = [policy]` và `builder.mint = multiasset`.
  - Tính min-ADA cho output chứa token bằng `min_lovelace(context, TransactionOutput(...))`.
  - Thêm một output gửi token về địa chỉ chính với min ADA.
  - TTL đặt `last_block_slot + 1000`.
  - `build_and_sign([payment_skey, policy_signing_key], change_address=main_address)` và gửi tx.

## Chạy thử
- Bảo đảm ví có đủ tADA để min-ADA + phí (~ vài ADA dự phòng).
- Chạy file trong môi trường Python của dự án.

## Lưu ý
- Policy keys trong thư mục `keys` là để demo; trong dự án lớn nên gom về `keys/` gốc để dùng chung (phục vụ burn sau này).
- Với nhiều tài sản, min-ADA có thể tăng.
