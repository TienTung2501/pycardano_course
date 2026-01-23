"""
Xin chào mọi người, chào mừng đến với bài học thứ 6 
trong chuỗi hướng dẫn Pycardano của tôi!
Thì trong bài học này, chúng ta sẽ tìm hiểu cách

Lesson 5 — Consolidate UTxOs

Mục tiêu: gộp tất cả UTxO của địa chỉ về một UTxO đổi duy nhất
Trong giao dịch trên Cardano, mỗi lần bạn nhận tiền, 
bạn sẽ nhận được một UTxO (Unspent Transaction Output) riêng biệt.
Nếu bạn nhận nhiều lần, bạn sẽ có nhiều UTxO lẻ tẻ.
Khi thực hiện giao dịch tiêu tiền, bạn phải sử dụng từng UTxO một.
Điều này dẫn đến việc tạo ra nhiều đầu vào (inputs) trong giao dịch, 
làm tăng kích thước giao dịch và phí giao dịch.
Để tối ưu hóa, bạn có thể gộp (consolidate) 
tất cả các UTxO lẻ thành một UTxO duy nhất.
Điều này giúp giảm số lượng đầu vào trong các giao dịch tương lai, 
tiết kiệm phí và làm cho việc quản lý tài sản trở nên dễ dàng hơn.


Bước 1: Khởi tạo môi trường ảo
Chạy lệnh sau để tạo thư mục venv chứa môi trường riêng:
python3 -m venv venv


Bước 2: Kích hoạt môi trường (Activate)
Đây là điểm khác biệt chính so với Windows. Trên Linux/Ubuntu, bạn dùng lệnh source:
source venv/bin/activate


Khi thành công, bạn sẽ thấy tên môi trường (venv) 
xuất hiện phía trước dấu nhắc lệnh (prompt) trong terminal.
Bước 3. Cài đặt thư viện PyCardano
Khi đã ở trong môi trường (venv), 
việc cài đặt thư viện diễn ra rất nhanh chóng và an toàn.
Chạy lệnh:
pip install pycardano blockfrost-python

Bước 4 : Tạo file .env và điền biến môi trường

"""

import os
import sys
from blockfrost import ApiError, ApiUrls, BlockFrostApi
from dotenv import load_dotenv
from pycardano import *
import time
# === BƯỚC 1: CẤU HÌNH MÔI TRƯỜNG ===
# Tải biến môi trường
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

# === BƯỚC 2: KHÔI PHỤC VÍ TỪ MNEMONIC ===


#=================Không nói đoạn này=======================
# Giải thích về cơ chế ví của Cardano:
# Trong bài học trước, mình đã chia sẻ khá chi tiết về lý thuyết ví trên Cardano. Ở video này, mình sẽ đi sâu vào code để các bạn thấy rõ cách nó hoạt động thực tế.
# > Về cơ bản, ví Cardano sử dụng công nghệ HD Wallet (Ví phân cấp định danh). Quy trình khởi tạo diễn ra qua hai bước chuẩn:
# > Đầu tiên là chuẩn BIP-39 (giống với Bitcoin): Giúp chúng ta tạo ra cụm Mnemonic gồm 24 từ khóa tiếng Anh dễ nhớ. Quan trọng hơn, 
# từ 24 từ khóa này, thuật toán sẽ sinh ra một chuỗi Seed (hạt giống) - đây là gốc rễ của mọi dữ liệu trong ví.
# > Tiếp theo là chuẩn BIP-32: Từ chuỗi Seed gốc đó, chuẩn này giúp xây dựng lên cấu ví phân cấp là một 'cây thư mục' phân cấp khổng lồ. 
# Từ gốc này, chúng ta có thể tạo ra vô số nhánh con và ví con. Để tìm đúng cái ví mình cần trong cái cây khổng lồ đó, 
# chúng ta cần một 'địa chỉ đường đi' cụ thể được gọi là Derivation Path (Đường dẫn phái sinh).

