from __future__ import annotations
import json
from typing import Any, Dict, List, Tuple

from pathlib import Path

# Wire repo root
import sys
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from pycardano import (
    Address,
    Asset,
    AssetName,
    MultiAsset,
    Redeemer,
    ScriptHash,
    Transaction,
    TransactionWitnessSet,
    TransactionOutput,
    Value,
    min_lovelace,
)
from pycardano.hash import VerificationKeyHash
from pycardano.key import ExtendedSigningKey, ExtendedVerificationKey
from pycardano.crypto.bip32 import HDWallet

from course.cip68_dynamic_nft.off_chain.utils.context import mk_context, network
from course.cip68_dynamic_nft.off_chain.utils.validators import (
    load_applied_mint_policy,
    load_applied_store_validator,
)
from course.cip68_dynamic_nft.off_chain.utils.assets import (
    derive_suffix_28_from_input,
    ensure_index_lt_256,
)
from course.cip68_dynamic_nft.off_chain.utils.labels import build_token_name
from course.cip68_dynamic_nft.off_chain.utils.datum import metadatum_from_json
from course.cip68_dynamic_nft.off_chain.common.config import (
    REFERENCE_TOKEN_LABEL,
    NON_FUNGIBLE_TOKEN_LABEL,
    MNEMONIC,
)
from pycardano.txbuilder import TransactionBuilder


# Derive keys and address from mnemonic and account index

def _mk_keys_from_mnemonic(mnemonic: str, idx: int) -> Tuple[ExtendedSigningKey, ExtendedVerificationKey, Address]:
    hd = HDWallet.from_mnemonic(mnemonic)
    hd = (
        hd.derive(1852, hardened=True)
        .derive(1815, hardened=True)
        .derive(0, hardened=True)
        .derive(0)
        .derive(idx)
    )
    xsk = ExtendedSigningKey(hd.xprivate_key)
    xvk = ExtendedVerificationKey(xsk.to_verification_key())
    vkh = VerificationKeyHash.from_verification_key(xvk)
    addr = Address(payment_part=vkh, network=network())
    return xsk, xvk, addr


def get_addresses() -> Tuple[str, str]:
    if not MNEMONIC:
        raise RuntimeError("Missing MNEMONIC in .env")
    issuer_xsk, issuer_xvk, issuer_addr = _mk_keys_from_mnemonic(MNEMONIC, 0)
    user_xsk, user_xvk, user_addr = _mk_keys_from_mnemonic(MNEMONIC, 1)
    return issuer_addr.encode(), user_addr.encode()


def get_store_summary() -> Dict[str, Any]:
    context = mk_context()
    store = load_applied_store_validator()
    utxos = context.utxos(store.lock_address)
    return {
        "store_address": store.lock_address.encode(),
        "utxo_count": len(utxos),
    }


