from dataclasses import dataclass
import os
import sys
import json
from blockfrost import ApiUrls, BlockFrostApi
from dotenv import load_dotenv
from pycardano import (
    Network, Address, ExtendedSigningKey, BlockFrostChainContext, TransactionBuilder,
    TransactionOutput, Value, AssetName, PolicyID, PlutusData, Redeemer,
    TransactionWitnessSet, Transaction, BytesPlutusData, MapPlutusData,
    HDWallet, crypto
)
import cbor2

load_dotenv()
network = os.getenv("BLOCKFROST_NETWORK")
wallet_mnemonic = os.getenv("MNEMONIC")
blockfrost_api_key = os.getenv("BLOCKFROST_PROJECT_ID")

if network == "testnet":
    base_url = ApiUrls.preview.value
    cardano_network = Network.TESTNET
else:
    base_url = ApiUrls.mainnet.value
    cardano_network = Network.MAINNET

# Tạo wallet
new_wallet = crypto.bip32.HDWallet.from_mnemonic(wallet_mnemonic)
payment_key = new_wallet.derive_from_path("m/1852'/1815'/0'/0/0")
staking_key = new_wallet.derive_from_path("m/1852'/1815'/0'/2/0")
payment_skey = ExtendedSigningKey.from_hdwallet(payment_key)
staking_skey = ExtendedSigningKey.from_hdwallet(staking_key)
main_address = Address(
    payment_part=payment_skey.to_verification_key().hash(),
    staking_part=staking_skey.to_verification_key().hash(),
    network=cardano_network,
)
owner_hash = payment_skey.to_verification_key().hash()

api = BlockFrostApi(project_id=blockfrost_api_key, base_url=base_url)
cardano = BlockFrostChainContext(project_id=blockfrost_api_key, base_url=base_url)

# Kiểm tra balance (cần ~2 ADA)
utxos = api.address_utxos(main_address)
total_ada = sum(int(utxo.amount[0].quantity) for utxo in utxos)
if total_ada < 2_000_000:
    print("Không đủ ADA. Cần ít nhất 2 ADA.")
    sys.exit(1)

# Đọc mint script từ plutus.json
def read_mint_script() -> tuple:
    with open("plutus.json", "r") as f:
        data = json.load(f)
    validator = data["validators"][0]  # Giả sử validator đầu là dynamic_nft
    script_bytes = bytes.fromhex(validator["compiledCode"])
    script_hash = PolicyID.from_primitive(bytes.fromhex(validator["hash"]))
    return PlutusV3Script(script_bytes), script_hash

mint_script, policy_id = read_mint_script()
asset_name = AssetName(b"DynamicNFT")
print(f"Policy ID: {policy_id}")
# Tìm UTXO chứa NFT
def find_nft_utxo(address: Address) -> tuple:
    utxos_details = api.address_utxos_details(address)
    for utxo in utxos_details:
        amounts = {a.unit: a for a in utxo.amount}
        policy_asset = f"{policy_id.to_primitive_hex()}.{asset_name.name.hex()}"
        if policy_asset in amounts and int(amounts[policy_asset].quantity) == 1:
            # Lấy datum
            if utxo.datum_hash:
                datum_cbor = api.datums(utxo.datum_hash)
                # Parse để confirm (tùy chọn)
            return utxo.hash, utxo.index, utxo.amount
    raise Exception("Không tìm thấy NFT UTXO")

utxo_tx_id, utxo_index, utxo_amount = find_nft_utxo(main_address)
nft_utxo = UTxO.from_primitive((TransactionId(utxo_tx_id), utxo_index), utxo_amount)

# Metadata mới
new_metadata = {"name": "Updated Dynamic NFT", "image": "ipfs://example/new_image.png", "description": "Updated desc"}
new_datum = create_cip68_datum(policy_id.to_str_hex(), asset_hex, new_metadata)  # Từ hàm ở mint.py

# Build tx
builder = TransactionBuilder(cardano)
builder.add_input(nft_utxo)  # Input UTXO NFT
builder.add_input_address(main_address)  # Cho phí
builder.add_output(
    TransactionOutput(
        address=main_address,
        amount=Value.from_utxo(nft_utxo) - Value(1_500_000),  # Giữ NFT + ADA trừ phí
        datum=new_datum,
    )
)
builder.ttl = cardano.last_block_slot + 1000

signed_tx = builder.build_and_sign(
    signing_keys=[payment_skey],
    change_address=main_address,
)
tx_id = cardano.submit_tx(signed_tx)
print(f"Update thành công! Tx ID: {tx_id}")
print(f"Metadata mới: {new_metadata}")