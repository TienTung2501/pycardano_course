"""
Lesson 1 (Chapter 3) — Hello World (Spend/Unlock)

Mục tiêu: Tiêu UTxO đã lock ở hợp đồng HelloWorld bằng redeemer hợp lệ,
trả ADA về ví, ký bởi owner.

Các bước chính:
1) Đọc .env, dựng ví và mạng Blockfrost.
2) Đọc blueprint `plutus.json` → PlutusV3Script + ScriptHash → script address.
3) Tạo redeemer HelloWorldRedeemer(msg: bytes) (Constr 0) để unlock.
4) Xác định UTxO đã lock (theo lock_tx_id) và add_script_input(..., redeemer=...).
5) Thêm input address từ ví để bù phí, set required_signers = [owner].
6) build_and_sign và submit_tx.
"""

from dataclasses import dataclass
import os
import sys
import json
from blockfrost import ApiError, ApiUrls, BlockFrostApi
from dotenv import load_dotenv
from pycardano import *
from pycardano.hash import VerificationKeyHash, ScriptHash, TransactionId

# Nạp biến môi trường
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

# Tạo khóa từ mnemonic (payment/staking)
new_wallet = crypto.bip32.HDWallet.from_mnemonic(wallet_mnemonic)
payment_key = new_wallet.derive_from_path(f"m/1852'/1815'/0'/0/0")
staking_key = new_wallet.derive_from_path(f"m/1852'/1815'/0'/2/0")
payment_skey = ExtendedSigningKey.from_hdwallet(payment_key)
staking_skey = ExtendedSigningKey.from_hdwallet(staking_key)

# Tạo địa chỉ ví với payment/staking
main_address = Address(
    payment_part=payment_skey.to_verification_key().hash(),
    staking_part=staking_skey.to_verification_key().hash(),
    network=cardano_network,
)

print(f"Địa chỉ ví: {main_address}")

# Khởi tạo API và context
api = BlockFrostApi(project_id=blockfrost_api_key, base_url=base_url)

# Ngữ cảnh chuỗi để build/submit giao dịch
cardano = BlockFrostChainContext(project_id=blockfrost_api_key, base_url=base_url)

# Đọc validator từ plutus.json để lấy PlutusV3Script + hash
def read_validator() -> dict:
    with open("plutus.json", "r") as f:
        validator = json.load(f)
    script_bytes = PlutusV3Script(  # Sử dụng PlutusV3 như sample
        bytes.fromhex(validator["validators"][0]["compiledCode"])
    )
    script_hash = ScriptHash(bytes.fromhex(validator["validators"][0]["hash"]))
    return {
        "type": "PlutusV3",
        "script_bytes": script_bytes,
        "script_hash": script_hash,
    }

validator = read_validator()

# Script address (địa chỉ hợp đồng)
script_address = Address(
    payment_part=validator["script_hash"],
    network=cardano_network,
)

print(f"Địa chỉ hợp đồng (script): {script_address}")

# Định nghĩa Datum class (không dùng trực tiếp khi spend nhưng để minh hoạ)
@dataclass
class HelloWorldDatum(PlutusData):
    CONSTR_ID = 0
    owner: bytes

# Tạo datum (owner = hash của payment verification key)
owner_vkey = payment_skey.to_verification_key()
owner_hash = owner_vkey.hash()
datum = HelloWorldDatum(owner=owner_hash.to_primitive())

# Định nghĩa Redeemer class (Constr 0)
@dataclass
class HelloWorldRedeemer(PlutusData):
    CONSTR_ID = 0
    msg: bytes

# Tạo redeemer (msg = b"Hello, World!") và bọc trong Redeemer
message = b"Hello, World!"
redeemer_data = HelloWorldRedeemer(msg=message)
redeemer = Redeemer(data=redeemer_data)  # Wrapper Redeemer như sample

# Tìm UTxO đã lock theo tx_id chuỗi
def get_utxo_from_str(context, tx_id: str, contract_address: Address) -> UTxO:
    for utxo in context.utxos(str(contract_address)):
        if str(utxo.input.transaction_id) == tx_id:
            return utxo
    raise Exception(f"UTxO not found for transaction {tx_id}")

# Xây và gửi giao dịch tiêu script input (unlock)
def unlock(
    utxo: UTxO,
    from_script: PlutusV3Script,
    redeemer: Redeemer,
    signing_key: PaymentSigningKey,
    owner: VerificationKeyHash,
    context: BlockFrostChainContext,
) -> TransactionId:
    # Build transaction
    builder = TransactionBuilder(context=context)
    builder.add_script_input(
        utxo=utxo,
        script=from_script,
        redeemer=redeemer,
    )
    builder.add_input_address(main_address)  # Thêm input từ ví nếu cần (cho phí/change)
    builder.add_output(
        TransactionOutput(
            address=main_address,
            amount=utxo.output.amount.coin,  # Gửi lại ADA từ UTxO
        )
    )
    builder.required_signers = [owner]  # Yêu cầu chữ ký của owner (theo logic on-chain)
    signed_tx = builder.build_and_sign(
        signing_keys=[signing_key],
        change_address=main_address,
    )

    # Submit transaction
    context.submit_tx(signed_tx)
    return signed_tx.id

# TODO: Lấy lock_tx_id từ tham số dòng lệnh hoặc input runtime
lock_tx_id = "0dcb00409748c13e5d5eee4061a1eed82b1b0a90abc519f9497d6d6bcbad5e77" # Thay bằng tx_id thực tế

# Get UTxO to spend
utxo = get_utxo_from_str(cardano, lock_tx_id, script_address)

# Execute transaction
tx_hash = unlock(
    utxo=utxo,
    from_script=validator["script_bytes"],
    redeemer=redeemer,
    signing_key=payment_skey,
    owner=payment_skey.to_verification_key().hash(),  # Owner hash
    context=cardano,
)

print(
    f"2 tADA unlocked from the contract\n\tTx ID: {tx_hash}\n\tRedeemer: {redeemer.to_cbor_hex()}"
)