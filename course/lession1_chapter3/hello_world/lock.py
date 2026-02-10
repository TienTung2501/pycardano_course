"""
Lesson 1 (Chapter 3) — Hello World (Lock)

Mục tiêu: Lock 2 ADA vào địa chỉ hợp đồng Plutus kèm datum chứa owner (hash của
payment verification key), dùng Blockfrost + PyCardano.

Các bước chính trong file:
1) Đọc .env, thiết lập mạng (testnet → preview) và tạo ví từ mnemonic.
2) Đọc blueprint `plutus.json` của Aiken, dựng PlutusV3Script và ScriptHash.
3) Tạo địa chỉ script từ ScriptHash (không có staking part).
4) Định nghĩa datum HelloWorldDatum(owner: bytes) và khởi tạo từ vkey hash.
5) Xây giao dịch: thêm input từ ví, output 2 ADA đến địa chỉ script kèm datum.
6) TTL, build_and_sign và submit_tx.
"""

from dataclasses import dataclass
import os
import sys
import json
from blockfrost import ApiError, ApiUrls, BlockFrostApi
from dotenv import load_dotenv
from pycardano import *
from pycardano.hash import VerificationKeyHash, ScriptHash

# Nạp biến môi trường (.env ở gốc repo)
load_dotenv()
network = os.getenv("BLOCKFROST_NETWORK")
wallet_mnemonic = os.getenv("MNEMONIC")
blockfrost_api_key = os.getenv("BLOCKFROST_PROJECT_ID")

# Thiết lập mạng và URL API
if network == "testnet":
    base_url = ApiUrls.preview.value
    cardano_network = Network.TESTNET
else:
    base_url = ApiUrls.mainnet.value
    cardano_network = Network.MAINNET

# Tạo khóa từ mnemonic (BIP32: 1852H/1815H/0H/0/0 và /2/0)
new_wallet = crypto.bip32.HDWallet.from_mnemonic(wallet_mnemonic)
payment_key = new_wallet.derive_from_path(f"m/1852'/1815'/0'/0/0")
staking_key = new_wallet.derive_from_path(f"m/1852'/1815'/0'/2/0")
payment_skey = ExtendedSigningKey.from_hdwallet(payment_key)
staking_skey = ExtendedSigningKey.from_hdwallet(staking_key)

# Tạo địa chỉ ví (payment/staking) cho tài khoản chính
main_address = Address(
    payment_part=payment_skey.to_verification_key().hash(),
    staking_part=staking_skey.to_verification_key().hash(),
    network=cardano_network,
)

print(f"Địa chỉ ví: {main_address}")

# Khởi tạo API BlockFrost để truy vấn UTxO số dư sơ bộ (không bắt buộc cho build tx)
api = BlockFrostApi(project_id=blockfrost_api_key, base_url=base_url)

# Lấy UTxO để kiểm tra số dư ví (đảm bảo có đủ ADA cho phí và 2 ADA lock)
try:
    utxos = api.address_utxos(main_address)
except Exception as e:
    if e.status_code == 404:
        print("Địa chỉ không có UTxO nào.")
        if network == "testnet":
            print("Yêu cầu tADA từ faucet: https://docs.cardano.org/cardano-testnets/tools/faucet/")
        sys.exit(1)
    else:
        print(f"Lỗi: {e.message}")
        sys.exit(1)

# Kiểm tra số dư ADA
total_ada = sum(int(utxo.amount[0].quantity) for utxo in utxos)
print(f"Tổng ADA khả dụng: {total_ada / 1_000_000} ADA")

if total_ada < 3_000_000:  # Dự phòng 3 ADA cho phí, lock, và spend sau
    print("Không đủ ADA để lock hợp đồng. Cần ít nhất 3 ADA.")
    sys.exit(1)

# Ngữ cảnh chuỗi để build/submit giao dịch
cardano = BlockFrostChainContext(project_id=blockfrost_api_key, base_url=base_url)

# Đọc validator từ plutus.json (blueprint Aiken) — dùng compiledCode và hash có sẵn
def read_validator() -> dict:
    with open("plutus.json", "r") as f:
        validator = json.load(f)
    script_bytes = PlutusV3Script(  # Sử dụng PlutusV3 như sample
        bytes.fromhex(validator["validators"][0]["compiledCode"])
    )
    script_hash = ScriptHash(bytes.fromhex(validator["validators"][0]["hash"]))
    return {
        "type": "PlutusV3",
        "script_bytes": script_bytes,
        "script_hash": script_hash,
    }

validator = read_validator()

# Script address (địa chỉ hợp đồng) — không có staking, mạng theo cardano_network
script_address = Address(
    payment_part=validator["script_hash"],
    network=cardano_network,
)

print(f"Địa chỉ hợp đồng (script): {script_address}")

# Định nghĩa Datum class (PlutusData) để đóng gói
# dữ liệu thành định dạng CBOR khớp với on-chain type
@dataclass
class HelloWorldDatum(PlutusData):# Datum kế thừa PlutusData
    CONSTR_ID = 0 
    owner: bytes  # VerificationKeyHash.to_primitive() trả về bytes

