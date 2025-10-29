from typing import Tuple
from pycardano import Address, Redeemer, TransactionOutput
from pycardano.txbuilder import TransactionBuilder
from pycardano.key import ExtendedSigningKey, ExtendedVerificationKey
from pycardano.hash import VerificationKeyHash
from pycardano.crypto.bip32 import HDWallet

from off_chain.utils.context import mk_context, network
from off_chain.utils.validators import load_applied_store_validator
from off_chain.common.config import MNEMONIC

def _mk_keys_from_mnemonic(mnemonic: str, idx: int) -> Tuple[ExtendedSigningKey, ExtendedVerificationKey, Address]:
    hd = HDWallet.from_mnemonic(mnemonic)
    hd = hd.derive(1852, hardened=True).derive(1815, hardened=True).derive(0, hardened=True).derive(0).derive(idx)
    xsk = ExtendedSigningKey(hd.xprivate_key)
    xvk = ExtendedVerificationKey(xsk.to_verification_key())
    vkh = VerificationKeyHash.from_verification_key(xvk)
    addr = Address(payment_part=vkh, network=network())
    return xsk, xvk, addr

def main():
    if not MNEMONIC:
        raise RuntimeError("Missing MNEMONIC in .env")

    issuer_xsk, issuer_xvk, issuer_addr = _mk_keys_from_mnemonic(MNEMONIC, 0)
    user_xsk, user_xvk, user_addr = _mk_keys_from_mnemonic(MNEMONIC, 1)

    context = mk_context()
    store = load_applied_store_validator()

    utxos = context.utxos(store.lock_address)
    if not utxos:
        raise RuntimeError("No UTxOs at store")

    builder = TransactionBuilder(context)
    builder.add_input_address(issuer_addr)

    # Rdmr=Remove (Constr 1)
    for u in utxos:
        builder.add_script_input(u, store.script, datum=u.output.datum, redeemer=Redeemer(1))
        builder.add_output(TransactionOutput(user_addr, u.output.amount, datum=u.output.datum))



    signed_tx = builder.build_and_sign([issuer_xsk], change_address=issuer_addr, auto_required_signers=True)
    tx_id = context.submit_tx(signed_tx.to_cbor())
    print(f"Transaction submitted! ID: {tx_id}")

if __name__ == "__main__":
    main()