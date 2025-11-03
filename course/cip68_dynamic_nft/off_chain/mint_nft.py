import json
from pathlib import Path
from typing import Tuple

from pycardano import (
    Address,
    Asset,
    AssetName,
    MultiAsset,
    Redeemer,
    ScriptHash,
    TransactionOutput,
    Value,
    min_lovelace,
)
from pycardano.key import ExtendedSigningKey, ExtendedVerificationKey
from pycardano.txbuilder import TransactionBuilder
from pycardano.crypto.bip32 import HDWallet

from off_chain.utils.context import mk_context, network
from off_chain.utils.validators import load_applied_mint_policy, load_applied_store_validator
from off_chain.utils.assets import derive_suffix_28_from_input, ensure_index_lt_256
from off_chain.utils.labels import build_token_name
from off_chain.utils.datum import metadatum_from_json
from off_chain.common.config import (
    REFERENCE_TOKEN_LABEL,
    NON_FUNGIBLE_TOKEN_LABEL,
    MNEMONIC,
)


def _mk_keys_from_mnemonic(mnemonic: str, idx: int) -> Tuple[ExtendedSigningKey, ExtendedVerificationKey, Address]:
    """Derive issuer/user keys and address from mnemonic."""
    hd = HDWallet.from_mnemonic(mnemonic)
    # Payment key
    payment_hd = hd.derive(1852, hardened=True).derive(1815, hardened=True).derive(0, hardened=True).derive(0).derive(idx)
    xsk = ExtendedSigningKey.from_hdwallet(payment_hd)
    xvk = xsk.to_verification_key()
    # Staking key
    staking_hd = hd.derive(1852, hardened=True).derive(1815, hardened=True).derive(0, hardened=True).derive(2).derive(0)
    staking_key = ExtendedSigningKey.from_hdwallet(staking_hd)
    addr = Address(
        payment_part=xvk.hash(),
        staking_part=staking_key.to_verification_key().hash(),
        network=network(),
    )
    return xsk, xvk, addr


def main():
    if not MNEMONIC:
        raise RuntimeError("Missing MNEMONIC in .env")

    # issuer = index 0, user = index 1
    issuer_xsk, issuer_xvk, _ = _mk_keys_from_mnemonic(MNEMONIC, 0)
    user_xsk, user_xvk, user_addr = _mk_keys_from_mnemonic(MNEMONIC, 1)

    context = mk_context()
    mint = load_applied_mint_policy()
    store = load_applied_store_validator()

    # Chọn 1 UTxO của user làm entropy cho token name
    utxos = context.utxos(user_addr)
    if not utxos:
        raise RuntimeError("User address has no UTxO")
    base_utxo = utxos[0]
    if not ensure_index_lt_256(base_utxo):
        raise RuntimeError("Selected UTxO index must be < 256")

    # Derive unique asset name suffix
    suffix = derive_suffix_28_from_input(base_utxo)
    tn_ref = build_token_name(REFERENCE_TOKEN_LABEL, suffix)
    tn_user = build_token_name(NON_FUNGIBLE_TOKEN_LABEL, suffix)

    policy_id: ScriptHash = mint.policy_id
    an_ref = AssetName(tn_ref)
    an_user = AssetName(tn_user)

    print(f"Minting CIP-68 NFT pair with suffix: {policy_id.payload.hex()}")

    # Inline datum cho ref NFT
    meta_path = Path(__file__).resolve().parent / "nft-metadata.json"
    if meta_path.exists():
        meta_json = json.loads(meta_path.read_text(encoding="utf-8"))
    else:
        meta_json = {"name": "CIP-68 NFT", "description": "Minted by pycardano", "version": 1}
    inline_datum = metadatum_from_json(meta_json, version=1)

    # MultiAsset mint
    ma = MultiAsset()
    ma[policy_id] = Asset({an_ref: 1, an_user: 1})

    builder = TransactionBuilder(context)
    builder.mint = ma
    builder.add_minting_script(mint.script, Redeemer(0))  # Constr 0: mint both

    # Output user NFT

    out_user = TransactionOutput(
        user_addr,
        Value(0, MultiAsset({policy_id: Asset({an_user: 1})}))
    )

    out_user.amount.coin = min_lovelace(context, out_user)
    builder.add_output(out_user)

    # Output ref NFT with inline datum
    out_ref = TransactionOutput(
        store.lock_address,
        Value(0, MultiAsset({policy_id: Asset({an_ref: 1})})),
        datum=inline_datum
    )

    out_ref.amount.coin = min_lovelace(context, out_ref)
    builder.add_output(out_ref)

    # Add input UTxO for fee/collateral
    builder.add_input_address(user_addr)

    # Build & sign transaction (both issuer and user)
    signed_tx = builder.build_and_sign(
        [user_xsk, issuer_xsk],
        change_address=user_addr,
        auto_required_signers=True
    )

    tx_id = context.submit_tx(signed_tx.to_cbor())
    print(f"Transaction submitted! ID: {tx_id}")


if __name__ == "__main__":
    main()