# === Giải thích CONSTR_ID ===
# Ý nghĩa: Trong Plutus Core, các kiểu dữ liệu thường được định nghĩa dưới dạng Sum Types 
# (ví dụ: data MyDatum = ActionA | ActionB). 
# Mỗi lựa chọn (ActionA, ActionB) được gán một chỉ số (index), bắt đầu từ 0.
# CONSTR_ID = 0 nghĩa là HelloWorldDatum tương ứng 
# với lựa chọn đầu tiên trong kiểu dữ liệu trên chuỗi.
# Ví dụ, nếu kiểu dữ liệu trên chuỗi định nghĩa: data HelloWorldDatum = MkHelloWorldDatum ByteString 
# thì CONSTR_ID = 0 biểu thị rằng đây là lựa chọn duy nhất và đầu tiên.
# Ví dụ có 2 lựa chọn, CONSTR_ID = 0 sẽ là lựa chọn đầu tiên, CONSTR_ID = 1 sẽ là lựa chọn thứ hai.
# Ví dụ datum trên chuỗi:
# data HelloWorldDatum = MkHelloWorldDatum ByteString | AnotherDatumConstructor Integer
# thì CONSTR_ID = 0 tương ứng với MkHelloWorldDatum, CONSTR_ID = 1 tương ứng với AnotherDatumConstructor.

# === Ví dụ thực tế về Datum với nhiều CONSTR_ID ===
# Ví dụ thực tế datum có 2 lựa chọn:
# -- On-chain code example (Aiken) --
# data EscrowState = 
#       OnSale                        -- Index 0: Chỉ chứa giá tiền, người bán
#         { seller :: PubKeyHash
#         , price  :: Integer 
#         }
#     | FundsLocked                   -- Index 1: Chứa thêm thông tin người mua
#         { seller :: PubKeyHash
#         , buyer  :: PubKeyHash      -- Thêm trường này
#         , price  :: Integer
#         }

# === Định nghĩa hai trạng thái datum với CONSTR_ID khác nhau ===
# # --- Trạng thái 1: Đang rao bán (CONSTR_ID = 0) ---
# @dataclass
# class OnSaleDatum(PlutusData):
#     CONSTR_ID = 0
#     seller: bytes
#     price: int

# # --- Trạng thái 2: Đã có người mua, khóa tiền (CONSTR_ID = 1) ---
# @dataclass
# class FundsLockedDatum(PlutusData):
#     CONSTR_ID = 1
#     seller: bytes
#     buyer: bytes  # Lúc này mới xuất hiện người mua
#     price: int
# Tạo datum (owner = hash của payment verification key của ví)
# Tuy nhiên, với các ứng dụng phức tạp hơn (Game, DeFi, DAO), 
# Datum đóng vai trò là một "Máy trạng thái" (State Machine). 
# Datum sẽ thay đổi hình dạng tùy theo giai đoạn của hợp đồng.

# Trên đây là một ví dụ thực tế về Hợp đồng Trung gian mua bán (Escrow).

# Bài toán: Mua bán an toàn
# Giai đoạn 1: Alice (Người bán) treo món hàng lên contract. 
# Trạng thái là "Đang rao bán".

# Giai đoạn 2: Bob (Người mua) gửi tiền vào contract. 
# Trạng thái chuyển thành "Đã khóa tiền" (chờ Alice giao hàng).

# Lúc này, Datum buộc phải có nhiều CONSTR_ID để phân biệt 2 trạng thái này.
# === Hoặc dễ gặp và phổ biến nhất đó là khi bạn viết redeemer có nhiều lựa chọn khác nhau. ===
# Ví dụ redeemer có 2 lựa chọn: "Mint" và "Burn". 
# đây là một ví dụ phổ biến trong NFT minting policy.
# Bạn sẽ định nghĩa 2 redeemer class với CONSTR_ID = 0 (Mint) và CONSTR_ID = 1 (Burn).
# === Kết thúc ví dụ thực tế ===

owner_vkey = payment_skey.to_verification_key()
owner_hash = owner_vkey.hash()  # Sử dụng VerificationKeyHash như sample
datum = HelloWorldDatum(owner=owner_hash.to_primitive())  # to_primitive() -> bytes

# Tạo TransactionBuilder cho lock: tiêu UTxO từ ví và gửi 2 ADA đến script
lock_builder = TransactionBuilder(context=cardano)
lock_builder.add_input_address(main_address)

# Thêm output: Gửi 2 ADA đến script address với datum inline
amount_to_lock = 2_000_000  # 2 ADA
lock_builder.add_output(
    TransactionOutput(
        address=script_address,
        amount=Value(amount_to_lock),
        datum=datum,  # Sử dụng PlutusData instance trực tiếp
    )
)

# Thiết lập TTL ngắn (demo)
lock_builder.ttl = cardano.last_block_slot + 1000

# Build và ký giao dịch, đổi (change) về main_address
lock_signed_tx = lock_builder.build_and_sign(
    signing_keys=[payment_skey],
    change_address=main_address,
)

# In chi tiết
print(f"Số đầu vào lock: {len(lock_signed_tx.transaction_body.inputs)}")
print(f"Số đầu ra lock: {len(lock_signed_tx.transaction_body.outputs)}")
print(f"Phí lock: {lock_signed_tx.transaction_body.fee / 1_000_000} ADA")

# Gửi giao dịch lock
try:
    lock_tx_id = cardano.submit_tx(lock_signed_tx.to_cbor())
    print(f"Giao dịch lock thành công! ID: {lock_tx_id}")
    print(f"2 tADA locked into the contract\n\tTx ID: {lock_tx_id}\n\tDatum: {datum.to_cbor_hex()}")
except Exception as e:
    print(f"Lỗi gửi lock: {e}")
    sys.exit(1)