# Ví Cardano sử dụng mô hình ví phân cấp định danh (HDWallet) theo chuẩn BIP-32.
# Mỗi ví HDWallet có thể tạo ra nhiều cặp khóa (key pair) và địa chỉ (address)
# thông qua các đường dẫn phái sinh (derivation path) khác nhau.

#=================Không nói đoạn này=======================


# Tạo khóa từ mnemonic (payment/staking)
#1: Khôi phục ví HDWallet ví phân cấp định danh từ mnemonic bằng chuẩn BIP-32
new_wallet = crypto.bip32.HDWallet.from_mnemonic(wallet_mnemonic)

#2: Tạo khóa thanh toán và khóa đặt cược từ ví 
# HDWallet sử dụng đường dẫn phái sinh chuẩn Cardano
payment_key = new_wallet.derive_from_path(f"m/1852'/1815'/0'/0/0")
staking_key = new_wallet.derive_from_path(f"m/1852'/1815'/0'/2/0")


#=================Không nói đoạn này=======================
# Giải thích về các thành phần trong đường dẫn phái sinh (derivation path):
# Thành phần,Mã số,Ý nghĩa,Giải thích:
# m :Master Node -->"Gốc của cây, được tạo ra trực tiếp từ Seed (24 từ khóa)."
# 1852 : Purpose -->Chuẩn ví,"CIP-1852: Đây là chuẩn ví hiện đại (Shelley era) hỗ trợ Staking. (Nếu bạn thấy số 44', đó là ví Byron cũ thời 2017, không stake được)."
# 1815': Coin Type -->Loại tiền,Mã số đại diện cho ADA. (Fun fact: 1815 là năm sinh của bà Ada Lovelace - nữ lập trình viên đầu tiên trong lịch sử).
# 0': Account -->Tài khoản,"Giống như các ngăn ví khác nhau. Bạn có thể tạo Account 0 cho bố, Account 1 (1') cho mẹ... chung trên 1 bộ 24 từ. Mặc định luôn dùng 0'."
# 0 hoặc 2:Role --> Vai trò,Rất quan trọng! Xác định loại chìa khóa:  0: External (Payment) - Dùng để nhận tiền/tiêu tiền.  1: Internal (Change) - Ví ẩn dùng để nhận tiền thối lại.  2: Staking - Dùng để ủy thác vào Pool.
# 0: Index -->Số thứ tự,"Địa chỉ thứ mấy trong chuỗi. 0 là địa chỉ đầu tiên, 1 là địa chỉ thứ 2... Có thể tạo ra hàng tỷ địa chỉ (index) khác nhau."
#=================Không nói đoạn này=======================


#3: Tạo khóa để ký giao dịch cho cả payment và staking
payment_skey = ExtendedSigningKey.from_hdwallet(payment_key)
staking_skey = ExtendedSigningKey.from_hdwallet(staking_key)

# Địa chỉ ví chính để gom UTxO
main_address = Address(
    payment_part=payment_skey.to_verification_key().hash(),
    staking_part=staking_skey.to_verification_key().hash(),
    network=cardano_network,
)

print(f"Địa chỉ được tạo: {main_address}")
# === BƯỚC 3: KẾT NỐI BLOCKFROST VÀ LẤY UTXO ===
# Khởi tạo Blockfrost API để liệt kê UTxO
api = BlockFrostApi(project_id=blockfrost_api_key, base_url=base_url)

# Lấy tất cả UTxO của địa chỉ
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


# === BƯỚC 4: XÂY DỰNG GIAO DỊCH ===
# Tạo context để builder biết thông tin mạng (slot, protocol param...)
cardano = BlockFrostChainContext(project_id=blockfrost_api_key, base_url=base_url)

# TransactionBuilder cho consolidate
builder = TransactionBuilder(cardano)

