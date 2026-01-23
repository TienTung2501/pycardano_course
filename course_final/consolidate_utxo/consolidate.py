"""
Lesson 5 — Consolidate UTxOs

Mục tiêu: gộp tất cả UTxO của địa chỉ về một UTxO duy nhất (giúp giảm số lượng
UTxO và tối ưu phí giao dịch).

Mọi người có thể hiểu đơn giản như sau:
Hãy tưởng tượng ví của các bạn giống như một con heo đất.
Mỗi lần ai đó chuyển tiền cho bạn, họ nhét vào một tờ tiền.
Nếu bạn nhận 100 lần mỗi lần 1 ADA, trong heo đất sẽ có 100 tờ 1 ADA.
Khi bạn muốn mua một món đồ giá 90 ADA, bạn phải lôi 90 tờ tiền đó ra để trả.
Việc đếm 90 tờ tiền tốn thời gian và công sức.
Trong Blockchain, việc 'đếm' này tốn phí giao dịch (Fee) và dung lượng mạng.
Bài hôm nay, chúng ta sẽ học cách gom tất cả tiền lẻ đổi thành một tờ tiền mệnh giá lớn duy nhất. 
Kỹ thuật này gọi là Consolidate UTxO.

Bước 1: Khởi tạo môi trường ảo
Chạy lệnh sau để tạo thư mục venv chứa môi trường riêng:
python -m venv venv


Bước 2: Kích hoạt môi trường (Activate)
.\venv\Scripts\Activate.ps1  # Dùng cho PowerShell


Khi thành công, bạn sẽ thấy tên môi trường (venv) xuất hiện phía trước dấu nhắc lệnh (prompt) trong terminal.
Bước 3. Cài đặt thư viện PyCardano, Blockfrost-python và python-dotenv
Khi đã ở trong môi trường (venv), việc cài đặt thư viện diễn ra rất nhanh chóng và an toàn.
Chạy lệnh:
pip install pycardano blockfrost-python python-dotenv

Bước 4 : Tạo file .env và điền biến môi trường

"""
import os
import sys
from dotenv import load_dotenv
from blockfrost import BlockFrostApi, ApiError, ApiUrls
from pycardano import *
import time

# === Bước 1: CẤU BIẾN BIẾN MÔI TRƯỜNG ===
load_dotenv()
network = os.getenv("BLOCKFROST_NETWORK")
blockfrost_api_key = os.getenv("BLOCKFROST_PROJECT_ID")
wallet_mnemonic = os.getenv("MNEMONIC")

# Thiết lập mạng và URL API
if network == "testnet":
    api_url = ApiUrls.preprod.value
    network_id = Network.TESTNET
else:
    api_url = ApiUrls.mainnet.value
    network_id = Network.MAINNET

# === BƯỚC 2: KHÔI PHỤC VÍ TỪ MNEMONIC ===

# khôi phuc ví từ mnemonic
new_wallet = crypto.bip32.HDWallet.from_mnemonic(wallet_mnemonic)

# Tạo payment key và stake key từ wallet

payment_key=new_wallet.derive_from_path("m/1852'/1815'/0'/0/0")
stake_key=new_wallet.derive_from_path("m/1852'/1815'/0'/2/0")

# Tạo skey của payment và stake
payment_skey=ExtendedSigningKey.from_hdwallet(payment_key)
stake_skey=ExtendedSigningKey.from_hdwallet(stake_key)

# Tạo main address từ payment và stake vkey
main_address=Address(payment_skey.to_verification_key().hash(),stake_skey.to_verification_key().hash(),network_id)

print(f"Main Address: {main_address}")

# === BƯỚC 3: KẾT NỐI VỚI BLOCKFROST API , lấy utxo ===
api = BlockFrostApi(
    project_id=blockfrost_api_key,
    base_url=api_url
)
# Lấy UTxOs của địa chỉ chính
try:
    utxos = api.address_utxos(main_address)
except Exception as e:
    if e.status_code == 404:
        print("Địa chỉ chưa có UTxO nào.")
        if network == "testnet":
            print("Vui lòng sử dụng faucet để gửi một ít ADA vào địa chỉ này.")
            print(f"Faucet testnet: https://testnets.cardano.org/en/testnets/cardano/tools/faucet/")
        sys.exit(1)
    else:
        print(f"Lỗi khi lấy UTxO: {e}")
        sys.exit(1)

# === BƯỚC 4: TẠO GIAO DỊCH CONSOLIDATE UTXO ===
# Tạo context cho giao dịch
context = BlockFrostChainContext(project_id=blockfrost_api_key, base_url=api_url)

# Tạo transaction builder
builder = TransactionBuilder(context)

# Tiếp theo thêm tất cả UTxO vào transaction builder
# Để add input ta có thể dùng 2 cách sau đây:
# builder.add_input_address(main_address) # cách này sẽ tự động thêm UTxO của địa chỉ vào builder hạn chế đó là không kiểm soát được UTxO nào được thêm vào
# builder.add_input(utxos)  # cách này cho phép ta kiểm soát được UTxO nào được thêm vào vì là hướng dẫn gộp utxo nên ta phải add tất cả utxo vào
# cần xây dựng hoặc tạo UTXO để truyền vào hàm add_input utxo
# Để tạo ra utxo nó sẽ có 2 thành phần chính là TransactionInput và TransactionOutput
# Trong transactionInput sẽ bao gồm tx_hash và tx_index
# Trong transactionOutput sẽ bao gồm address và value chính vì thế mà mỗi một utxo sẽ được tạo ra từ 2 thành phần này
# Khi lấy utxo từ blockfrost api ta sẽ nhận được một danh sách các utxo
# Ta sẽ duyệt qua từng utxo trong danh sách và tạo TransactionInput và TransactionOutput


