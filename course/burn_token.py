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

# Tạo địa chỉ chính (ví gửi và chứa token)
main_address = Address(
    payment_part=payment_skey.to_verification_key().hash(),
    staking_part=staking_skey.to_verification_key().hash(),
    network=cardano_network,
)

print(f"Địa chỉ ví: {main_address}")


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

# Kiểm tra số dư ADA và token
total_ada = 0
total_tokens = 0
asset_name = "Pycardano_test_COINP_003"
asset_name_bytes = asset_name.encode("utf-8")
token_unit = None  # Lưu unit của MichielCOIN (policy_id + asset_name_hex)

for utxo in utxos:
    total_ada += int(utxo.amount[0].quantity)  # ADA (lovelace)
    for asset in utxo.amount[1:]:
        if asset.unit != "lovelace":
            # Kiểm tra xem asset có phải là MichielCOIN không
            if asset.unit.endswith(asset_name_bytes.hex()):
                total_tokens += int(asset.quantity)
                token_unit = asset.unit

print(f"Tổng ADA khả dụng: {total_ada / 1_000_000} ADA")
print(f"Tổng {asset_name} khả dụng: {total_tokens}")

# Kiểm tra số dư token
tokens_to_burn = 100
if total_tokens < tokens_to_burn:
    print(f"Không đủ {asset_name} để đốt. Cần ít nhất {tokens_to_burn}, hiện có {total_tokens}.")
    sys.exit(1)

# Khởi tạo ngữ cảnh chuỗi BlockFrost
cardano = BlockFrostChainContext(project_id=blockfrost_api_key, base_url=base_url)

# Tạo thư mục keys ở cùng cấp với tệp Python
keys_dir = os.path.join(os.path.dirname(__file__), "keys")
if not os.path.exists(keys_dir):
    os.makedirs(keys_dir)

# Định nghĩa đường dẫn tệp khóa trong thư mục keys
policy_skey_path = os.path.join(keys_dir, "policy.skey")
policy_vkey_path = os.path.join(keys_dir, "policy.vkey")

# Kiểm tra xem khóa chính sách có tồn tại không
if not exists(policy_skey_path) or not exists(policy_vkey_path):
    print(f"Không tìm thấy {policy_skey_path} hoặc {policy_vkey_path}. Cần tạo khóa khi phát hành token trước.")
    sys.exit(1)


# Tải khóa chính sách
policy_signing_key = PaymentSigningKey.load(policy_skey_path)
policy_verification_key = PaymentVerificationKey.load(policy_vkey_path)
pub_key_policy = ScriptPubkey(policy_verification_key.hash())
policy = ScriptAll([pub_key_policy])
policy_id = policy.hash()
policy_id_hex = policy_id.payload.hex()
native_scripts = [policy]

# Xác định token để đốt
token = AssetName(asset_name_bytes)
new_asset = Asset()
multiasset = MultiAsset()
new_asset[token] = -tokens_to_burn  # Giá trị âm để đốt token
multiasset[policy_id] = new_asset

# Tạo TransactionBuilder
builder = TransactionBuilder(cardano)

# # Thêm tất cả UTxO làm đầu vào thủ công
# for utxo in utxos:
#     tx_input = TransactionInput.from_primitive([utxo.tx_hash, utxo.tx_index])
    
#     # Xử lý ADA
#     coin = int(utxo.amount[0].quantity)
    
#     # Xử lý multi-asset cho UTxO này: Phân tích asset.unit thành policy_id và asset_name
#     ma = MultiAsset()  # Tạo MultiAsset mới cho mỗi UTxO
#     for asset in utxo.amount[1:]:
#         if asset.unit != "lovelace":
#             unit_hex = asset.unit
#             # Policy ID: 56 ký tự hex đầu (28 bytes)
#             policy_id_hex_utxo = unit_hex[:56]
#             # Asset name: phần còn lại
#             asset_name_hex = unit_hex[56:]
            
#             # Tạo PolicyId và AssetName từ hex
#             policy_id_utxo = PolicyId.from_primitive(bytes.fromhex(policy_id_hex_utxo))
#             asset_name_utxo = AssetName(bytes.fromhex(asset_name_hex))
            
#             # Thêm vào MultiAsset
#             if policy_id_utxo not in ma:
#                 ma[policy_id_utxo] = Asset()
#             ma[policy_id_utxo][asset_name_utxo] = int(asset.quantity)
    
#     # Tạo Value từ coin và multi_asset cho UTxO này
#     value = Value(coin=coin, multi_asset=ma)
#     tx_output = TransactionOutput(main_address, value)
#     utxo_obj = UTxO(tx_input, tx_output)
#     builder.add_input(utxo_obj)
builder.add_input_address(main_address)
# Thêm thông tin đốt token
builder.native_scripts = native_scripts
builder.mint = multiasset

# Kiểm tra số dư ADA có đủ cho phí và UTxO tối thiểu
if total_ada < 2_000_000:  # Dự phòng 2 ADA cho phí và UTxO tối thiểu
    print(f"Không đủ ADA để đốt token. Cần ít nhất 2 ADA, hiện có {total_ada / 1_000_000} ADA.")
    sys.exit(1)

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
print(f"Token đã đốt: \t {tokens_to_burn} {asset_name} từ {main_address}")

# Gửi giao dịch
try:
    tx_id = cardano.submit_tx(signed_tx.to_cbor())
    print(f"Giao dịch đốt token đã gửi! ID: {tx_id}")
except Exception as e:
    if "BadInputsUTxO" in str(e):
        print("Đang cố chi tiêu một đầu vào không tồn tại (hoặc đã bị sử dụng).")
    elif "ValueNotConservedUTxO" in str(e):
        print("Giao dịch không được cân bằng. Đầu vào và đầu ra (+phí) không khớp.")
    elif "InputUTxODepletedException" in str(e):
        print("Không đủ ADA trong UTxO để chi trả phí giao dịch.")
    else:
        print(f"Lỗi: {e}")