# Tiếp theo thêm tất cả UTxO vào transaction builder
# Để add input ta có thể dùng 2 cách sau đây:
# builder.add_input_address(main_address) 
# # cách này sẽ tự động thêm UTxO của địa chỉ vào builder 
# hạn chế đó là không kiểm soát được UTxO nào được thêm vào
# builder.add_input(utxos)  
# # cách này cho phép ta kiểm soát được UTxO nào được thêm vào 
# vì là thực hiện consolidate nên cách này phù hợp hơn
# cần xây tạo UTXO để truyền vào hàm add_input(utxo)
# # Có một vấn đề đó là khi lấy utxo từ blockfrost api 
# ta sẽ nhận được một danh sách các utxo 
# nhưng đây là dữ liệu thô của blockfrost 
# chưa phải là utxo object của pycardano
# # Để tạo ra utxo nó sẽ có 2 thành phần chính là TransactionInput và TransactionOutput
# # Trong transactionInput sẽ bao gồm tx_hash và tx_index
# # Trong transactionOutput sẽ bao gồm address và value 
# # chính vì thế mà mỗi một utxo sẽ được tạo ra từ 2 thành phần này
# # Khi lấy utxo từ blockfrost api ta sẽ nhận được một danh sách các utxo
# # Ta sẽ duyệt qua từng utxo trong danh sách và tạo TransactionInput và TransactionOutput
# === BẮT ĐẦU VÒNG LẶP XỬ LÝ UTXO ===
print(f"\n--- TÌM THẤY {len(utxos)} UTXO. BẮT ĐẦU GỘP... ---")
for i, utxo in enumerate(utxos):
    # --- PHẦN IN THÔNG TIN (LOGGING) ---
    print(f"\n[{i+1}/{len(utxos)}] UTxO: {utxo.tx_hash} #Index:{utxo.tx_index}")
    
    # 1. Tạo Input
    tx_input = TransactionInput.from_primitive([utxo.tx_hash, utxo.tx_index])
    
    # 2. Xử lý Value & In chi tiết tài sản
    lovelace_amount = 0
    multi_assets = {} 

    for asset in utxo.amount:
        if asset.unit == "lovelace":
            lovelace_amount = int(asset.quantity)
            print(f"   └── {lovelace_amount / 1_000_000:,.6f} ADA") # In ra số ADA đã format
        else:
            # Tách PolicyID và AssetName
            policy_id = asset.unit[:56]
            asset_name_hex = asset.unit[56:] 
            quantity = int(asset.quantity)

            # Cố gắng dịch tên Token từ Hex sang chữ cái (ASCII) cho dễ đọc
            try:
                asset_name_str = bytes.fromhex(asset_name_hex).decode("utf-8")
            except:
                asset_name_str = f"(Hex) {asset_name_hex}" # Nếu không dịch được thì để nguyên Hex

            print(f"   └── Token: {asset_name_str} (SL: {quantity:,}) - [Policy: {policy_id[:8]}...]")

            # Thêm vào dictionary cho Value
            if policy_id not in multi_assets:
                multi_assets[policy_id] = {}
            multi_assets[policy_id][asset_name_hex] = quantity

    # 3. Tạo Value object
    if multi_assets:
        value = Value.from_primitive([lovelace_amount, multi_assets])
    else:
        value = Value.from_primitive([lovelace_amount])

    # 4. Thêm vào Builder
    tx_output = TransactionOutput(main_address, value)
    utxo_obj = UTxO(tx_input, tx_output)
    builder.add_input(utxo_obj)

print("\n--- ĐÃ THÊM TẤT CẢ VÀO BUILDER ---")

# Không thêm output cụ thể: để builder tự cân bằng (phí + 1 output đổi) về địa chỉ
# === BƯỚC 5: TÍNH TOÁN VÀ KÝ ===
# Mẹo: Không set output. Ta set change_address = main_address.
# Vì bản chất giao dịch là chi tiêu toàn bộ input, để tạo ra 1 output duy nhất trả về chính ví mình nên không cần add output.
# Builder sẽ lấy (Tổng Input) - (Phí) = (Tiền thối lại).
# Tiền thối lại này chính là cái UTxO to bự mà ta muốn tạo.
builder.auxiliary_data = None  # Tùy chọn: Đặt None nếu không có metadata
signed_tx = builder.build_and_sign([payment_skey], change_address=main_address)

