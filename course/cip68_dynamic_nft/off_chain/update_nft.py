import json
from typing import Tuple
from pathlib import Path

from pycardano import (
    Address,
    Redeemer,
    TransactionOutput,
)
from pycardano.txbuilder import TransactionBuilder
from pycardano.key import ExtendedSigningKey, ExtendedVerificationKey
from pycardano.hash import VerificationKeyHash
from pycardano.crypto.bip32 import HDWallet

from off_chain.utils.context import mk_context, network
from off_chain.utils.validators import load_applied_store_validator
from off_chain.utils.datum import metadatum_from_json
from off_chain.common.config import MNEMONIC

def _mk_keys_from_mnemonic(mnemonic: str, idx: int) -> Tuple[ExtendedSigningKey, ExtendedVerificationKey, Address]:
    hd = HDWallet.from_mnemonic(mnemonic)
    payment_hd = hd.derive(1852, hardened=True).derive(1815, hardened=True).derive(0, hardened=True).derive(0).derive(idx)
    staking_hd = hd.derive(1852, hardened=True).derive(1815, hardened=True).derive(0, hardened=True).derive(2).derive(0)
    xsk = ExtendedSigningKey.from_hdwallet(payment_hd)
    staking_key = ExtendedSigningKey.from_hdwallet(staking_hd)
    xvk = xsk.to_verification_key()
    vkh = xvk.hash()
    # Địa chỉ ví chính để gom UTxO
    addr = Address(
        payment_part=xsk.to_verification_key().hash(),
        staking_part=staking_key.to_verification_key().hash(),
        network=network(),
    )
    return xsk, xvk, addr

def main():
    if not MNEMONIC:
        raise RuntimeError("Missing MNEMONIC in .env")

    issuer_xsk, issuer_xvk, issuer_addr = _mk_keys_from_mnemonic(MNEMONIC, 0)
    context = mk_context()
    store = load_applied_store_validator()

    # Lấy 1 ref UTxO ở store (UTxO có inline datum)
    store_utxos = context.utxos(store.lock_address)
    if not store_utxos:
        raise RuntimeError("No UTxOs at store address")
    ref_utxo = next((u for u in store_utxos if u.output.datum), None)
    if not ref_utxo:
        raise RuntimeError("No reference UTxO with inline datum found at store")

    # New metadata
    meta_path = Path(__file__).resolve().parent / "nft-metadata-updated.json"
    if meta_path.exists():
        updated_meta = json.loads(meta_path.read_text(encoding="utf-8"))
    else:
        updated_meta = {"name": "Updated", "description": "Updated by pycardano"}
    inline_datum = metadatum_from_json(updated_meta, version=2)

    builder = TransactionBuilder(context)
    # Thêm UTxO từ issuer để phí/collateral
    builder.add_input_address(issuer_addr)

    # Rdmr=Update (Constr 0)
    builder.add_script_input(ref_utxo, store.script, datum=ref_utxo.output.datum, redeemer=Redeemer(0))
    # Trả lại về store cùng số lượng tài sản, chỉ đổi datum
    out_ref = TransactionOutput(store.lock_address, ref_utxo.output.amount, datum=inline_datum)
    builder.add_output(out_ref)


    signed_tx = builder.build_and_sign([issuer_xsk], change_address=issuer_addr,auto_required_signers= True)
    tx_id = context.submit_tx(signed_tx.to_cbor())
    print(f"Transaction submitted! ID: {tx_id}")

if __name__ == "__main__":
    main()

