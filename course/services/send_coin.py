import os
import sys
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

# Địa chỉ người nhận (thay bằng địa chỉ testnet thực)
receiver_address = Address.from_primitive("addr_test1qqja25tffmwywjufeycgn86zj7slfj9w4wh5a7ft4png47ue0r2q9x4995mt5xscmehf5swm6qx4flkg98euf3rk45usuerp08")

# Số ADA gửi (100 ADA = 100,000,000 lovelace)
amount_to_send = 100_000_000  # 100 ADA

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
        print(e.message)
        sys.exit(1)

# Kiểm tra số dư ADA
total_ada = sum(int(utxo.amount[0].quantity) for utxo in utxos)
print(f"Tổng ADA khả dụng: {total_ada / 1_000_000} ADA")

if total_ada < amount_to_send + 1_000_000:  # Dự phòng 1 ADA cho phí và UTxO tối thiểu
    print(f"Không đủ ADA để gửi {amount_to_send / 1_000_000} ADA. Cần ít nhất {(amount_to_send + 1_000_000) / 1_000_000} ADA.")
    sys.exit(1)

# Khởi tạo ngữ cảnh chuỗi BlockFrost
cardano = BlockFrostChainContext(project_id=blockfrost_api_key, base_url=base_url)

# Tạo TransactionBuilder
builder = TransactionBuilder(cardano)

builder.add_input_address(main_address)

# Thêm đầu ra để gửi ADA đến người nhận
builder.add_output(TransactionOutput(receiver_address, Value(amount_to_send)))

# Thiết lập TTL (tùy chọn, dựa trên slot hiện tại + buffer)
builder.ttl = cardano.last_block_slot + 1000

# Tự động tính phí và xử lý đổi
builder.auxiliary_data = None  # Tùy chọn: Đặt None nếu không có metadata
signed_tx = builder.build_and_sign([payment_skey], change_address=main_address)

# In chi tiết giao dịch
print(f"Số đầu vào: \t {len(signed_tx.transaction_body.inputs)}")
print(f"Số đầu ra: \t {len(signed_tx.transaction_body.outputs)}")
print(f"Phí: \t\t {signed_tx.transaction_body.fee / 1_000_000} ADA")
print(f"Đã gửi: \t {amount_to_send / 1_000_000} ADA đến {receiver_address}")

# Gửi giao dịch
try:
    tx_id = cardano.submit_tx(signed_tx.to_cbor())
    print(f"Giao dịch đã gửi! ID: {tx_id}")
except Exception as e:
    if "BadInputsUTxO" in str(e):
        print("Đang cố chi tiêu một đầu vào không tồn tại (hoặc đã bị sử dụng).")
    elif "ValueNotConservedUTxO" in str(e):
        print("Giao dịch không được cân bằng. Đầu vào và đầu ra (+phí) không khớp.")
    elif "InputUTxODepletedException" in str(e):
        print("Không đủ ADA trong UTxO để chi trả đầu ra và phí giao dịch.")
    else:
        print(f"Lỗi: {e}")