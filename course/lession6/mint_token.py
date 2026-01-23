"""
Xin chào mọi người, chào mừng đến với bài học thứ 6 
trong chuỗi hướng dẫn Pycardano của tôi!
Thì trong bài học này, chúng ta sẽ tìm hiểu cách
========================================================
Lesson 6 — Mint Fungible Token (FT) with Native Script
========================================================

Mục tiêu bài học:
- Hiểu cơ chế mint token trên Cardano
- Phát hành 100 Fungible Token (FT)
- Sử dụng Native Script (policy dựa trên khóa công khai)
- Thực hành bằng thư viện Pycardano

Cách thực hiện:
Mình sẽ huong dẫn chi tiết từng bước trong code bên dưới.
Kèm theo giải thích về lý thuyết liên quan.
"""

# ======================================================
# 1. IMPORT THƯ VIỆN CẦN THIẾT
# ======================================================

import os
import sys
from os.path import exists

# Blockfrost: dùng để query blockchain (UTxO, submit tx, v.v.)
from blockfrost import ApiError, ApiUrls, BlockFrostApi

# dotenv: đọc biến môi trường từ file .env
from dotenv import load_dotenv

# Pycardano: thư viện chính để build transaction Cardano
from pycardano import *


# ======================================================
# 2. NẠP BIẾN MÔI TRƯỜNG (.env)
# ======================================================
# .env cần có:
# - BLOCKFROST_NETWORK=testnet | mainnet
# - BLOCKFROST_PROJECT_ID=...
# - MNEMONIC="word1 word2 ..."

load_dotenv()

network = os.getenv("BLOCKFROST_NETWORK")
wallet_mnemonic = os.getenv("MNEMONIC")
blockfrost_api_key = os.getenv("BLOCKFROST_PROJECT_ID")


# ======================================================
# 3. CẤU HÌNH MẠNG CARDANO (TESTNET / MAINNET)
# ======================================================

if network == "testnet":
    # Preview testnet (dùng để học)
    base_url = ApiUrls.preview.value
    cardano_network = Network.TESTNET
else:
    base_url = ApiUrls.mainnet.value
    cardano_network = Network.MAINNET


# ======================================================
# 4. TẠO KHÓA VÍ TỪ MNEMONIC (BIP-39 + CIP-1852)
# ======================================================
# Lưu ý:
# - Đây là ví "người dùng"
# - Dùng để:
#   + trả phí giao dịch
#   + nhận token sau khi mint

new_wallet = crypto.bip32.HDWallet.from_mnemonic(wallet_mnemonic)

# Payment key: dùng để gửi/nhận ADA & token
payment_key = new_wallet.derive_from_path("m/1852'/1815'/0'/0/0")

# Staking key: dùng cho staking (không dùng trong mint)
staking_key = new_wallet.derive_from_path("m/1852'/1815'/0'/2/0")

payment_skey = ExtendedSigningKey.from_hdwallet(payment_key)
staking_skey = ExtendedSigningKey.from_hdwallet(staking_key)


# ======================================================
# 5. TẠO ĐỊA CHỈ CARDANO (PAYMENT + STAKE)
# ======================================================

main_address = Address(
    payment_part=payment_skey.to_verification_key().hash(),
    staking_part=staking_skey.to_verification_key().hash(),
    network=cardano_network,
)

print(f"Địa chỉ ví phát hành & nhận token: {main_address}")


# ======================================================
# 6. KẾT NỐI BLOCKFROST – KIỂM TRA UTxO & SỐ DƯ
# ======================================================

api = BlockFrostApi(
    project_id=blockfrost_api_key,
    base_url=base_url
)

# Lấy toàn bộ UTxO của địa chỉ
try:
    utxos = api.address_utxos(main_address)
except Exception as e:
    if e.status_code == 404:
        print("Ví chưa có UTxO nào.")
        if network == "testnet":
            print("Lấy tADA tại faucet:")
            print("https://docs.cardano.org/cardano-testnets/tools/faucet/")
        sys.exit(1)
    else:
        print(f"Lỗi Blockfrost: {e}")
        sys.exit(1)

# Tính tổng ADA
total_ada = sum(int(utxo.amount[0].quantity) for utxo in utxos)
print(f"Tổng ADA khả dụng: {total_ada / 1_000_000} ADA")


# ======================================================
# 7. CHAIN CONTEXT (DÙNG ĐỂ BUILD TX)
# ======================================================

cardano = BlockFrostChainContext(
    project_id=blockfrost_api_key,
    base_url=base_url
)


# ======================================================
# 8. GIẢI THÍCH CƠ CHẾ MINT TOKEN TRÊN CARDANO (LÝ THUYẾT)
# ======================================================