# === BƯỚC 6: HIỂN THỊ VÀ GỬI ===
# Hiển thị thông tin giao dịch trước khi gửi
balance_lovelace = sum(
    int(a.quantity)
    for u in utxos
    for a in u.amount
    if a.unit == "lovelace"
)

print(f"Số dư địa chỉ:\t {balance_lovelace / 1_000_000} ADA")
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

# Khi chúng ta submit giao dịch, mặc dù submit đã thành công
# nhưng phải mất một khoảng thời gian để giao dịch được xác nhận on-chain
# chính vì thế mà nếu chúng ta query lại UTxO ngay lập tức
# thì rất có thể giao dịch chưa được xác nhận kịp thời
# Vì vậy chúng ta cần chờ một khoảng thời gian
# sau đó mới query lại UTxO để lấy thông tin chính xác nhất
# Để làm được điều này chúng ta sẽ viết hàm wait_for_tx bên dưới
# hàm này sẽ lặp lại liên tục kiểm tra giao dịch đã được xác nhận hay chưa
# cứ mỗi lần kiểm tra không thấy sẽ chờ 10 giây rồi kiểm tra lại
# nếu đã được xác nhận thì hàm sẽ trả về True

# === BƯỚC 7: CHỜ XÁC NHẬN VÀ HIỂN THỊ KẾT QUẢ MỚI ===
print("\n--- ĐANG CHỜ GIAO DỊCH ĐƯỢC XÁC NHẬN TRÊN ON-CHAIN ---")
print("Quá trình này có thể mất từ 20 giây đến 2 phút. Vui lòng không tắt script...")

def wait_for_tx(tx_hash):
    """Hàm chờ giao dịch được xác nhận bởi Blockfrost"""
    for i in range(30):  # Thử 30 lần, mỗi lần nghỉ 10s (Tổng 5 phút timeout)
        try:
            # Thử lấy thông tin giao dịch
            tx_detail = api.transaction(tx_hash)
            if tx_detail:
                print(f"Giao dịch đã được xác nhận tại Block: {tx_detail.block}")
                return True
        except ApiError:
            # Nếu lỗi 404 nghĩa là chưa tìm thấy, chờ tiếp
            print(f"[{i+1}/30] Chưa thấy giao dịch, đợi thêm 10s...")
            time.sleep(10)
    return False

# 1. Gọi hàm chờ giao dịch được xác nhận
if wait_for_tx(tx_id):
    print("\n--- ĐANG CẬP NHẬT LẠI DANH SÁCH UTXO ---")
    # Đợi thêm 5s để đảm bảo Blockfrost đã index xong phần UTxO
    time.sleep(5) 
    
    # 2. Lấy lại danh sách UTxO mới
    try:
        new_utxos = api.address_utxos(main_address)
        print(f"HOÀN TẤT! Số lượng UTxO hiện tại: {len(new_utxos)}")
        
        # In ra UTxO duy nhất còn lại
        for utxo in new_utxos:
            print(f"UTXO MỚI: {utxo.tx_hash} #Index:{utxo.tx_index}")
            total_ada = 0
            print("   Tài sản bên trong:")
            for asset in utxo.amount:
                if asset.unit == "lovelace":
                    total_ada = int(asset.quantity) / 1_000_000
                    print(f"{total_ada:,.6f} ADA")
                else:
                    # Decode tên token cho đẹp
                    try:
                        name = bytes.fromhex(asset.unit[56:]).decode("utf-8")
                    except:
                        name = asset.unit[56:]
                    print(f"   - {name}: {int(asset.quantity):,}")
                    
    except Exception as e:
        print(f"Lỗi khi lấy UTxO mới: {e}")
else:
    print("Quá thời gian chờ (Timeout). Hãy kiểm tra thủ công trên Cardanoscan.")