import os
import sys
from os.path import exists
from blockfrost import ApiError, ApiUrls, BlockFrostApi
from dotenv import load_dotenv
from pycardano import *

# Tải biến môi trường
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

# Tạo khóa từ mnemonic
new_wallet = crypto.bip32.HDWallet.from_mnemonic(wallet_mnemonic)
payment_key = new_wallet.derive_from_path(f"m/1852'/1815'/0'/0/0")
staking_key = new_wallet.derive_from_path(f"m/1852'/1815'/0'/2/0")
payment_skey = ExtendedSigningKey.from_hdwallet(payment_key)
staking_skey = ExtendedSigningKey.from_hdwallet(staking_key)

# Tạo địa chỉ chính (ví gửi)
main_address = Address(
    payment_part=payment_skey.to_verification_key().hash(),
    staking_part=staking_skey.to_verification_key().hash(),
    network=cardano_network,
)

print(f"Địa chỉ ví gửi: {main_address}")


# Khởi tạo API BlockFrost
api = BlockFrostApi(project_id=blockfrost_api_key, base_url=base_url)

# Lấy UTxO
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

# Khởi tạo ngữ cảnh chuỗi BlockFrost
cardano = BlockFrostChainContext(project_id=blockfrost_api_key, base_url=base_url)

# Tạo thư mục keys ở cùng cấp với tệp Python
keys_dir = os.path.join(os.path.dirname(__file__), "keys")
if not os.path.exists(keys_dir):
    os.makedirs(keys_dir)

# Định nghĩa đường dẫn tệp khóa trong thư mục keys
policy_skey_path = os.path.join(keys_dir, "policy.skey")
policy_vkey_path = os.path.join(keys_dir, "policy.vkey")

# Tạo hoặc tải khóa chính sách (policy keys)
if not exists(policy_skey_path) or not exists(policy_vkey_path):
    payment_key_pair = PaymentKeyPair.generate()
    payment_signing_key = payment_key_pair.signing_key
    payment_verification_key = payment_key_pair.verification_key
    payment_signing_key.save(policy_skey_path)
    payment_verification_key.save(policy_vkey_path)

# Tải khóa chính sách
policy_signing_key = PaymentSigningKey.load(policy_skey_path)
policy_verification_key = PaymentVerificationKey.load(policy_vkey_path)
pub_key_policy = ScriptPubkey(policy_verification_key.hash())
policy = ScriptAll([pub_key_policy])
policy_id = policy.hash()
policy_id_hex = policy_id.payload.hex()
native_scripts = [policy]

# Xác định token để phát hành
asset_name = "Pycardano_test_COINP_003"
asset_name_bytes = asset_name.encode("utf-8")
token = AssetName(asset_name_bytes)
new_asset = Asset()
multiasset = MultiAsset()
new_asset[token] = 100  # Số lượng token phát hành
multiasset[policy_id] = new_asset

# Tạo TransactionBuilder
builder = TransactionBuilder(cardano)

# # Thêm tất cả UTxO làm đầu vào thủ công
# for utxo in utxos:
#     tx_input = TransactionInput.from_primitive([utxo.tx_hash, utxo.tx_index])
#     value = Value.from_primitive(
#         [int(utxo.amount[0].quantity)] + [
#             (asset.unit, int(asset.quantity)) for asset in utxo.amount[1:] if asset.unit != "lovelace"
#         ]
#     )
#     tx_output = TransactionOutput(main_address, value)
#     utxo_obj = UTxO(tx_input, tx_output)
#     builder.add_input(utxo_obj)

builder.add_input_address(main_address)
# Thêm thông tin phát hành token
builder.native_scripts = native_scripts
builder.mint = multiasset

# Tính ADA tối thiểu cho đầu ra chứa token
min_val = min_lovelace(
    cardano, output=TransactionOutput(main_address, Value(0, multiasset))
)

# Kiểm tra số dư ADA có đủ không
if total_ada < min_val + 2_000_000:  # Dự phòng 2 ADA cho phí và UTxO tối thiểu
    print(f"Không đủ ADA để phát hành token. Cần ít nhất {(min_val + 2_000_000) / 1_000_000} ADA.")
    sys.exit(1)

# Thêm đầu ra chứa token và ADA tối thiểu
builder.add_output(TransactionOutput(main_address, Value(min_val, multiasset)))

# Thiết lập TTL
builder.ttl = cardano.last_block_slot + 1000

# Tự động tính phí và xử lý đổi
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