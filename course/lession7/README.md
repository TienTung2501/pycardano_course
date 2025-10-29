# Lesson 7 — Mint Multiple NFTs (CIP-721 metadata) & Burn

Mục tiêu: đúc nhiều NFT cùng lúc với metadata 721 và có script burn tương ứng.

File chính: `mint_nfts.py`, `burn_nfts.py`

## Mint nhiều NFT (`mint_nfts.py`)
- Đọc `.env` và derive ví từ mnemonic.
- Chuẩn bị danh sách `assets` (name + các thuộc tính ngẫu nhiên như type, attack, ...).
- Tạo/tải policy keys tại `course/lession7/keys/` (nếu không tồn tại sẽ sinh mới).
- Dựng `ScriptPubkey` → `ScriptAll` → `policy_id`.
- Tạo cấu trúc metadata CIP-721: `{ 721: { policy_id_hex: { asset_name: { ...fields } } } }` và gán vào `AuxiliaryData(AlonzoMetadata(...))`.
- Dựng `Asset` tổng hợp nhiều `AssetName`, set mỗi NFT = 1.
- `builder.native_scripts = [policy]`, `builder.mint = my_nft`.
- Tính min-ADA cho output chứa tất cả NFT → thêm output về địa chỉ chính.
- `add_input_address(main_address)` và `build_and_sign([payment_skey, policy_signing_key], change_address=main_address)` → submit.

## Burn NFTs (`burn_nfts.py`)
- Nguyên tắc burn: cùng policy, lượng âm trong `Asset` tương ứng với token-name cần burn.
- Yêu cầu có policy signing key khớp với khi mint.
- Ký giao dịch bởi ví và policy-signing-key.

## Lưu ý
- Nếu muốn mint kèm IPFS, có thể push metadata/asset lên IPFS và đặt link trong metadata CIP-721.
- Min-ADA tăng theo số lượng tài sản trong 1 output; có thể chọn chia nhiều output để tối ưu.
