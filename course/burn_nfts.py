import os
import random
import sys
from os.path import exists

from blockfrost import ApiError, ApiUrls, BlockFrostApi, BlockFrostIPFS
from dotenv import load_dotenv

from pycardano import *

load_dotenv()
network = os.getenv("BLOCKFROST_NETWORK")
wallet_mnemonic = os.getenv("MNEMONIC")
blockfrost_api_key = os.getenv("BLOCKFROST_PROJECT_ID")


types = ["lion", "elephant", "panda", "sloth", "tiger", "wolf"]

assets = [
    {
        "name": "Pycardano_test_NFT_001",
    },
    {
        "name": "Pycardano_test_NFT_002",
    },
    {
        "name": "Pycardano_test_NFT_003",
    },
    {
        "name": "Pycardano_test_NFT_004",
    },
    {
        "name": "Pycardano_test_NFT_005",
    },
]


if network == "testnet":
    base_url = ApiUrls.preview.value
    cardano_network = Network.TESTNET
else:
    base_url = ApiUrls.mainnet.value
    cardano_network = Network.MAINNET


new_wallet = crypto.bip32.HDWallet.from_mnemonic(wallet_mnemonic)
payment_key = new_wallet.derive_from_path(f"m/1852'/1815'/0'/0/0")
staking_key = new_wallet.derive_from_path(f"m/1852'/1815'/0'/2/0")
payment_skey = ExtendedSigningKey.from_hdwallet(payment_key)
staking_skey = ExtendedSigningKey.from_hdwallet(staking_key)


main_address = Address(
    payment_part=payment_skey.to_verification_key().hash(),
    staking_part=staking_skey.to_verification_key().hash(),
    network=cardano_network,
)


print(" ")
print(f"Derived address: {main_address}")

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


cardano = BlockFrostChainContext(project_id=blockfrost_api_key, base_url=base_url)

builder = TransactionBuilder(cardano)

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

my_asset = Asset()
my_nft = MultiAsset()


asset_burned = []

for asset in assets:
    asset_name = asset["name"]
    asset_name_bytes = asset_name.encode("utf-8")
    nft1 = AssetName(asset_name_bytes)
    my_asset[nft1] = -1  # Giá trị âm để burn NFT
    asset_burned.append(asset_name)

my_nft[policy_id] = my_asset
builder.native_scripts = native_scripts
builder.mint = my_nft


builder.add_input_address(main_address)
signed_tx = builder.build_and_sign(
    [payment_skey, policy_signing_key], change_address=main_address
)
result = cardano.submit_tx(signed_tx.to_cbor())

print(f"Number of inputs: \t {len(signed_tx.transaction_body.inputs)}")
print(f"Number of outputs: \t {len(signed_tx.transaction_body.outputs)}")
print(f"Fee: \t\t\t {signed_tx.transaction_body.fee/1000000} ADA")
print(f"Transaction submitted! ID: {result}")