# Dưới đây là chi tiết về quá trình tạo và thêm UTxO vào transaction builder và hiển thị thông tin UTxO
for i,utxo in enumerate(utxos):
    # in thông tin của từng utxo
    print(f"\n [{i+1}/{len(utxos)}] UTxO Info: {utxo.tx_hash}# Index: {utxo.tx_index}")
    # Tạo TransactionInput từ tx_hash và tx_index
    tx_input = TransactionInput.from_primitive([utxo.tx_hash, utxo.tx_index])
    # Hiển thị thong tin của utxo
    lovelace_ammount = 0
    multi_asset = {}
    for asset in utxo.amount:
        if asset.unit == "lovelace":
            lovelace_ammount = int(asset.quantity)
            print(f"    {lovelace_ammount / 1_000_000} ADA")
        else:
            policy_id = asset.unit[:56]
            asset_name = asset.unit[56:]
            quantity = int(asset.quantity)
            try:
                asset_display_name = bytes.fromhex(asset_name).decode('utf-8') # chuyển từ hex sang string
            except:
                asset_display_name = asset_name  # nếu không chuyển được thì giữ nguyên giá trị hex
            print(f"    Asset: {asset_display_name} (Policy ID: {policy_id}) - Quantity: {quantity}")
            # Thêm vào multi_asset dictionary để hiển thị
            if policy_id not in multi_asset:
                multi_asset[policy_id] = {}
            multi_asset[policy_id][asset_name] = quantity
    if multi_asset:
        value= Value.from_primitive([lovelace_ammount, multi_asset])
    else:
        value= Value.from_primitive([lovelace_ammount])
    # Tạo TransactionOutput từ main_address và value
    tx_output = TransactionOutput(main_address, value)
    # Tạo UTxO từ TransactionInput và TransactionOutput
    utxo_obj = UTxO(tx_input, tx_output)
    # Thêm UTxO vào transaction builder
    builder.add_input(utxo_obj)
# In tổng số UTxO đã thêm
print(f"\nTổng số UTxO đã thêm vào giao dịch: {len(utxos)}")

# === BƯỚC 5: KÝ GIAO DỊCH VÀ GỬI LÊN MẠNG ONCHAIN ===
signed_tx = builder.build_and_sign([payment_skey], change_address=main_address)

# Hiển thị một số thông tin của giao dịch

balance_ada = sum(
    int(a.quantity)
    for u in utxos
    for a in u.amount
    if a.unit == "lovelace"
)
print(f"\nTổng số ADA trong tất cả UTxO: {balance_ada / 1_000_000} ADA")
print(f"Số lượng UTXO trước khi gộp: {len(signed_tx.transaction_body.inputs)}")
print(f"Số lượng UTXO sau khi gộp: {len(signed_tx.transaction_body.outputs)}")
print(f"Phí giao dịch: {signed_tx.transaction_body.fee / 1_000_000} ADA")

# Gửi giao dịch lên mạng
try:
    tx_id= context.submit_tx(signed_tx.to_cbor())
    print(f"\nGiao dịch đã được gửi thành công! Tx ID: {tx_id}")
except Exception as e:
    if "BadInputsUTxO" in str(e):
        print("Lỗi: Một số UTxO đã được sử dụng trong một giao dịch khác. Vui lòng thử lại.")
    elif "ValueNotConserved" in str(e):
        print("Lỗi: Giá trị không được bảo toàn. Vui lòng kiểm tra lại UTxO và số dư.")
    else:
        print(f"Lỗi khi gửi giao dịch: {e}")

# Hàm đợi giao dịch được xác nhận
def wait_for_tx(tx_hash):
    for i in range(30):# lặp 30 lần kiểm tra mỗi 10 giây
        try:
            tx = api.transaction(tx_hash)
            if tx:
                print("Giao dịch đã được xác nhận trên blockchain!")
                return True
        except ApiError:
            print("Giao dịch chưa được xác nhận, đang chờ tiếp 10 giây...")
            time.sleep(10)
    return False
# Gọi hàm đợi giao dịch được xác nhận
if wait_for_tx(tx_id):
    print("\n Đang cập nhật lại danh sách UTxO sau khi gộp...")
    # Đợi thêm 20 giây để blockfrost đồng bộ
    time.sleep(20)
    # Lấy lại UTxO sau khi gộp
    try:
        utxos_after = api.address_utxos(main_address)
        print(f"Số lượng UTxO hiện tại sau khi gộp: {len(utxos_after)}")
        # Hiển thị thông tin UTxO hiện tại
        for utxo in utxos_after:
            print(f"UTxO: {utxo.tx_hash}# Index: {utxo.tx_index}")
            for asset in utxo.amount:
                if asset.unit == "lovelace":
                    print(f"    {int(asset.quantity) / 1_000_000} ADA")
                else:
                    policy_id = asset.unit[:56]
                    asset_name = asset.unit[56:]
                    quantity = int(asset.quantity)
                    try:
                        asset_display_name = bytes.fromhex(asset_name).decode('utf-8') # chuyển từ hex sang string
                    except:
                        asset_display_name = asset_name  # nếu không chuyển được thì giữ nguyên giá trị hex
                    print(f"    Asset: {asset_display_name} (Policy ID: {policy_id}) - Quantity: {quantity}")
    except Exception as e:
        print(f"Lỗi khi lấy UTxO sau khi gộp: {e}")
else:
    print("Giao dịch không được xác nhận trong thời gian chờ. Vui lòng kiểm tra lại trên blockchain.")
                

    