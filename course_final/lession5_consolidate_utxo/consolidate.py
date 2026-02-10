"""
Xin chào mọi người, chào mừng mọi người đã đến với bài học thứ 5
trong chuỗi video hướng dẫn lập trình Pycardano của chúng tôi!
Thì trong bài học này, chúng ta sẽ tìm hiểu cách

Lesson 5 — Consolidate UTxOs

Mục tiêu của kỹ thuật này đó là: gộp tất cả UTxO của địa chỉ 
về một UTxO duy nhất
Như các bạn đã biết,
Trong giao dịch trên Cardano, mỗi lần bạn nhận tiền, 
bạn sẽ nhận được một UTxO (Unspent Transaction Output) riêng biệt.
Nếu bạn nhận nhiều lần, bạn sẽ có nhiều UTxO lẻ tẻ.

Điều này dẫn đến việc tạo ra nhiều đầu vào (inputs) trong giao dịch, 
làm tăng kích thước giao dịch và phí giao dịch.
Để tối ưu hóa, bạn có thể gộp (consolidate) 
tất cả các UTxO lẻ thành một UTxO duy nhất.
Điều này giúp giảm số lượng đầu vào trong các giao dịch tương lai, 
tiết kiệm phí và làm cho việc quản lý tài sản trở nên dễ dàng hơn.


Bước 1: Khởi tạo môi trường ảo
Chạy lệnh sau để tạo thư mục venv chứa môi trường riêng:
python -m venv venv


Bước 2: Kích hoạt môi trường (Activate)
Đây là điểm khác biệt chính so với Windows. Trên Linux/Ubuntu, bạn dùng lệnh source:
.\venv\Scripts\Activate.ps1


Khi thành công, bạn sẽ thấy tên môi trường (venv) 
xuất hiện phía trước dấu nhắc lệnh (prompt) trong terminal.
Bước 3. Cài đặt thư viện PyCardano
Khi đã ở trong môi trường (venv), 
việc cài đặt thư viện diễn ra rất nhanh chóng và an toàn.
Chạy lệnh:
pip install pycardano blockfrost-python python-dotenv

Bước 4 : Tạo file .env và điền biến môi trường

"""
import os
import sys
from blockfrost import BlockFrostApi, ApiError, ApiUrls
from dotenv import load_dotenv
from pycardano import *
import time

# === Bước 1: Cấu hình môi trường ===
# Tải biến môi trường
load_dotenv()

network= os.getenv("BLOCKFROST_NETWORK")
blockfrost_api_key = os.getenv("BLOCKFROST_PROJECT_ID")
wallet_mnemonic = os.getenv("MNEMONIC")

# Thiết lập mạng và URL API Blockfrost
if network == "testnet":
    network = Network.TESTNET
    api_url = ApiUrls.preprod.value
else:
    network = Network.MAINNET
    api_url = ApiUrls.mainnet.value

# === Bước 2: Khôi phục ví từ mnemonic ===

# Khôi phục ví HDwallet từ mnemonic
new_wallet = crypto.bip32.HDWallet.from_mnemonic(wallet_mnemonic)

# Tạo khóa thanh toán và khóa đặt cược từ derivation path
payment_key=new_wallet.derive_from_path("m/1852'/1815'/0'/0/0")
staking_key=new_wallet.derive_from_path("m/1852'/1815'/0'/2/0")

# Tạo khóa để ký giao dịch cho cả payment và staking
payment_skey= ExtendedSigningKey.from_hdwallet(payment_key)
staking_skey= ExtendedSigningKey.from_hdwallet(staking_key)

# Tạo địa chỉ main từ phần stakeing key và payment key

main_address= Address(payment_skey.to_verification_key().hash(),
                        staking_skey.to_verification_key().hash(),
                        network=network)

print(f"Main Address: {main_address}")

