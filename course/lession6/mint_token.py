"""
Lesson 6 — Mint Fungible Token (FT) with Native Script

Mục tiêu: phát hành 100 FT (ví dụ Pycardano_test_COINP_003) bằng policy khóa công khai.

Luồng chính:
1) Đọc .env, thiết lập mạng và tạo ví payment/staking.
2) Sinh hoặc tải policy keys (payment signing/verifying key dành cho policy) trong thư mục `keys/` cạnh file.
3) Tạo ScriptPubkey từ policy vkey → ScriptAll → policy_id.
4) Dựng MultiAsset và tính min-ADA cho output chứa token.
5) Dựng giao dịch: native_scripts, mint, output trả token về ví, TTL → build_and_sign → submit.
"""

import os
import sys
from os.path import exists
from blockfrost import ApiError, ApiUrls, BlockFrostApi
from dotenv import load_dotenv
from pycardano import *

# Nạp .env
load_dotenv()
network = os.getenv("BLOCKFROST_NETWORK")
wallet_mnemonic = os.getenv("MNEMONIC")
blockfrost_api_key = os.getenv("BLOCKFROST_PROJECT_ID")

# Thiết lập mạng và URL API (testnet → preview)
if network == "testnet":
    base_url = ApiUrls.preview.value
    cardano_network = Network.TESTNET
else:
    base_url = ApiUrls.mainnet.value
    cardano_network = Network.MAINNET

# Tạo khóa từ mnemonic (payment/staking)
new_wallet = crypto.bip32.HDWallet.from_mnemonic(wallet_mnemonic)
payment_key = new_wallet.derive_from_path(f"m/1852'/1815'/0'/0/0")
staking_key = new_wallet.derive_from_path(f"m/1852'/1815'/0'/2/0")
payment_skey = ExtendedSigningKey.from_hdwallet(payment_key)
staking_skey = ExtendedSigningKey.from_hdwallet(staking_key)

# Địa chỉ ví phát hành (đồng thời nhận token)
main_address = Address(
    payment_part=payment_skey.to_verification_key().hash(),
    staking_part=staking_skey.to_verification_key().hash(),
    network=cardano_network,
)

print(f"Địa chỉ ví gửi: {main_address}")


# Khởi tạo Blockfrost API để kiểm tra UTxO/số dư
api = BlockFrostApi(project_id=blockfrost_api_key, base_url=base_url)

# Lấy UTxO để ước lượng số dư tối thiểu cần thiết
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

# Ngữ cảnh chuỗi để build/submit giao dịch
cardano = BlockFrostChainContext(project_id=blockfrost_api_key, base_url=base_url)

# Tạo thư mục keys cạnh file (demo; dự án lớn nên gom về `keys/` gốc)
keys_dir = os.path.join(os.path.dirname(__file__), "keys")
if not os.path.exists(keys_dir):
    os.makedirs(keys_dir)

# Định nghĩa đường dẫn tệp khóa trong thư mục keys
policy_skey_path = os.path.join(keys_dir, "policy.skey")
policy_vkey_path = os.path.join(keys_dir, "policy.vkey")

# Tạo hoặc tải khóa chính sách (policy signing/verifying keys)
if not exists(policy_skey_path) or not exists(policy_vkey_path):
    payment_key_pair = PaymentKeyPair.generate()
    payment_signing_key = payment_key_pair.signing_key
    payment_verification_key = payment_key_pair.verification_key
    payment_signing_key.save(policy_skey_path)
    payment_verification_key.save(policy_vkey_path)
# Tại sao cần: policy signing key để ký giao dịch mint; policy verifying key để tạo script.
# Để đúc (mint) token, mạng lưới Cardano cần biết "Ai là người có quyền đúc?".
# Bạn cần một cặp khóa chuyên biệt cho việc này, gọi là Policy Keys.

# Trên cardano, mỗi token được xác định duy nhất bởi một cặp thông tin:
# 1) policy_id: định danh chính sách (chính sách xác định quyền đúc token)
# 2) asset_name: tên tài sản (có thể là chuỗi ký tự bất kỳ, mã hóa dưới dạng bytes)
# Việc kết hợp policy_id và asset_name tạo nên định danh duy nhất cho mỗi token trên mạng lưới.
# Ví dụ, bạn có thể có nhiều token với cùng tên asset_name nhưng khác policy_id,
# hoặc cùng policy_id nhưng khác asset_name. Sự kết hợp này giúp phân biệt và quản lý các token một cách hiệu quả trên Cardano.
# policy_id được tạo ra từ hash của Native Script, trong đó chứa khóa công khai của policy.