# ------------------------------------------------------
# BƯỚC 1 — VẤN ĐỀ CỐT LÕI
# ------------------------------------------------------
# Khi phát hành một token, blockchain cần trả lời câu hỏi:
# "Ai có quyền mint (đúc) hoặc burn (hủy) token này?"

# Cardano giải quyết vấn đề này bằng khái niệm:
# -> Minting Policy (chính sách phát hành token)


# ------------------------------------------------------
# BƯỚC 2 — CÁC CƠ CHẾ MINT TOKEN TRÊN CARDANO
# ------------------------------------------------------
# Trên Cardano, có 2 cơ chế để định nghĩa Minting Policy:
#
# 1. Native Script
#    - Quy tắc đơn giản
#    - Không cần smart contract (Plutus)
#
# 2. Plutus Script
#    - Hợp đồng thông minh
#    - Logic phức tạp hơn (DeFi, NFT động, v.v.)


# ------------------------------------------------------
# BƯỚC 3 — VÌ SAO BÀI NÀY DÙNG NATIVE SCRIPT
# ------------------------------------------------------
# Trong bài học này, chúng ta sử dụng Native Script vì:
# - Dễ hiểu
# - Phổ biến trong thực tế
# - Đủ dùng cho việc phát hành token cơ bản (FT / NFT)
#
# Với Native Script, quyền mint token thường được xác định
# dựa trên chữ ký của một khóa công khai (public key).


# ------------------------------------------------------
# BƯỚC 4 — NATIVE SCRIPT HOẠT ĐỘNG NHƯ THẾ NÀO?
# ------------------------------------------------------
# Native Script không chứa code chạy phức tạp.
# Nó chỉ là một tập các điều kiện cần thỏa mãn.
#
# Ví dụ trong bài này:
# - Giao dịch mint token PHẢI có chữ ký
# - Chữ ký đó phải tương ứng với một khóa công khai cụ thể
#
# Nếu điều kiện này đúng -> giao dịch hợp lệ -> token được mint.


# ------------------------------------------------------
# BƯỚC 5 — KHÓA CÔNG KHAI ĐẾN TỪ ĐÂU?
# ------------------------------------------------------
# Để có khóa công khai (public key) đưa vào Native Script,
# chúng ta cần tạo ra một cặp khóa riêng, gọi là:
#
# -> Policy Key Pair
#
# Policy Key Pair gồm:
# - Policy Signing Key  (khóa bí mật): dùng để ký giao dịch mint
# - Policy Verifying Key (khóa công khai): dùng để tạo Native Script


# ------------------------------------------------------
# BƯỚC 6 — CÁC CÁCH TẠO POLICY KEY
# ------------------------------------------------------
# Có nhiều cách để tạo policy key, phổ biến nhất là:
#
# 1. Tạo ngẫu nhiên (PaymentKeyPair.generate)
#    - Độc lập với ví người dùng
#    - Phổ biến nhất trong quản lý token
#
# 2. Sinh từ mnemonic của ví
#    - Có thể làm, nhưng ít dùng
#
# 3. Multisig / DAO key
#    - Dùng khi cần quản trị phi tập trung


# ------------------------------------------------------
# BƯỚC 7 — POLICY ID LÀ GÌ?
# ------------------------------------------------------
# Policy ID = hash của Native Script
#
# Native Script chứa:
# - Khóa công khai (verifying key)
# - Các điều kiện mint
#
# Vì vậy:
# - Policy ID đại diện cho "luật phát hành" của token
# - Mọi token trên Cardano đều được định danh bởi:
#   (policy_id, asset_name)


# ------------------------------------------------------
# BƯỚC 8 — KẾT LUẬN: VÌ SAO CHÚNG TA CẦN POLICY KEY?
# ------------------------------------------------------
# Chúng ta cần policy key vì:
#
# - Blockchain cần biết "ai có quyền mint token"
# - Native Script cần một khóa công khai để xác thực chữ ký
# - Policy key cho phép kiểm soát nguồn cung token
#
# Policy key đóng vai trò như:
# -> "Quyền phát hành tiền" của token trên Cardano
#
# Ai giữ policy signing key:
# -> người đó có quyền mint / burn token theo chính sách đã định
#
# Vì vậy, policy key cần được:
# - Tạo cẩn thận
# - Lưu trữ an toàn
# - Có thể tái sử dụng cho các lần mint trong tương lai

# ======================================================
# 9. TẠO / TẢI POLICY KEY (QUYỀN MINT TOKEN)
# ======================================================
# Đây KHÔNG phải payment key của ví
# Đây là "policy key" – khóa kiểm soát quyền mint

keys_dir = os.path.join(os.path.dirname(__file__), "keys")
os.makedirs(keys_dir, exist_ok=True)

policy_skey_path = os.path.join(keys_dir, "policy.skey")
policy_vkey_path = os.path.join(keys_dir, "policy.vkey")