def mint_dynamic_nft(
    metadata: Dict[str, Any], issuer_index: int = 0, user_index: int = 1
) -> Tuple[str, Dict[str, str]]:
    if not MNEMONIC:
        raise RuntimeError("Missing MNEMONIC in .env")

    issuer_xsk, issuer_xvk, _ = _mk_keys_from_mnemonic(MNEMONIC, issuer_index)
    user_xsk, user_xvk, user_addr = _mk_keys_from_mnemonic(MNEMONIC, user_index)

    context = mk_context()
    mint = load_applied_mint_policy()
    store = load_applied_store_validator()

    utxos = context.utxos(user_addr)
    if not utxos:
        raise RuntimeError(
            "Address does not have any UTXOs. Get test ADA from the faucet if on testnet."
        )
    base_utxo = utxos[0]
    if not ensure_index_lt_256(base_utxo):
        raise RuntimeError("Selected UTxO index must be < 256")

    suffix = derive_suffix_28_from_input(base_utxo)
    tn_ref = build_token_name(REFERENCE_TOKEN_LABEL, suffix)
    tn_user = build_token_name(NON_FUNGIBLE_TOKEN_LABEL, suffix)

    policy_id: ScriptHash = mint.policy_id
    an_ref = AssetName(tn_ref)
    an_user = AssetName(tn_user)

    meta_json = metadata or {"name": "CIP-68 NFT", "description": "Minted by API", "version": 1}
    inline_datum = metadatum_from_json(meta_json, version=1)

    ma = MultiAsset()
    ma[policy_id] = Asset()
    ma[policy_id][an_ref] = 1
    ma[policy_id][an_user] = 1

    builder = TransactionBuilder(context)
    builder.mint = ma
    builder.add_minting_script(mint.script, Redeemer(0))

    out_user = TransactionOutput(
        user_addr, Value(0, MultiAsset({policy_id: Asset({an_user: 1})}))
    )
    min_user = min_lovelace(context, out_user)
    out_user.amount.coin = min_user
    builder.add_output(out_user)

    out_ref = TransactionOutput(
        store.lock_address, Value(0, MultiAsset({policy_id: Asset({an_ref: 1})})), datum=inline_datum
    )
    min_ref = min_lovelace(context, out_ref)
    out_ref.amount.coin = min_ref
    builder.add_output(out_ref)

    builder.add_input_address(user_addr)

    signed_tx = builder.build_and_sign(
        [user_xsk, issuer_xsk], change_address=user_addr, auto_required_signers=True
    )
    tx_id = mk_context().submit_tx(signed_tx.to_cbor())

    return tx_id, {
        "reference_token": an_ref.hex(),
        "user_token": an_user.hex(),
        "policy_id": policy_id.payload.hex(),
    }


def update_dynamic_nft(metadata: Dict[str, Any], issuer_index: int = 0) -> str:
    if not MNEMONIC:
        raise RuntimeError("Missing MNEMONIC in .env")

    issuer_xsk, issuer_xvk, issuer_addr = _mk_keys_from_mnemonic(MNEMONIC, issuer_index)
    context = mk_context()
    store = load_applied_store_validator()

    store_utxos = context.utxos(store.lock_address)
    if not store_utxos:
        raise RuntimeError("No UTxOs at store address")
    ref_utxo = next((u for u in store_utxos if u.output.datum), None)
    if not ref_utxo:
        raise RuntimeError("No reference UTxO with inline datum found at store")

    updated_meta = metadata or {"name": "Updated", "description": "Updated by API"}
    inline_datum = metadatum_from_json(updated_meta, version=2)

    builder = TransactionBuilder(context)
    builder.add_input_address(issuer_addr)
    builder.add_script_input(ref_utxo, store.script, datum=ref_utxo.output.datum, redeemer=Redeemer(0))

    out_ref = TransactionOutput(store.lock_address, ref_utxo.output.amount, datum=inline_datum)
    builder.add_output(out_ref)

    signed_tx = builder.build_and_sign([issuer_xsk], change_address=issuer_addr, auto_required_signers=True)
    tx_id = context.submit_tx(signed_tx.to_cbor())
    return tx_id


def remove_dynamic_nft(issuer_index: int = 0, user_index: int = 1) -> Tuple[str, int]:
    if not MNEMONIC:
        raise RuntimeError("Missing MNEMONIC in .env")

    issuer_xsk, issuer_xvk, issuer_addr = _mk_keys_from_mnemonic(MNEMONIC, issuer_index)
    _, _, user_addr = _mk_keys_from_mnemonic(MNEMONIC, user_index)

    context = mk_context()
    store = load_applied_store_validator()

    utxos = context.utxos(store.lock_address)
    if not utxos:
        raise RuntimeError("No UTxOs at store")

    builder = TransactionBuilder(context)
    builder.add_input_address(issuer_addr)

    consumed = 0
    for u in utxos:
        builder.add_script_input(u, store.script, datum=u.output.datum, redeemer=Redeemer(1))
        builder.add_output(TransactionOutput(user_addr, u.output.amount, datum=u.output.datum))
        consumed += 1

    signed_tx = builder.build_and_sign([issuer_xsk], change_address=issuer_addr, auto_required_signers=True)
    tx_id = context.submit_tx(signed_tx.to_cbor())
    return tx_id, consumed


