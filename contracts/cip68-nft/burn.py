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

# Tìm NFT UTXO (từ hàm find_nft_utxo)
utxo_tx_id, utxo_index, _ = find_nft_utxo(main_address)
nft_utxo = UTxO.from_primitive((TransactionId(utxo_tx_id), utxo_index), Value())  # Amount từ api nếu cần

# Build tx
builder = TransactionBuilder(cardano)
builder.add_input(nft_utxo)
builder.add_input_address(main_address)
mint_value = Value(assets={(policy_id, asset_name): -1})
builder.mint = mint_value
# Không add output cho NFT
builder.ttl = cardano.last_block_slot + 1000

body = builder.build(change_address=main_address)
witness_set = TransactionWitnessSet(
    mint_redeemers={policy_id: redeemer},
    plutus_scripts={policy_id: mint_script},
)
tx = Transaction(body, witness_set)
tx_body_cbor = body.to_cbor()
signature = payment_skey.sign(tx_body_cbor)
witness_set.signatures[owner_hash] = signature
tx = Transaction(body, witness_set)

tx_id = cardano.submit_tx(tx)
print(f"Burn thành công! Tx ID: {tx_id}")