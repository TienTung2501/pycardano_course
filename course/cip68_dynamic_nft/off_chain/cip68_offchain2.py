#!/usr/bin/env python3
"""
cip68_offchain.py

CIP-68 off-chain utility: mint / burn / update / remove.

Usage:
  python -m off_chain.cip68_offchain mint
  python -m off_chain.cip68_offchain burn
  python -m off_chain.cip68_offchain update
  python -m off_chain.cip68_offchain remove

This script expects you have:
- off_chain.utils.validators.load_applied_mint_policy
- off_chain.utils.validators.load_applied_store_validator
- off_chain.utils.datum.metadatum_from_json
- off_chain.common.config.MNEMONIC, REFERENCE_TOKEN_LABEL, NON_FUNGIBLE_TOKEN_LABEL
- pycardano set up and network configured in your utils/context.mk_context()
"""
import sys
import json
import traceback
import hashlib
from pathlib import Path
from typing import Tuple, Optional

from pycardano import (
    Address,
    Asset,
    AssetName,
    MultiAsset,
    Redeemer,
    TransactionOutput,
    Value,
    min_lovelace,
    RawCBOR,
    PlutusData,
)
from pycardano.exception import TransactionFailedException
from pycardano.key import ExtendedSigningKey, ExtendedVerificationKey
from pycardano.txbuilder import TransactionBuilder
from pycardano.crypto.bip32 import HDWallet

# Use ConstrPlutusData if available for redeemers
try:
    from pycardano.plutus import ConstrPlutusData
except Exception:
    ConstrPlutusData = None  # fallback handled later

# Project utilities (must exist in your repo)
from off_chain.utils.context import mk_context, network
from off_chain.utils.validators import load_applied_mint_policy, load_applied_store_validator
from off_chain.utils.datum import metadatum_from_json
from off_chain.common.config import (
    REFERENCE_TOKEN_LABEL,
    NON_FUNGIBLE_TOKEN_LABEL,
    MNEMONIC,
)

# -----------------------
# Local helpers (robust)
# -----------------------