# Nếu chưa có thì tạo mới
if not exists(policy_skey_path) or not exists(policy_vkey_path):
    policy_keypair = PaymentKeyPair.generate()
    policy_keypair.signing_key.save(policy_skey_path)
    policy_keypair.verification_key.save(policy_vkey_path)

# Nạp policy key
policy_signing_key = PaymentSigningKey.load(policy_skey_path)
policy_verification_key = PaymentVerificationKey.load(policy_vkey_path)


# ======================================================
# 10. TẠO NATIVE SCRIPT & POLICY ID
# ======================================================
# Native Script yêu cầu:
# - Giao dịch phải có chữ ký của policy key

pub_key_policy = ScriptPubkey(
    policy_verification_key.hash()
)

policy = ScriptAll([pub_key_policy])

# Policy ID = hash của script
policy_id = policy.hash()
policy_id_hex = policy_id.payload.hex()

native_scripts = [policy]


# ======================================================
# 11. ĐỊNH NGHĨA TOKEN CẦN MINT
# ======================================================

# Trên Cardano, một token KHÔNG tồn tại độc lập.
# Mỗi token luôn được định danh duy nhất bởi cặp:
#
#   (Policy ID, Asset Name)
#
# Trong đó:
# - Policy ID: xác định "luật phát hành" (minting policy)
# - Asset Name: tên token dưới policy đó
#
# --------------------------------------------
# BƯỚC 1 — Định nghĩa Asset Name (tên token)
# --------------------------------------------
# Asset Name là bytes, không phải string thuần

asset_name = "Pycardano_test_COINP_003"
token = AssetName(asset_name.encode("utf-8"))

# --------------------------------------------
# BƯỚC 2 — Tạo Asset
# --------------------------------------------
# Asset={
#     "Asset_name": 100
#       ....
#     "Asset_name": 1,
#     "Asset_name": 1,
# }
#
# quantity > 0  -> mint
# quantity < 0  -> burn


asset = Asset()
asset[token] = 100   # Mint 100 fungible tokens
# asset = {
#     "Pycardano_test_COINP_003": 100
#       ....
#     "NFT_001": 1,
#     "NFT_002": 1,
# }


# --------------------------------------------
# BƯỚC 3 — Tạo MultiAsset
# --------------------------------------------
# Một transaction Cardano có thể xử lý:
# - nhiều token
# - nhiều asset name
# - nhiều policy ID
# MultiAsset = {
#   policy_id_1: Asset,
#   policy_id_2: Asset
# }

# Vì vậy, mint token luôn dùng MultiAsset:


multiasset = MultiAsset()
multiasset[policy_id] = asset

# kết quả:
# multiasset = {
#     "abcd1234...": {-->policy_id
#         "Pycardano_test_COINP_003": 100,
#           ....
#         "NFT_001": 1,
#         "NFT_002": 1,
#     }
#     "efgh5678...": {-->policy_id
#         "AnotherToken": 500,
#     }
# }


# ======================================================
# 12. BUILD TRANSACTION MINT TOKEN
# ======================================================

builder = TransactionBuilder(cardano)

# Cho builder tự chọn UTxO từ ví
builder.add_input_address(main_address)

# Gắn script & mint data
builder.native_scripts = native_scripts
builder.mint = multiasset


# ======================================================
# 13. TÍNH MIN-ADA CHO UTxO CHỨA TOKEN
# ======================================================
# Cardano yêu cầu mỗi UTxO chứa token phải có ADA tối thiểu

min_val = min_lovelace(
    cardano,
    output=TransactionOutput(
        main_address,
        Value(0, multiasset)
    )
)

# Kiểm tra đủ ADA không
if total_ada < min_val + 2_000_000:
    print("Không đủ ADA để mint token.")
    sys.exit(1)

# Thêm output nhận token
builder.add_output(
    TransactionOutput(
        main_address,
        Value(min_val, multiasset)
    )
)


# ======================================================
# 14. TTL (HẠN GIAO DỊCH)
# ======================================================
builder.ttl = cardano.last_block_slot + 1000


# ======================================================
# 15. KÝ GIAO DỊCH
# ======================================================
# CẦN 2 CHỮ KÝ:
# - payment_skey: trả phí
# - policy_signing_key: quyền mint

signed_tx = builder.build_and_sign(
    [payment_skey, policy_signing_key],
    change_address=main_address
)


# ======================================================
# 16. IN THÔNG TIN GIAO DỊCH
# ======================================================

print(f"Phí giao dịch: {signed_tx.transaction_body.fee / 1_000_000} ADA")
print(f"Mint: 100 {asset_name}")
print(f"Policy ID: {policy_id_hex}")


# ======================================================
# 17. SUBMIT TRANSACTION
# ======================================================

tx_id = cardano.submit_tx(signed_tx.to_cbor())
print(f"Mint token thành công! Tx ID: {tx_id}")
