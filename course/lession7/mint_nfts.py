"""
Xin chào mọi người, chào mừng đến với bài học thứ 7 
trong chuỗi hướng dẫn Pycardano của tôi!
Thì trong bài học này, chúng ta sẽ tìm hiểu cách

Lesson 7 — Mint Multiple NFTs with CIP-721 metadata
(Với mint 1 NFT tương tự chỉ khác cách tạo metadata và multiasset)

Mục tiêu: Đúc nhiều NFT (mỗi cái = 1) với metadata 721 và trả về ví người phát hành.
Với Token số lượng > 1 thì tương tự như bài trước.
Với NFT số lượng = 1, mỗi NFT có metadata riêng.

Data mẫu NFT (có thể mở rộng thêm):
types = ["lion", "elephant", "panda", "sloth", "tiger", "wolf"]  # ví dụ thuộc tính

assets = [
    {
        "name": "Pycardano_test_NFT_001",
        "attack": str(random.randint(1, 70)),
        "speed": str(random.randint(1, 70)),
        "defense": str(random.randint(1, 70)),
        "health": str(random.randint(1, 70)),
        "type": random.choice(types),
    },
    {
        "name": "Pycardano_test_NFT_002",
        "attack": str(random.randint(1, 70)),
        "speed": str(random.randint(1, 70)),
        "defense": str(random.randint(1, 70)),
        "health": str(random.randint(1, 70)),
        "type": random.choice(types),
    },
    {
        "name": "Pycardano_test_NFT_003",
        "attack": str(random.randint(1, 70)),
        "speed": str(random.randint(1, 70)),
        "defense": str(random.randint(1, 70)),
        "health": str(random.randint(1, 70)),
        "type": random.choice(types),
    },
    {
        "name": "Pycardano_test_NFT_004",
        "attack": str(random.randint(1, 70)),
        "speed": str(random.randint(1, 70)),
        "defense": str(random.randint(1, 70)),
        "health": str(random.randint(1, 70)),
        "type": random.choice(types),
    },
    {
        "name": "Pycardano_test_NFT_005",
        "attack": str(random.randint(1, 70)),
        "speed": str(random.randint(1, 70)),
        "defense": str(random.randint(1, 70)),
        "health": str(random.randint(1, 70)),
        "type": random.choice(types),
    },
]
"""
import os
import random
import sys
from os.path import exists

from blockfrost import ApiError, ApiUrls, BlockFrostApi, BlockFrostIPFS
from dotenv import load_dotenv

from pycardano import *

# Nạp biến môi trường
load_dotenv()
network = os.getenv("BLOCKFROST_NETWORK")
wallet_mnemonic = os.getenv("MNEMONIC")
blockfrost_api_key = os.getenv("BLOCKFROST_PROJECT_ID")



# Map network (testnet → preview)
if network == "testnet":
    base_url = ApiUrls.preview.value
    cardano_network = Network.TESTNET
else:
    base_url = ApiUrls.mainnet.value
    cardano_network = Network.MAINNET


# Derive payment/staking từ mnemonic
new_wallet = crypto.bip32.HDWallet.from_mnemonic(wallet_mnemonic)
payment_key = new_wallet.derive_from_path(f"m/1852'/1815'/0'/0/0")
staking_key = new_wallet.derive_from_path(f"m/1852'/1815'/0'/2/0")
payment_skey = ExtendedSigningKey.from_hdwallet(payment_key)
staking_skey = ExtendedSigningKey.from_hdwallet(staking_key)


# Địa chỉ ví phát hành và nhận NFT
main_address = Address(
    payment_part=payment_skey.to_verification_key().hash(),
    staking_part=staking_skey.to_verification_key().hash(),
    network=cardano_network,
)


print(" ")
print(f"Derived address: {main_address}")

# Kiểm tra UTxO để đảm bảo có đủ ADA
api = BlockFrostApi(project_id=blockfrost_api_key, base_url=base_url)

try:
    utxos = api.address_utxos(main_address)
