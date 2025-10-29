# Lesson 1 (Chapter 3) — Hello World (Aiken + Python Off-chain)

Mục tiêu: xây dựng hợp đồng Hello World với Aiken và tương tác lock/spend bằng Python (PyCardano + Blockfrost).

Thư mục liên quan:
- `hello_world/` — dự án Aiken (blueprint `plutus.json`), có README gốc cho bản Lucid/TS.
- Python scripts: `hello_world/lock.py`, `hello_world/spend.py`.

## luồng lock.py
- Đọc `.env` (project ID, mnemonic, network) và tạo địa chỉ ví.
- Đọc `plutus.json`, lấy `compiledCode` và `hash` (dựng `PlutusV3Script`, `ScriptHash`).
- Tạo địa chỉ script bằng `Address(payment_part=script_hash, ...)`.
- Định nghĩa `HelloWorldDatum(owner: bytes)` lấy từ `verification key hash` của ví làm owner.
- Xây dựng giao dịch:
  - `TransactionBuilder(context)` với `add_input_address(main_address)`.
  - Thêm output đến script address, kèm 2 ADA và datum vừa tạo.
  - TTL = `last_block_slot + 1000`.
  - `build_and_sign([payment_skey], change_address=main_address)` rồi `submit_tx`.

## luồng spend.py
- Tương tự phần đầu như lock.py: tạo ví, đọc `plutus.json`, địa chỉ script.
- Định nghĩa `HelloWorldRedeemer(msg: bytes)` và tạo `Redeemer(data=...)` (Constr 0).
- Tìm UTxO đã lock (theo tx id từ lệnh trước, ví dụ đặt trong biến `lock_tx_id`).
- Xây dựng giao dịch:
  - `add_script_input(utxo, from_script, redeemer=...)` để tiêu UTxO script.
  - `add_input_address(main_address)` để bù phí.
  - Trả ADA về `main_address` (output thường).
  - `required_signers = [owner_hash]` và `build_and_sign([payment_skey], change_address=main_address)`.
  - `submit_tx`.

## chạy thử
- Build Aiken trước trong `hello_world/`: `aiken build` → sinh `plutus.json`.
- Đặt `.env` (`BLOCKFROST_PROJECT_ID`, `MNEMONIC`, `BLOCKFROST_NETWORK=testnet`).
- Chạy `lock.py` để lock 2 ADA vào contract.
- Lấy tx id và chỉnh `lock_tx_id` trong `spend.py`, chạy `spend.py` để unlock.

## lưu ý
- Bản README gốc trong `hello_world/README.md` nói về Lucid/TS; phần này là bản chạy với Python.
- Khi tiêu script input cần đúng `Redeemer` như logic trên-chain; ví dụ ở đây chấp nhận Constr 0 với bất kỳ bytes.