def burn_dynamic_nft(issuer_index: int = 0, user_index: int = 1) -> str:
    if not MNEMONIC:
        raise RuntimeError("Missing MNEMONIC in .env")

    user_xsk, user_xvk, user_addr = _mk_keys_from_mnemonic(MNEMONIC, user_index)
    issuer_xsk, issuer_xvk, _ = _mk_keys_from_mnemonic(MNEMONIC, issuer_index)

    context = mk_context()
    mint = load_applied_mint_policy()
    store = load_applied_store_validator()

    utxos = context.utxos(user_addr)
    found_suffix = None
    for u in utxos:
        ma = u.output.amount.multi_asset
        if mint.policy_id in ma:
            for n in list(ma[mint.policy_id].keys()):
                raw = bytes(n)
                if len(raw) == 32 and raw[:4] in (
                    REFERENCE_TOKEN_LABEL.to_bytes(4, "big"),
                    NON_FUNGIBLE_TOKEN_LABEL.to_bytes(4, "big"),
                ):
                    found_suffix = raw[4:]
                    break
        if found_suffix:
            break
    if not found_suffix:
        raise RuntimeError("No CIP-68 pair found under policy at user")

    an_ref = AssetName(build_token_name(REFERENCE_TOKEN_LABEL, found_suffix))
    an_user = AssetName(build_token_name(NON_FUNGIBLE_TOKEN_LABEL, found_suffix))

    # Find the store UTxO that holds the matching reference token to keep value conservation when burning
    store_utxos = context.utxos(store.lock_address)
    ref_utxo = None
    for s in store_utxos:
        ma = s.output.amount.multi_asset
        if mint.policy_id in ma and an_ref in ma[mint.policy_id]:
            ref_utxo = s
            break
    if ref_utxo is None:
        raise RuntimeError("No matching reference token at store for this suffix; cannot burn")

    ma = MultiAsset()
    ma[mint.policy_id] = Asset()
    ma[mint.policy_id][an_ref] = -1
    ma[mint.policy_id][an_user] = -1

    builder = TransactionBuilder(context)
    builder.add_input_address(user_addr)
    # Spend the store UTxO via validator (Remove)
    builder.add_script_input(ref_utxo, store.script, datum=ref_utxo.output.datum, redeemer=Redeemer(1))
    builder.mint = ma
    builder.add_minting_script(mint.script, Redeemer(1))

    signed_tx = builder.build_and_sign([user_xsk, issuer_xsk], change_address=user_addr, auto_required_signers=True)
    tx_id = context.submit_tx(signed_tx.to_cbor())
    return tx_id


# ---------- Wallet-driven flow (build/finalize) ----------

def _addr_from_bech32(addr: str) -> Address:
    return Address.from_primitive(addr)