except Exception as e:
    if e.status_code == 404:
        print("Address does not have any UTXOs. ")
        if network == "testnet":
            print(
                "Request tADA from the faucet: https://docs.cardano.org/cardano-testnets/tools/faucet/"
            )
    else:
        print(e.message)
    sys.exit(1)


# Context cho build & submit
cardano = BlockFrostChainContext(project_id=blockfrost_api_key, base_url=base_url)

builder = TransactionBuilder(cardano)

# Tạo thư mục keys ở cùng cấp với tệp Python (demo; thực tế nên gom về `keys/` gốc)
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


# Tải khóa chính sách, dựng ScriptPubkey → ScriptAll → policy_id
policy_signing_key = PaymentSigningKey.load(policy_skey_path)
policy_verification_key = PaymentVerificationKey.load(policy_vkey_path)
pub_key_policy = ScriptPubkey(policy_verification_key.hash())


policy = ScriptAll([pub_key_policy])

policy_id = policy.hash()
policy_id_hex = policy_id.payload.hex()
native_scripts = [policy]
# ======================================================
# 8. GIẢI THÍCH: NFT TRÊN CARDANO LÀ GÌ?
# ======================================================
# Cardano KHÔNG có chuẩn ERC-721 riêng.
#
# NFT trên Cardano thực chất là:
# - Native Token
# - Có supply = 1
# - Có metadata theo chuẩn CIP-721
#
# FT và NFT dùng CHUNG cơ chế mint.
# Sự khác biệt chỉ nằm ở:
# - Số lượng
# - Metadata
# ======================================================

my_asset = Asset()
my_nft = MultiAsset()

# Dựng metadata CIP-721
metadata = {721: {policy_id_hex: {}}}

# ======================================================
# 11. TẠO METADATA CIP-721
# ======================================================
# Cấu trúc:
# {
#   721: {
#     policy_id: {
#       asset_name: { ...metadata }
#     }
#   }
# }

# 12. TẠO MULTIASSET ĐỂ MINT NFT
# (Mint NFT khác với FT ở chỗ: mỗi NFT có supply = 1 và metadata riêng)
# Vì vậy trong phần này mình sẽ không giải thích chi tiết cách tạo asset
# vì tương tự như phần mint token trong bài trước.
# ======================================================
# quantity = 1  → NFT
# quantity > 1  → FT

asset_minted = []

for asset in assets:
    asset_name = asset["name"]
    asset_name_bytes = asset_name.encode("utf-8")
    metadata[721][policy_id_hex][asset_name] = {
        "name": asset_name,
        "type": asset["type"],
        "attack": asset["attack"],
        "speed": asset["speed"],
        "defense": asset["defense"],
        "health": asset["health"],
    }
    nft1 = AssetName(asset_name_bytes)  # token name = tên NFT
    my_asset[nft1] = 1

# Thêm asset vào MultiAsset dưới policy_id
my_nft[policy_id] = my_asset
# Thêm native_scripts và mint vào builder
builder.native_scripts = native_scripts

# Gắn metadata vào auxiliary data (Alonzo)
auxiliary_data = AuxiliaryData(AlonzoMetadata(metadata=Metadata(metadata)))
builder.auxiliary_data = auxiliary_data

# Đặt MultiAsset với giá trị dương để mint NFTs
builder.mint = my_nft

# Min-ADA cho output chứa nhiều NFT
min_val = min_lovelace(
    cardano, output=TransactionOutput(main_address, Value(0, my_nft))
)

builder.add_output(TransactionOutput(main_address, Value(min_val, my_nft)))


# Input address để builder tự chọn UTxO
builder.add_input_address(main_address)
signed_tx = builder.build_and_sign(
    [payment_skey, policy_signing_key], change_address=main_address
)
result = cardano.submit_tx(signed_tx.to_cbor())

print(f"Number of inputs: \t {len(signed_tx.transaction_body.inputs)}")
print(f"Number of outputs: \t {len(signed_tx.transaction_body.outputs)}")
print(f"Fee: \t\t\t {signed_tx.transaction_body.fee/1000000} ADA")
print(f"Transaction submitted! ID: {result}")