# === Bước 3: Kết nối với Blockfrost API và lấy utxo ===
# Khởi tạo kết nối với Blockfrost API
api= BlockFrostApi(project_id=blockfrost_api_key, base_url=api_url)

# Lấy tất cả UTxO của địa chỉ main_address
try: 
    utxos= api.address_utxos(main_address)
except Exception as e:
    if e.status_code == 404:
        print("Địa chỉ chưa có UTxO nào.")
        if network == "testnet":
            print("Vui lòng sử dụng faucet testnet để gửi một ít ADA vào địa chỉ này.")
        sys.exit(1)
    else:
        print(f"Lỗi khi lấy UTxO: {e}")
        sys.exit(1)

# === Bước 4: Xây dựng giao dịch ===

# Tạo context giao dịch để xây dựng giao dịch
context= BlockFrostChainContext(project_id=blockfrost_api_key, base_url=api_url)


# Tạo đối tượng TransactionBuilder
builder= TransactionBuilder(context)

# Thêm tất cả UTxO vào làm đầu vào (inputs) của giao dịch
# Trên thư viện pycardano, để add input vào giao dịch chúng ta có thể
# dùng 2 cách:
# Cách 1: Dùng hàm add_input_address của builder để add input vào giao dịch
# tuy nhiên cách này có một vài điểm hạn chế đó là chúng ta sẽ không
# thể kiểm soát được việc chọn UTxO nào để add vào giao dịch
# ==> chúng ta không sử dụng phương pháp này trong bài học này
# Cách 2: đó là dùng hàm add_input(utxo) của builder để thực hiện
# add từng UTxO một vào giao dịch 
# ===> cách này sẽ giúp chúng ta kiểm soát được việc chọn UTxO nào
# để add vào giao dịch

# Để tạo ra đối tượng UTxO làm đầu vào cho hàm add_input(utxo)
# chúng ta cần tạo ra một đối tượng utxo có 2 thành phần chính đó là
# TransactionInput và TransactionOutput
# Trong TransactionInput sẽ bao gồm tx_hash và tx_index của UTxO
# Trong TransactionOutput sẽ bao gồm address và value của UTxO

# Duyệt qua tất cả UTxO và thêm vào giao dịch
print(f"Danh sách UTxO sẽ được gộp: {len(utxos)} UTxOs")

for i, utxo in enumerate(utxos):
    # in thông tin chi tiết của từng UTxO
    print(f"\n[{i+1}]/{len(utxos)} UTxO Details: {utxo.tx_hash}# Index{utxo.tx_index}")
    # Tạo TransactionInput từ tx_hash và tx_index
    tx_input= TransactionInput.from_primitive([utxo.tx_hash, utxo.tx_index])

    # Xử lý value của UTxO và in chi tiết thông tin tài sản:
    lovelace_amount= 0
    multi_asset={}
    for asset in utxo.amount:
        if asset.unit == "lovelace":
            lovelace_amount= int(asset.quantity)
            print(f" - ADA: {lovelace_amount / 1_000_000} ADA")
        else:
            policy_id= asset.unit[:56]
            asset_name= asset.unit[56:]
            quantity= int(asset.quantity)
            
            # In thông tin tài sản đa dạng (multi-asset)
            try:
                asset_name_str= bytes.fromhex(asset_name).decode("utf-8") # Convert hex to string
            except:
                asset_name_str= asset_name  # Nếu không thể decode, giữ nguyên dạng hex
            print(f" - Asset: {policy_id}.{asset_name_str} - Quantity: {quantity}")
            # Xây dựng multi_asset dictionary để xử lý value
            if policy_id not in multi_asset:
                multi_asset[policy_id]= {}
            multi_asset[policy_id][asset_name]= quantity
    # Tạo TransactionOutput từ address và value
    # Xây dựng value
    if multi_asset:
        value = Value.from_primitive([lovelace_amount, multi_asset])
    else:
        value = Value.from_primitive([lovelace_amount])
    # Tạo TransactionOutput
    tx_output= TransactionOutput(address=main_address, amount=value)
    # Tạo UTxO từ TransactionInput và TransactionOutput
    utxo_to_add= UTxO(tx_input, tx_output)
    # Thêm UTxO vào giao dịch
    builder.add_input(utxo_to_add)