def list_cip68_nfts(user_bech32: str) -> Dict[str, Any]:
    """List CIP-68 NFTs for a user address under current mint policy, including store datum."""
    context = mk_context()
    user_addr = _addr_from_bech32(user_bech32)
    mint = load_applied_mint_policy()
    store = load_applied_store_validator()

    # Map suffix -> presence of user token and reference datum
    result: List[Dict[str, Any]] = []

    # Scan user UTxOs for user tokens (label 222)
    user_utxos = context.utxos(user_addr)
    suffixes = set()
    for u in user_utxos:
        ma = u.output.amount.multi_asset
        if mint.policy_id in ma:
            for n in ma[mint.policy_id].keys():
                raw = bytes(n)
                if len(raw) == 32 and raw[:4] == NON_FUNGIBLE_TOKEN_LABEL.to_bytes(4, "big"):
                    suffixes.add(raw[4:])

    # For each suffix, check store for corresponding reference token (label 100) and read datum
    store_utxos = context.utxos(store.lock_address)
    for suffix in suffixes:
        ref_name = AssetName(build_token_name(REFERENCE_TOKEN_LABEL, suffix))
        datum_json = None
        ref_utxo_ref = None
        user_utxo_ref = None
        # find a user utxo holding the user token for this suffix
        for u in user_utxos:
            ma = u.output.amount.multi_asset
            if mint.policy_id in ma and AssetName(build_token_name(NON_FUNGIBLE_TOKEN_LABEL, suffix)) in ma[mint.policy_id]:
                user_utxo_ref = {"tx_hash": str(u.input.transaction_id), "index": u.input.index}
                break
        for s in store_utxos:
            ma = s.output.amount.multi_asset
            if mint.policy_id in ma and ref_name in ma[mint.policy_id]:
                ref_utxo_ref = {
                    "tx_hash": str(s.input.transaction_id),
                    "index": s.input.index,
                }
                if s.output.datum is not None:
                    # Try to export datum as JSON-like via to_cbor_hex as fallback
                    try:
                        # If datum builder exposes original fields, convert here (course datum is metadata-like)
                        datum_json = {"cbor": s.output.datum.to_cbor_hex()}
                    except Exception:
                        datum_json = {"cbor": s.output.datum.to_cbor_hex()}
                break
        result.append(
            {
                "policy_id": mint.policy_id.payload.hex(),
                "suffix_hex": suffix.hex(),
                "user_token_hex": AssetName(build_token_name(NON_FUNGIBLE_TOKEN_LABEL, suffix)).hex(),
                "reference_token_hex": ref_name.hex(),
                "user_utxo": user_utxo_ref,
                "store_utxo": ref_utxo_ref,
                "datum": datum_json,
            }
        )

    return {"address": user_bech32, "items": result}


