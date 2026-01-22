"""
Lesson 5 — Consolidate UTxOs

Mục tiêu: gộp tất cả UTxO của địa chỉ về một UTxO đổi duy nhất (giúp giảm số lượng
UTxO và tối ưu phí ở các lần giao dịch sau).

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
python3 -m venv venv


Bước 2: Kích hoạt môi trường (Activate)
Đây là điểm khác biệt chính so với Windows. Trên Linux/Ubuntu, bạn dùng lệnh source:
source venv/bin/activate


Khi thành công, bạn sẽ thấy tên môi trường (venv) xuất hiện phía trước dấu nhắc lệnh (prompt) trong terminal.
Bước 3. Cài đặt thư viện PyCardano
Khi đã ở trong môi trường (venv), việc cài đặt thư viện diễn ra rất nhanh chóng và an toàn.
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

# Tạo khóa từ mnemonic (payment/staking)
#1: Khôi phục ví HDWallet ví phân cấp định danh từ mnemonic bằng chuẩn BIP-32
new_wallet = crypto.bip32.HDWallet.from_mnemonic(wallet_mnemonic)
#2: Tạo khóa thanh toán và khóa đặt cược từ ví HDWallet sử dụng đường dẫn phái sinh chuẩn Cardano
payment_key = new_wallet.derive_from_path(f"m/1852'/1815'/0'/0/0")
staking_key = new_wallet.derive_from_path(f"m/1852'/1815'/0'/2/0")
# Giải thích về các thành phần trong đường dẫn phái sinh (derivation path):
# Thành phần,Mã số,Ý nghĩa,Giải thích:
# m :Master Node -->"Gốc của cây, được tạo ra trực tiếp từ Seed (24 từ khóa)."
# 1852 : Purpose -->Chuẩn ví,"CIP-1852: Đây là chuẩn ví hiện đại (Shelley era) hỗ trợ Staking. (Nếu bạn thấy số 44', đó là ví Byron cũ thời 2017, không stake được)."
# 1815': Coin Type -->Loại tiền,Mã số đại diện cho ADA. (Fun fact: 1815 là năm sinh của bà Ada Lovelace - nữ lập trình viên đầu tiên trong lịch sử).
# 0': Account -->Tài khoản,"Giống như các ngăn ví khác nhau. Bạn có thể tạo Account 0 cho bố, Account 1 (1') cho mẹ... chung trên 1 bộ 24 từ. Mặc định luôn dùng 0'."
# 0 hoặc 2:Role --> Vai trò,Rất quan trọng! Xác định loại chìa khóa:  0: External (Payment) - Dùng để nhận tiền/tiêu tiền.  1: Internal (Change) - Ví ẩn dùng để nhận tiền thối lại.  2: Staking - Dùng để ủy thác vào Pool.
# 0: Index -->Số thứ tự,"Địa chỉ thứ mấy trong chuỗi. 0 là địa chỉ đầu tiên, 1 là địa chỉ thứ 2... Có thể tạo ra hàng tỷ địa chỉ (index) khác nhau."
#3: Chuyển đổi khóa sang định dạng ExtendedSigningKey của pycardano
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

# Ngữ cảnh chuỗi để build/submit giao dịch
# === BƯỚC 4: XÂY DỰNG GIAO DỊCH ===
# Tạo context để builder biết thông tin mạng (slot, protocol param...)
cardano = BlockFrostChainContext(project_id=blockfrost_api_key, base_url=base_url)

# TransactionBuilder cho consolidate
builder = TransactionBuilder(cardano)

# Thêm tất cả UTxO làm đầu vào (không dùng add_input_address để đảm bảo gom hết)
# Điểm mấu chốt: thay vì dùng `add_input_address` (chọn UTxO tối ưu), script này
# chủ động add từng UTxO làm input để "gom" hết toàn bộ UTxO hiện có.

# 1. Tại sao không dùng add_input_address (Tự động)?
# PyCardano (và hầu hết các thư viện ví) sử dụng thuật toán Coin Selection (Chọn đồng xu) khi bạn dùng hàm tự động.

# Mục tiêu của Tự động: Là sự TIẾT KIỆM và TỐI ƯU.

# Nó chỉ nhặt ra vừa đủ số UTxO cần thiết để trả cho số tiền bạn muốn gửi + phí.

# Nó sẽ bỏ qua các UTxO còn lại để tiết kiệm phí giao dịch (vì giao dịch càng nhiều đầu vào thì kích thước càng lớn, phí càng cao).

# Ví dụ: Ví bạn có 100 tờ 1 ADA (Tổng 100 ADA).

# Nếu bạn dùng lệnh tự động gửi 5 ADA.

# Thư viện sẽ chỉ nhặt 5 tờ 1 ADA.

# Kết quả: Ví bạn còn lại 95 tờ tiền lẻ. Mục tiêu "Gom UTxO" (Consolidate) THẤT BẠI.

# 2. Tại sao phải dùng Loop add_input từng cái (Thủ công)?
# Mục tiêu của Thủ công: Là sự KIỂM SOÁT TUYỆT ĐỐI.

# Trong bài học Consolidate, mục đích của chúng ta là DỌN NHÀ. Chúng ta muốn ép buộc giao dịch phải "ăn" tất cả mọi thứ đang có, dù là những đồng vụn vặt nhất (Dust).

# Bằng cách viết vòng lặp for, chúng ta ra lệnh: "Tôi không quan tâm cần bao nhiêu, hãy lấy HẾT tất cả những gì tôi tìm thấy và ném vào lò lửa (Input)."
# === BẮT ĐẦU VÒNG LẶP XỬ LÝ UTXO ===
print(f"\n--- TÌM THẤY {len(utxos)} UTXO. BẮT ĐẦU GỘP... ---")
# Để add từng UTxO vào Builder chúng ta phải xử lý thủ công từng bước chúng ta phải khởi tạo
# Từng UTXO bao gồm:
# - TransactionInput (tham chiếu đến mã giao dịch + index)
# - TransactionOutput (địa chỉ + giá trị)
# Dưới đây là quy trình chi tiết cho mỗi UTxO:
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

# 1. Chờ giao dịch confirm
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