# Policy ID được xây dựng dựa trên khóa công khai (verification key) của policy
# và được mã hóa trong một script gọi là Native Script.
# Khi bạn muốn đúc thêm token, bạn phải ký giao dịch bằng khóa bí mật (signing key) tương ứng với khóa công khai đã dùng trong script.
# Nếu không có khóa bí mật này, bạn sẽ không thể đúc thêm token theo chính sách đã định.
# Điều này đảm bảo rằng chỉ những người sở hữu khóa bí mật mới có quyền đúc token theo chính sách đó,
# từ đó bảo vệ tính toàn vẹn và kiểm soát của token trên mạng lưới Cardano.
# Việc lưu trữ khóa trong thư mục `keys/` giúp bạn dễ dàng quản lý và sử dụng chúng khi cần thiết.
# Nếu bạn mất khóa này, bạn sẽ không thể đúc thêm token theo chính sách đã định.
# Do đó, việc bảo vệ và sao lưu khóa là rất quan trọng.
# Việc tạo khóa một lần và tái sử dụng chúng giúp duy trì tính liên tục trong việc quản lý token.



# Tải khóa chính sách và dựng policy script (ScriptPubkey → ScriptAll)
#1: Tải khóa từ tệp
policy_signing_key = PaymentSigningKey.load(policy_skey_path)
#2: Tạo ScriptPubkey và ScriptAll
policy_verification_key = PaymentVerificationKey.load(policy_vkey_path)
pub_key_policy = ScriptPubkey(policy_verification_key.hash())
policy = ScriptAll([pub_key_policy])
#3: Lấy policy_id
policy_id = policy.hash()
policy_id_hex = policy_id.payload.hex()
native_scripts = [policy]

# Xác định token để phát hành (tên và số lượng)
asset_name = "Pycardano_test_COINP_003"
asset_name_bytes = asset_name.encode("utf-8")
token = AssetName(asset_name_bytes)
new_asset = Asset()
multiasset = MultiAsset()
new_asset[token] = 100  # Số lượng token phát hành
multiasset[policy_id] = new_asset

# Tạo TransactionBuilder và cấu hình minting
builder = TransactionBuilder(cardano)

builder.add_input_address(main_address)  # để builder tự chọn UTxO hợp lý
# Thêm thông tin phát hành token
builder.native_scripts = native_scripts
builder.mint = multiasset

# Tính ADA tối thiểu cho đầu ra chứa token (min-ADA phụ thuộc số lượng/tên tài sản)
min_val = min_lovelace(
    cardano, output=TransactionOutput(main_address, Value(0, multiasset))
)

# Kiểm tra số dư ADA có đủ không
if total_ada < min_val + 2_000_000:  # Dự phòng 2 ADA cho phí và UTxO tối thiểu
    print(f"Không đủ ADA để phát hành token. Cần ít nhất {(min_val + 2_000_000) / 1_000_000} ADA.")
    sys.exit(1)

# Thêm đầu ra chứa token và ADA tối thiểu
builder.add_output(TransactionOutput(main_address, Value(min_val, multiasset)))

# Thiết lập TTL (demo): last_block_slot + 1000
builder.ttl = cardano.last_block_slot + 1000

# Build/sign: ký bởi ví và policy signing key; đổi (change) về main_address
builder.auxiliary_data = None  # Tùy chọn: Đặt None nếu không có metadata
try:
    signed_tx = builder.build_and_sign(
        [payment_skey, policy_signing_key], change_address=main_address
    )
except Exception as e:
    print(f"Lỗi khi xây dựng giao dịch: {e}")
    sys.exit(1)

# In chi tiết giao dịch
print(f"Số đầu vào: \t {len(signed_tx.transaction_body.inputs)}")
print(f"Số đầu ra: \t {len(signed_tx.transaction_body.outputs)}")
print(f"Phí: \t\t {signed_tx.transaction_body.fee / 1_000_000} ADA")
print(f"ADA trong đầu ra: \t {min_val / 1_000_000} ADA (tối thiểu cho token)")
print(f"Token phát hành: \t 100 {asset_name} đến {main_address}")

# Gửi giao dịch
try:
    tx_id = cardano.submit_tx(signed_tx.to_cbor())
    print(f"Giao dịch phát hành token đã gửi! ID: {tx_id}")
except Exception as e:
    if "BadInputsUTxO" in str(e):
        print("Đang cố chi tiêu một đầu vào không tồn tại (hoặc đã bị sử dụng).")
    elif "ValueNotConservedUTxO" in str(e):
        print("Giao dịch không được cân bằng. Đầu vào và đầu ra (+phí) không khớp.")
    elif "InputUTxODepletedException" in str(e):
        print("Không đủ ADA trong UTxO để chi trả đầu ra và phí giao dịch.")
    else:
        print(f"Lỗi: {e}")