def build_mint_tx(user_bech32: str, metadata: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """Build unsigned transaction (with scripts/redeemers included, no vkey witnesses) for CIP-68 mint.
    Returns tx_cbor and details (policy_id, token names).
    """
    context = mk_context()
    user_addr = _addr_from_bech32(user_bech32)
    mint = load_applied_mint_policy()
    store = load_applied_store_validator()

    utxos = context.utxos(user_addr)
    if not utxos:
        raise RuntimeError("Address does not have any UTXOs. Faucet some tADA if on testnet.")
    base_utxo = utxos[0]
    if not ensure_index_lt_256(base_utxo):
        raise RuntimeError("Selected UTxO index must be < 256")

    suffix = derive_suffix_28_from_input(base_utxo)
    tn_ref = build_token_name(REFERENCE_TOKEN_LABEL, suffix)
    tn_user = build_token_name(NON_FUNGIBLE_TOKEN_LABEL, suffix)

    policy_id: ScriptHash = mint.policy_id
    an_ref = AssetName(tn_ref)
    an_user = AssetName(tn_user)

    meta_json = metadata or {"name": "CIP-68 NFT", "description": "Minted by API", "version": 1}
    inline_datum = metadatum_from_json(meta_json, version=1)

    ma = MultiAsset()
    ma[policy_id] = Asset()
    ma[policy_id][an_ref] = 1
    ma[policy_id][an_user] = 1

    builder = TransactionBuilder(context)
    builder.mint = ma
    builder.add_minting_script(mint.script, Redeemer(0))

    out_user = TransactionOutput(user_addr, Value(0, MultiAsset({policy_id: Asset({an_user: 1})})))
    out_user.amount.coin = min_lovelace(context, out_user)
    builder.add_output(out_user)

    out_ref = TransactionOutput(store.lock_address, Value(0, MultiAsset({policy_id: Asset({an_ref: 1})})), datum=inline_datum)
    out_ref.amount.coin = min_lovelace(context, out_ref)
    builder.add_output(out_ref)

    # Ensure we include at least one user UTxO so the wallet must sign
    builder.add_input_address(user_addr)

    # Build body (no signatures) and witness set (scripts/redeemers) for signing on client
    body = builder.build(change_address=user_addr)
    witness = builder.build_witness_set()
    tx = Transaction(body, witness)
    tx_cbor = tx.to_cbor()
    details = {
        "policy_id": policy_id.payload.hex(),
        "reference_token": an_ref.hex(),
        "user_token": an_user.hex(),
    }
    return tx_cbor, details


def build_burn_tx(user_bech32: str) -> Tuple[str, Dict[str, Any]]:
    """Build unsigned transaction (with scripts/redeemers) to burn CIP-68 pair under current policy."""
    context = mk_context()
    user_addr = _addr_from_bech32(user_bech32)
    mint = load_applied_mint_policy()
    store = load_applied_store_validator()

    utxos = context.utxos(user_addr)
    found_suffix = None
    for u in utxos:
        ma = u.output.amount.multi_asset
        if mint.policy_id in ma:
            for n in list(ma[mint.policy_id].keys()):
                raw = bytes(n)
                if len(raw) == 32 and raw[:4] in (
                    REFERENCE_TOKEN_LABEL.to_bytes(4, "big"),
                    NON_FUNGIBLE_TOKEN_LABEL.to_bytes(4, "big"),
                ):
                    found_suffix = raw[4:]
                    break
        if found_suffix:
            break
    if not found_suffix:
        raise RuntimeError("No CIP-68 pair found under policy at user")

    an_ref = AssetName(build_token_name(REFERENCE_TOKEN_LABEL, found_suffix))
    an_user = AssetName(build_token_name(NON_FUNGIBLE_TOKEN_LABEL, found_suffix))

    # Include the store UTxO with the ref token as a script input to satisfy value conservation
    store_utxos = context.utxos(store.lock_address)
    ref_utxo = None
    for s in store_utxos:
        ma = s.output.amount.multi_asset
        if mint.policy_id in ma and an_ref in ma[mint.policy_id]:
            ref_utxo = s
            break
    if ref_utxo is None:
        raise RuntimeError("No matching reference token at store for this suffix; cannot burn")

    ma = MultiAsset()
    ma[mint.policy_id] = Asset()
    ma[mint.policy_id][an_ref] = -1
    ma[mint.policy_id][an_user] = -1

    builder = TransactionBuilder(context)
    builder.add_input_address(user_addr)
    builder.add_script_input(ref_utxo, store.script, datum=ref_utxo.output.datum, redeemer=Redeemer(1))
    builder.mint = ma
    builder.add_minting_script(mint.script, Redeemer(1))

    body = builder.build(change_address=user_addr)
    witness = builder.build_witness_set()
    tx = Transaction(body, witness)
    tx_cbor = tx.to_cbor()
    details = {
        "policy_id": mint.policy_id.payload.hex(),
        "reference_token": an_ref.hex(),
        "user_token": an_user.hex(),
    }
    return tx_cbor, details


def finalize_with_user_witness(tx_cbor: str, user_witness_cbor: str, issuer_index: int = 0) -> str:
    """Merge user witness with issuer signature and submit the transaction."""
    if not MNEMONIC:
        raise RuntimeError("Missing MNEMONIC in .env (issuer credentials)")

    # Parse unsigned tx (with scripts+redeemers) and user's witness
    tx = Transaction.from_cbor(tx_cbor)
    body = tx.transaction_body
    witness = tx.transaction_witness_set or TransactionWitnessSet()

    user_witness = TransactionWitnessSet.from_cbor(user_witness_cbor)
    # Merge user's vkey witnesses
    if user_witness.v_key_witnesses:
        if witness.v_key_witnesses is None:
            witness.v_key_witnesses = user_witness.v_key_witnesses
        else:
            witness.v_key_witnesses.update(user_witness.v_key_witnesses)

    # Sign as issuer and append
    issuer_xsk, _, _ = _mk_keys_from_mnemonic(MNEMONIC, issuer_index)
    issuer_vw = issuer_xsk.sign(body.hash())
    if witness.v_key_witnesses is None:
        from pycardano import VKeyWitnesses
        witness.v_key_witnesses = VKeyWitnesses()
    witness.v_key_witnesses.add(issuer_vw)

    full_tx = Transaction(body, witness)
    tx_id = mk_context().submit_tx(full_tx.to_cbor())
    return tx_id