def safe_run(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except TransactionFailedException as e:
        print("\n❌ TransactionFailedException (evaluation failed):")
        print(e)
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print("\n❌ Exception:")
        print(type(e).__name__, str(e))
        traceback.print_exc()
        sys.exit(1)

def _mk_keys_from_mnemonic(mnemonic: str, idx: int) -> Tuple[ExtendedSigningKey, ExtendedVerificationKey, Address]:
    """
    Derive payment and staking keys from mnemonic using CIP1852 path.
    Return (xsk, xvk, address).
    """
    hd = HDWallet.from_mnemonic(mnemonic)
    payment_hd = hd.derive(1852, hardened=True).derive(1815, hardened=True).derive(0, hardened=True).derive(0).derive(idx)
    staking_hd = hd.derive(1852, hardened=True).derive(1815, hardened=True).derive(0, hardened=True).derive(2).derive(0)
    xsk = ExtendedSigningKey.from_hdwallet(payment_hd)
    staking_key = ExtendedSigningKey.from_hdwallet(staking_hd)
    xvk = xsk.to_verification_key()
    addr = Address(
        payment_part=xvk.hash(),
        staking_part=staking_key.to_verification_key().hash(),
        network=network(),
    )
    return xsk, xvk, addr

def _debug_tx_builder(builder: TransactionBuilder):
    print("\n==== TransactionBuilder state (debug) ====")
    try:
        import pprint
        pprint.pprint(builder.__dict__)
    except Exception:
        print("(unable to pretty print builder state)")
    print("=========================================\n")

# Utility: derive suffix 28 bytes from a UTxO returned by context.utxos(address)
# The UTxO objects from pycardano have `.input.transaction_id` and `.input.index`
def derive_suffix_28_from_utxo(utxo) -> bytes:
    """
    Derive 28-byte suffix from UTxO (CIP-68): blake2b(txid || idx) (digest_size=28)
    Accepts a pycardano UTxO object (has .input.transaction_id.payload and .input.index).
    """
    try:
        txid_bytes = utxo.input.transaction_id.payload
        idx = utxo.input.index
    except Exception as e:
        raise RuntimeError("derive_suffix_28_from_utxo: unexpected utxo structure") from e
    if not isinstance(idx, int):
        raise RuntimeError("derive_suffix_28_from_utxo: utxo index not int")
    idx_bytes = idx.to_bytes(2, "big")
    return hashlib.blake2b(txid_bytes + idx_bytes, digest_size=28).digest()

def ensure_index_lt_256_utxo(utxo) -> bool:
    try:
        idx = utxo.input.index
    except Exception:
        raise RuntimeError("ensure_index_lt_256_utxo: unexpected utxo structure")
    return int(idx) < 256

# Build token name bytes: 4-byte label big-endian + 28-byte suffix -> bytes
def build_token_name_bytes(label_int: int, suffix28: bytes) -> bytes:
    if not (0 <= label_int < 2**32):
        raise ValueError("label_int must fit 4 bytes")
    label_bytes = label_int.to_bytes(4, "big")
    if len(suffix28) != 28:
        raise ValueError("suffix must be 28 bytes")
    return label_bytes + suffix28

# Helper to create Redeemer for option(Some(Constructor)) per your Aiken types.
# Aiken used Option<...>, so the redeemer shape must be Some(MintAction.Mint) etc.
# We use ConstrPlutusData if available; otherwise fall back to simple PlutusData subclass.
def make_mint_redeemer(is_mint: bool):
    """
    Returns a pycardano.Redeemer representing Option(MintAction).
    Some(Mint) => Constr(0, [Constr(0, [])])
    Some(Burn) => Constr(0, [Constr(1, [])])
    None => Constr(1, [])
    """
    if ConstrPlutusData is None:
        # Best-effort fallback: build raw CBOR for Constr tags using cbor2 via a PlutusData wrapper.
        # Many pycardano versions have ConstrPlutusData, so this path should be rare.
        raise RuntimeError("ConstrPlutusData not available in pycardano in this environment. Install pycardano with Plutus support.")
    # Outer Option::Some -> constructor index 0, with one field (the inner MintAction)
    inner_idx = 0 if is_mint else 1  # 0 -> Mint, 1 -> Burn
    inner = ConstrPlutusData(inner_idx, [])     # MintAction.<idx>
    some = ConstrPlutusData(0, [inner])         # Option::Some
    return Redeemer(some)

def make_store_redeemer(is_update: bool):
    """
    Option(StoreAction): Some(Update) -> Constr(0, [Constr(0, [])])
                         Some(Remove) -> Constr(0, [Constr(1, [])])
    """
    if ConstrPlutusData is None:
        raise RuntimeError("ConstrPlutusData not available.")
    inner_idx = 0 if is_update else 1
    inner = ConstrPlutusData(inner_idx, [])
    some = ConstrPlutusData(0, [inner])
    return Redeemer(some)

# Simulate / submit with clear printing
def _simulate_or_submit(context, tx, submit: bool):
    try:
        print("Simulating transaction (evaluate)...")
        eval_res = context.evaluate_tx_cbor(tx.to_cbor())
        print("Simulation result:", eval_res)
    except TransactionFailedException as e:
        print("\n❌ Simulation/Evaluation failed. Blockfrost/Ogmios response:")
        print(e)
        # Show a helpful hint
        print("Hint: check that the applied validators are compiled with the correct parameters (issuer, store).")
        raise

    if submit:
        print("Submitting tx...")
        tx_id = context.submit_tx(tx.to_cbor())
        print("Submitted tx id:", tx_id)
        return tx_id
    return None

# -----------------------
# Actions
# -----------------------

def action_mint(debug: bool = False, submit: bool = True):
    """Mint pair: ref(label=100) -> store (inline datum), user(label=222) -> user address"""
    if not MNEMONIC:
        raise RuntimeError("MNEMONIC missing in config")

    issuer_xsk, issuer_xvk, _ = _mk_keys_from_mnemonic(MNEMONIC, 0)
    user_xsk, user_xvk, user_addr = _mk_keys_from_mnemonic(MNEMONIC, 1)

    print(f"\n=== ACTION: MINT ===")
    print("Issuer PKH (hex):", issuer_xvk.hash())
    print("User PKH (hex):", user_xvk.hash())

    context = mk_context()
    mint = load_applied_mint_policy()
    store = load_applied_store_validator()

    # Choose a UTxO from user for entropy / fee
    utxos = context.utxos(user_addr)
    if not utxos:
        raise RuntimeError("No UTxO at user address; fund the wallet.")
    base_utxo = utxos[0]
    if not ensure_index_lt_256_utxo(base_utxo):
        raise RuntimeError("Selected UTxO index must be < 256 for CIP-68 suffix derivation.")

    suffix = derive_suffix_28_from_utxo(base_utxo)
    tn_ref = build_token_name_bytes(REFERENCE_TOKEN_LABEL, suffix)
    tn_user = build_token_name_bytes(NON_FUNGIBLE_TOKEN_LABEL, suffix)

    policy_id = mint.policy_id
    an_ref = AssetName(tn_ref)
    an_user = AssetName(tn_user)

    print("Minting for policy:", str(policy_id))
    print("  ref token name (hex):", an_ref.payload.hex())
    print("  user token name (hex):", an_user.payload.hex())
    print("  user addr:", user_addr)
    print("  store addr:", store.lock_address)

    # metadata (read file if exists)
    meta_path = Path(__file__).resolve().parent / "nft-metadata.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    else:
        meta = {"name": "CIP-68 NFT", "description": "minted by pycardano", "version": 1}

    inline_datum = metadatum_from_json(meta, version=meta.get("version", 1))

    # Build MultiAsset for minting (two tokens)
    ma = MultiAsset()
    ma[policy_id] = Asset({an_ref: 1, an_user: 1})

    builder = TransactionBuilder(context)
    builder.mint = ma

    # Redeemer must be Option(Some(Mint)) per Aiken type Option<MintAction>
    mint_redeemer = make_mint_redeemer(is_mint=True)
    builder.add_minting_script(mint.script, mint_redeemer)

    # Output to user (user NFT)
    out_user = TransactionOutput(user_addr, Value(0, MultiAsset({policy_id: Asset({an_user: 1})})))
    out_user.amount.coin = min_lovelace(context, out_user)
    builder.add_output(out_user)

    # Output to store (ref NFT + inline datum)
    out_ref = TransactionOutput(store.lock_address, Value(0, MultiAsset({policy_id: Asset({an_ref: 1})})), datum=inline_datum)
    out_ref.amount.coin = min_lovelace(context, out_ref)
    builder.add_output(out_ref)

    # Use user's UTxOs to pay fees
    builder.add_input_address(user_addr)

    if debug:
        _debug_tx_builder(builder)

    try:
        signed = builder.build_and_sign([user_xsk, issuer_xsk], change_address=user_addr, auto_required_signers=True)
    except Exception as e:
        print("\n❌ Build/sign failed. Dumping builder state and exception:")
        traceback.print_exc()
        _debug_tx_builder(builder)
        raise

    return _simulate_or_submit(context, signed, submit)

def action_burn(debug: bool = False, submit: bool = True):
    """Burn both tokens and spend store UTxO (remove)."""
    if not MNEMONIC:
        raise RuntimeError("MNEMONIC missing in config")

    issuer_xsk, issuer_xvk, _ = _mk_keys_from_mnemonic(MNEMONIC, 0)
    user_xsk, user_xvk, user_addr = _mk_keys_from_mnemonic(MNEMONIC, 1)

    print(f"\n=== ACTION: BURN ===")
    print("Issuer PKH (hex):", issuer_xvk.hash().hex())
    print("User PKH (hex):", user_xvk.hash().hex())

    context = mk_context()
    mint = load_applied_mint_policy()
    store = load_applied_store_validator()

    utxos = context.utxos(user_addr)
    if not utxos:
        raise RuntimeError("No UTxO at user address")
    base_utxo = utxos[0]
    if not ensure_index_lt_256_utxo(base_utxo):
        raise RuntimeError("Selected UTxO index must be < 256")

    suffix = derive_suffix_28_from_utxo(base_utxo)
    tn_ref = build_token_name_bytes(REFERENCE_TOKEN_LABEL, suffix)
    tn_user = build_token_name_bytes(NON_FUNGIBLE_TOKEN_LABEL, suffix)

    policy_id = mint.policy_id
    an_ref = AssetName(tn_ref)
    an_user = AssetName(tn_user)

    print("Burning for policy:", str(policy_id))
    print("  ref token name (hex):", an_ref.payload.hex())
    print("  user token name (hex):", an_user.payload.hex())

    # Build mint map with negative quantities
    ma = MultiAsset()
    ma[policy_id] = Asset({an_ref: -1, an_user: -1})

    builder = TransactionBuilder(context)
    builder.mint = ma

    # Redeemer Some(Burn)
    burn_redeemer = make_mint_redeemer(is_mint=False)
    builder.add_minting_script(mint.script, burn_redeemer)

    # We must also spend the store UTxO that contains the ref token (validator expects it)
    store_utxos = context.utxos(store.lock_address)
    # find a utxo that has our policy/an_ref
    store_ref_utxo = None
    for u in store_utxos:
        try:
            multi = u.output.amount.multi_asset
            if policy_id in multi and an_ref in multi[policy_id] and multi[policy_id][an_ref] >= 1:
                store_ref_utxo = u
                break
        except Exception:
            continue

    if store_ref_utxo is None:
        raise RuntimeError("No store UTxO found containing the reference token required for burn.")

    # Redeemer: Option(Some(Remove)) for store validator
    store_remove_redeemer = make_store_redeemer(is_update=False)
    # add script input (spend store utxo)
    builder.add_script_input(store_ref_utxo, script=store.script, datum=store_ref_utxo.output.datum, redeemer=store_remove_redeemer)

    # Add user address inputs to cover fees/burn
    builder.add_input_address(user_addr)

    if debug:
        _debug_tx_builder(builder)

    try:
        signed = builder.build_and_sign([user_xsk, issuer_xsk], change_address=user_addr, auto_required_signers=True)
    except Exception as e:
        print("\n❌ Build/sign failed (burn). Dumping builder and exception:")
        traceback.print_exc()
        _debug_tx_builder(builder)
        raise

    return _simulate_or_submit(context, signed, submit)

def action_update_store(debug: bool = False, submit: bool = True):
    """Spend the store UTxO and recreate it with updated datum (Update)."""
    if not MNEMONIC:
        raise RuntimeError("MNEMONIC missing in config")

    issuer_xsk, issuer_xvk, issuer_addr = _mk_keys_from_mnemonic(MNEMONIC, 0)
    _, _, user_addr = _mk_keys_from_mnemonic(MNEMONIC, 1)

    print(f"\n=== ACTION: UPDATE STORE ===")
    print("Issuer PKH (hex):", issuer_xvk.hash().hex())

    context = mk_context()
    store = load_applied_store_validator()

    utxos = context.utxos(store.lock_address)
    if not utxos:
        raise RuntimeError("No UTxO at store script address")
    store_utxo = utxos[0]

    # Extract first policy & asset name from multi_asset (robust)
    multi = store_utxo.output.amount.multi_asset
    policies = list(multi.keys())
    if not policies:
        raise RuntimeError("Store UTxO has no native assets")
    policy_id = policies[0]
    names_map = multi[policy_id]
    an_ref = list(names_map.keys())[0]

    print("Updating store UTxO:", store_utxo.input.transaction_id.hex(), store_utxo.input.index)
    print("  policy:", str(policy_id))
    print("  asset name (hex):", an_ref.payload.hex())

    # New datum
    meta_path = Path(__file__).resolve().parent / "nft-metadata.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    else:
        meta = {"name": "CIP-68 NFT", "description": "updated", "version": 2}
    inline_datum = metadatum_from_json(meta, version=meta.get("version", 1))

    builder = TransactionBuilder(context)
    # Redeemer: Option(Some(Update))
    store_update_redeemer = make_store_redeemer(is_update=True)
    builder.add_script_input(store_utxo, script=store.script, datum=store_utxo.output.datum, redeemer=store_update_redeemer)

    # Recreate script output
    out_ref = TransactionOutput(store.lock_address, Value(0, MultiAsset({policy_id: Asset({an_ref: 1})})), datum=inline_datum)
    out_ref.amount.coin = min_lovelace(context, out_ref)
    builder.add_output(out_ref)

    # Provide issuer (payer) input for fees
    builder.add_input_address(issuer_addr)

    if debug:
        _debug_tx_builder(builder)

    try:
        signed = builder.build_and_sign([issuer_xsk], change_address=issuer_addr, auto_required_signers=True)
    except Exception as e:
        print("\n❌ Build/sign failed (update). Dumping builder and exception:")
        traceback.print_exc()
        _debug_tx_builder(builder)
        raise

    return _simulate_or_submit(context, signed, submit)

def action_remove_store(debug: bool = False, submit: bool = True):
    """Spend the store UTxO and move the ref asset out of script (Remove)."""
    if not MNEMONIC:
        raise RuntimeError("MNEMONIC missing in config")

    issuer_xsk, issuer_xvk, issuer_addr = _mk_keys_from_mnemonic(MNEMONIC, 0)
    _, _, user_addr = _mk_keys_from_mnemonic(MNEMONIC, 1)

    print(f"\n=== ACTION: REMOVE STORE ===")
    print("Issuer PKH (hex):", issuer_xvk.hash().hex())

    context = mk_context()
    store = load_applied_store_validator()

    utxos = context.utxos(store.lock_address)
    if not utxos:
        raise RuntimeError("No UTxO at store script address")
    store_utxo = utxos[0]

    multi = store_utxo.output.amount.multi_asset
    if not multi:
        raise RuntimeError("Store UTxO missing native assets")
    policy_id = list(multi.keys())[0]
    an_ref = list(multi[policy_id].keys())[0]

    recipient = user_addr

    builder = TransactionBuilder(context)
    # Redeemer: Option(Some(Remove))
    store_remove_redeemer = make_store_redeemer(is_update=False)
    builder.add_script_input(store_utxo, script=store.script, datum=store_utxo.output.datum, redeemer=store_remove_redeemer)

    out_any = TransactionOutput(recipient, Value(0, MultiAsset({policy_id: Asset({an_ref: 1})})), datum=store_utxo.output.datum)
    out_any.amount.coin = min_lovelace(context, out_any)
    builder.add_output(out_any)

    if debug:
        _debug_tx_builder(builder)

    try:
        signed = builder.build_and_sign([issuer_xsk], change_address=issuer_addr, auto_required_signers=True)
    except Exception as e:
        print("\n❌ Build/sign failed (remove). Dumping builder and exception:")
        traceback.print_exc()
        _debug_tx_builder(builder)
        raise

    return _simulate_or_submit(context, signed, submit)

# -----------------------
# CLI
# -----------------------
def main():
    if len(sys.argv) < 2:
        print("Usage: python -m off_chain.cip68_offchain <mint|burn|update|remove> [--debug] [--no-submit]")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    debug = "--debug" in sys.argv
    no_submit = "--no-submit" in sys.argv

    if cmd == "mint":
        safe_run(action_mint, debug=debug, submit=not no_submit)
    elif cmd == "burn":
        safe_run(action_burn, debug=debug, submit=not no_submit)
    elif cmd == "update":
        safe_run(action_update_store, debug=debug, submit=not no_submit)
    elif cmd == "remove":
        safe_run(action_remove_store, debug=debug, submit=not no_submit)
    else:
        print("Unknown command:", cmd)
        sys.exit(2)

if __name__ == "__main__":
    main()