# === Bước 5: Thực hiện ký giao dịch và  gửi giao dịch ===

signed_tx= builder.build_and_sign([payment_skey], 
                                  change_address=main_address)
# Hiển thị thông tin giao dịch đã ký

# số dư:
balance= sum(
    int(a.quantity) for utxo in utxos for a in utxo.amount if a.unit == "lovelace"
)

print(f"\nTổng số ADA trong tất cả UTxO: {balance / 1_000_000} ADA")
print(f"Số lượng UTxO trước khi gộp: {len(signed_tx.transaction_body.inputs)} UTxOs")
print(f"Số lượng UTxO sau khi gộp: {len(signed_tx.transaction_body.outputs)} UTxOs")
print(f"Phí giao dịch: {signed_tx.transaction_body.fee / 1_000_000} ADA")

# Gửi giao dịch đã ký lên mạng lưới
try:
    tx_id= context.submit_tx(signed_tx.to_cbor())
    print(f"Giao dịch đã được gửi thành công! Tx ID: {tx_id}")
except Exception as e:
    if "BadInputsUTxO" in str(e):
        print("Lỗi: Một hoặc nhiều UTxO đã được sử dụng trong một giao dịch khác.")
    elif "ValueNotConservedUTxO" in str(e):
        print("Lỗi: Giá trị không được bảo toàn. Vui lòng kiểm tra lại số lượng đầu vào và đầu ra.")
    else:
        print(f"Lỗi khi gửi giao dịch: {e}")

# thực  hiện chờ và kiểm tra UTXO trong ví sau khi giao dịch hoàn tất

def wait_for_tx(tx_hash):
    """Chờ cho đến khi giao dịch được xác nhận trên blockchain."""
    for i in range(30):
        try:
            tx = api.transaction(tx_hash)
            if tx:
                print("Giao dịch đã được xác nhận trên blockchain.")
                return True
        except ApiError:
            print("Đang chờ giao dịch được xác nhận vui lòng chờ thêm 10s...")
            time.sleep(10)
    return False
if wait_for_tx(tx_id):
    # chờ thêm một chút để đồng bộ hóa blockfrost
    print("Đang đồng bộ hóa dữ liệu từ Blockfrost...")
    time.sleep(20)
    # Lấy lại UTxO của địa chỉ sau khi giao dịch hoàn tất
    try:
        new_utxos= api.address_utxos(main_address)
        print(f"Số lượng UTxO hiện tại sau khi gộp: {len(new_utxos)} UTxOs")
        for utxo in new_utxos:
            print(f" - UTxO: {utxo.tx_hash}# Index{utxo.tx_index}")
            total_ada= 0
            print("   Tài sản bên trong:")
            for asset in utxo.amount:
                if asset.unit == "lovelace":
                    ada_amount= int(asset.quantity)
                    total_ada += ada_amount
                    print(f"     - ADA: {ada_amount / 1_000_000} ADA")
                else:
                    policy_id= asset.unit[:56]
                    asset_name= asset.unit[56:]
                    quantity= int(asset.quantity)
                    try:
                        asset_name_str= bytes.fromhex(asset_name).decode("utf-8") # Convert hex to string
                    except:
                        asset_name_str= asset_name  # Nếu không thể decode, giữ nguyên dạng hex
                    print(f"     - Asset: {policy_id}.{asset_name_str} - Quantity: {quantity}")
    except Exception as e:
        print(f"Lỗi khi lấy UTxO sau giao dịch: {e}")
else:
    print("Giao dịch không được xác nhận trong thời gian chờ.")