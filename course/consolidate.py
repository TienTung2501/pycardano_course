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

# Tạo địa chỉ chính
main_address = Address(
    payment_part=payment_skey.to_verification_key().hash(),
    staking_part=staking_skey.to_verification_key().hash(),
    network=cardano_network,
)

print(f"Địa chỉ được tạo: {main_address}")

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

# Khởi tạo ngữ cảnh chuỗi BlockFrost
cardano = BlockFrostChainContext(project_id=blockfrost_api_key, base_url=base_url)

# Tạo TransactionBuilder
builder = TransactionBuilder(cardano)

# Thêm tất cả UTxO làm đầu vào
for utxo in utxos:
    tx_input = TransactionInput.from_primitive([utxo.tx_hash, utxo.tx_index])
    # Xử lý UTxO đa tài sản
    value = Value.from_primitive(
        [int(utxo.amount[0].quantity)] + [
            (asset.unit, int(asset.quantity)) for asset in utxo.amount[1:] if asset.unit != "lovelace"
        ]
    )
    tx_output = TransactionOutput(main_address, value)
    utxo_obj = UTxO(tx_input, tx_output)
    builder.add_input(utxo_obj)
# Vòng lặp for utxo in utxos duyệt qua tất cả UTxO lấy từ api.address_utxos(main_address) 
# và thêm từng UTxO vào TransactionBuilder bằng builder.add_input(utxo_obj). 
# Điều này đảm bảo rằng tất cả UTxO của địa chỉ được thêm vào giao dịch, bất kể thuật toán chọn UTxO. Chính vì thế trong phần này sẽ không sử dụng add_input_address nữa.
# builder.add_input_address(main_address) tự động chọn UTxO từ địa chỉ chính sao cho tối ưu hợp lý nhất, nhưng không đảm bảo tất cả UTxO được sử dụng.
# Thêm đầu ra (ví dụ: gửi tất cả về cùng địa chỉ)
# Lưu ý: Điều chỉnh nếu muốn gửi tiền đến địa chỉ khác

# không thêm output cố định để tránh lỗi ValueNotConservedUTxO vì phí sẽ được tính tự động 
# builder.add_output(TransactionOutput(main_address, Value(total_ada)))


# Tự động tính phí và xử lý đổi
builder.auxiliary_data = None  # Tùy chọn: Đặt None nếu không có metadata
signed_tx = builder.build_and_sign([payment_skey], change_address=main_address)

# In chi tiết giao dịch
print(f"Số đầu vào: \t {len(signed_tx.transaction_body.inputs)}")
print(f"Số đầu ra: \t {len(signed_tx.transaction_body.outputs)}")
print(f"Phí: \t\t {signed_tx.transaction_body.fee / 1000000} ADA")

# Gửi giao dịch
try:
    tx_id = cardano.submit_tx(signed_tx.to_cbor())
    print(f"Giao dịch đã gửi! ID: {tx_id}")
except Exception as e:
    if "BadInputsUTxO" in str(e):
        print("Đang cố chi tiêu một đầu vào không tồn tại (hoặc đã bị sử dụng).")
    elif "ValueNotConservedUTxO" in str(e):
        print("Giao dịch không được cân bằng. Đầu vào và đầu ra (+phí) không khớp.")
    else:
        print(e)