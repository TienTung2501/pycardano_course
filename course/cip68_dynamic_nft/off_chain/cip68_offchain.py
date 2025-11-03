# python -m off_chain.cip68_offchain mint
# python -m off_chain.cip68_offchain update
# python -m off_chain.cip68_offchain burn
#!/usr/bin/env python3
"""
CIP-68 off-chain utility: mint / burn / update / remove.

Usage:
  python -m off_chain.cip68_offchain mint
  python -m off_chain.cip68_offchain burn
  python -m off_chain.cip68_offchain update
  python -m off_chain.cip68_offchain remove

This script expects the helper functions from your project:
- mk_context, network
- load_applied_mint_policy, load_applied_store_validator
- derive_suffix_28_from_input, ensure_index_lt_256
- build_token_name
- metadatum_from_json
- REFERENCE_TOKEN_LABEL, NON_FUNGIBLE_TOKEN_LABEL, MNEMONIC
"""
import sys
import json
from pathlib import Path
from typing import Tuple

from pycardano.exception import TransactionFailedException
import traceback
import json

from pycardano import (
    Address,
    Asset,
    AssetName,
    MultiAsset,
    Redeemer,
    TransactionOutput,
    Value,
    min_lovelace,
)
from pycardano import PlutusData
from pycardano.exception import TransactionFailedException
from pycardano.key import ExtendedSigningKey, ExtendedVerificationKey
from pycardano.txbuilder import TransactionBuilder
from pycardano.crypto.bip32 import HDWallet
# For proper Redeemer constructors

# Project utilities (your code)
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


# ---------- Helpers ----------
from dataclasses import dataclass
from typing import Union, Dict, List, Tuple
from pycardano import RawCBOR

# Helper to represent a metadata entry as PlutusData
@dataclass
class MetadataEntry(PlutusData):
    """Single key-value pair for CIP-68 metadata map"""
    CONSTR_ID = None  # No constructor, just a tuple-like structure
    key: bytes
    value: bytes

@dataclass
class MintAction:
    @dataclass
    class Mint(PlutusData):
        CONSTR_ID = 0
    
    @dataclass  
    class Burn(PlutusData):
        CONSTR_ID = 1

@dataclass
class OptionMintAction(PlutusData):
    """Option type wrapping MintAction - Some(MintAction)"""
    CONSTR_ID = 0  # Some
    value: Union[MintAction.Mint, MintAction.Burn]  # The wrapped MintAction

@dataclass
class CIP68Datum(PlutusData):
    """CIP-68 NFT metadata datum: Constr(0, [metadata_list_of_pairs, version, extra])"""
    CONSTR_ID = 0
    metadata: List[List[bytes]]  # List of [key, value] pairs as nested lists
    version: int  # Version number
    extra: bytes  # Extra data (usually empty)

@dataclass
class StoreAction:
    class Update(PlutusData):
        CONSTR_ID = 0
    class Remove(PlutusData):
        CONSTR_ID = 1
def _json_to_cip68_datum(metadata_json: dict, version: int = 1) -> CIP68Datum:
    """
    Convert JSON metadata dictionary to CIP68Datum PlutusData structure.
    
    Args:
        metadata_json: Dictionary with string keys (from JSON)
        version: CIP-68 version (default 1)
    
    Returns:
        CIP68Datum instance with metadata as list of [key, value] byte pairs
    """
    # Convert to list of [key_bytes, value_bytes] lists for Plutus Data encoding
    # Aiken Dict<K,V> is encoded as List<[K,V]> in Plutus Data
    metadata_pairs = [[k.encode('utf-8'), v.encode('utf-8') if isinstance(v, str) else v] 
                      for k, v in metadata_json.items()]
    
    return CIP68Datum(
        metadata=metadata_pairs,
        version=version,
        extra=b''  # Empty extra field for now
    )


def _mk_keys_from_mnemonic(mnemonic: str, idx: int) -> Tuple[ExtendedSigningKey, ExtendedVerificationKey, Address]:
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
    print("==== TransactionBuilder state (debug) ====")
    try:
        print(builder.__dict__)
    except Exception:
        print("(unable to pretty print builder)")
    print("=========================================")

def _simulate_or_submit(context, tx, submit: bool):
    """
    Try evaluate_tx (simulate). If simulation passes, optionally submit.
    """
    try:
        print("Simulating transaction (evaluate)...")
        eval_res = context.evaluate_tx_cbor(tx.to_cbor())
        print("Simulation result:", eval_res)
    except TransactionFailedException as e:
        print("Simulation FAILED. Blockfrost/ogmios returned evaluation failure:")
        print(e)
        raise

    if submit:
        print("Submitting tx...")
        tx_id = context.submit_tx(tx.to_cbor())
        print("Submitted:", tx_id)
        return tx_id
    return None

# ---------- Actions ----------

def action_mint(debug=False, submit=True):
    """Mint pair: ref(label=100) -> store (with inline datum), user(label=222) -> user address"""
    if not MNEMONIC:
        raise RuntimeError("MNEMONIC missing in config")

    issuer_xsk, issuer_xvk, _ = _mk_keys_from_mnemonic(MNEMONIC, 0)
    user_xsk, user_xvk, user_addr = _mk_keys_from_mnemonic(MNEMONIC, 1)

    context = mk_context()
    
    # Load store validator first (cần script_hash để truyền vào mint policy)
    store = load_applied_store_validator(issuer_vkh=issuer_xvk.hash())
    
    # Load mint policy với issuer + store parameters
    mint = load_applied_mint_policy(
        issuer_vkh=issuer_xvk.hash(),
        store_script_hash=store.script_hash
    )
    
    print("Issuer PKH (hex):", issuer_xvk.hash())
    print("User PKH (hex):", user_xvk.hash())
    # pick UTxO for entropy
    utxos = context.utxos(user_addr)
    if not utxos:
        raise RuntimeError("User address has no UTxO")
    base_utxo = utxos[0]
    if not ensure_index_lt_256(base_utxo):
        raise RuntimeError("Selected UTxO index must be < 256")

    suffix = derive_suffix_28_from_input(base_utxo)
    tn_ref = build_token_name(REFERENCE_TOKEN_LABEL, suffix)
    tn_user = build_token_name(NON_FUNGIBLE_TOKEN_LABEL, suffix)

    policy_id = mint.policy_id
    an_ref = AssetName(tn_ref)
    an_user = AssetName(tn_user)

    print("Minting pair for policy:", policy_id.payload.hex())
    print("  ref token name (hex):", an_ref.payload.hex())
    print("  user token name (hex):", an_user.payload.hex())
    print("  user addr:", user_addr)
    print("  store addr:", store.lock_address)

    # read (or minimal) metadata
    meta_path = Path(__file__).resolve().parent / "nft-metadata.json"
    if meta_path.exists():
        meta_json = json.loads(meta_path.read_text(encoding="utf-8"))
    else:
        meta_json = {"name": "CIP-68 NFT", "description": "minted by pycardano", "version": 1}

    # Create inline datum using CIP68Datum dataclass
    inline_datum = _json_to_cip68_datum(meta_json, version=1)

    # Build MultiAsset (correct types)
    ma = MultiAsset()
    ma[policy_id] = Asset({an_ref: 1, an_user: 1})

    builder = TransactionBuilder(context)
    builder.mint = ma

    # Redeemer: Option<MintAction> with Some(Mint)  
    # Some(MintAction.Mint) = Constr(0, [Constr(0, [])])
    mint_action = MintAction.Mint()
    some_mint_action = OptionMintAction(value=mint_action)
    mint_redeemer = Redeemer(some_mint_action)
    
    builder.add_minting_script(mint.script, mint_redeemer)
    
    # NOTE: For first mint, store address has no UTxOs yet, so no reference input needed
    # store_utxos = context.utxos(store.lock_address)
    # if store_utxos:
    #     builder.add_reference_input(store_utxos[0])
    #     print("Added store reference input:", store_utxos[0].input)
    
    # FIX: ĐẢO NGƯỢC THỨ TỰ — ref token (store) PHẢI LÀ OUTPUT ĐẦU TIÊN
    # Output 1: ref NFT → store (FIRST) with INLINE datum
    out_ref = TransactionOutput(
        store.lock_address,
        Value(0, MultiAsset({policy_id: Asset({an_ref: 1})})),
        datum=inline_datum,
        post_alonzo=True  # Enable inline datum
    )
    out_ref.amount.coin = min_lovelace(context, out_ref)
    builder.add_output(out_ref)

    # Output 2: user NFT → user address (SECOND)
    out_user = TransactionOutput(
        user_addr,
        Value(0, MultiAsset({policy_id: Asset({an_user: 1})}))
    )
    out_user.amount.coin = min_lovelace(context, out_user)
    builder.add_output(out_user)

    # Add input address (use user's UTxOs to pay fees)
    builder.add_input_address(user_addr)

    if debug:
        _debug_tx_builder(builder)

    # Build & sign - bypass evaluation completely
    from pycardano import ExecutionUnits, RedeemerTag
    
    # Set execution units manually on the redeemer to avoid evaluation
    print("\nSetting manual execution units to bypass evaluation...")
    
    # Set high execution units directly on the mint redeemer
    # Find the mint redeemer and update its ex_units
    for script, redeemer in builder._minting_script_to_redeemers:
        if redeemer.tag == RedeemerTag.MINT and redeemer.index == 0:
            redeemer.ex_units = ExecutionUnits(mem=14000000, steps=10000000000)
            print(f"Set execution units: {redeemer.ex_units}")
            break
    
    # Disable automatic estimation
    builder._should_estimate_execution_units = False
    
    try:
        signed_tx = builder.build_and_sign(
            [issuer_xsk, user_xsk], 
            change_address=user_addr,
            auto_required_signers=True
        )
        
        print(f"\nTransaction built successfully!")
        print(f"Transaction ID: {signed_tx.id}")
        
    except Exception as e:
        print(f"Builder build failed: {e}")
        import traceback
        traceback.print_exc()
        raise

    # Submit directly to network
    return _simulate_or_submit(context, signed_tx, submit)

def action_burn(debug=False, submit=True):
    """Burn pair: burn both ref and user (amount -1 each)."""
    if not MNEMONIC:
        raise RuntimeError("MNEMONIC missing in config")

    issuer_xsk, issuer_xvk, _ = _mk_keys_from_mnemonic(MNEMONIC, 0)
    user_xsk, user_xvk, user_addr = _mk_keys_from_mnemonic(MNEMONIC, 1)
    
    context = mk_context()
    
    # Load validators với parameters
    store = load_applied_store_validator(issuer_vkh=issuer_xvk.hash())
    mint = load_applied_mint_policy(
        issuer_vkh=issuer_xvk.hash(),
        store_script_hash=store.script_hash
    )

    # pick a UTxO (that currently holds the user NFT) - here we choose first
    utxos = context.utxos(user_addr)
    if not utxos:
        raise RuntimeError("User address has no UTxO")
    base_utxo = utxos[0]
    if not ensure_index_lt_256(base_utxo):
        raise RuntimeError("Selected UTxO index must be < 256")

    suffix = derive_suffix_28_from_input(base_utxo)
    tn_ref = build_token_name(REFERENCE_TOKEN_LABEL, suffix)
    tn_user = build_token_name(NON_FUNGIBLE_TOKEN_LABEL, suffix)

    policy_id = mint.policy_id
    an_ref = AssetName(tn_ref)
    an_user = AssetName(tn_user)

    print("Burning pair for policy:", policy_id.payload.hex())
    print("  ref token:", an_ref.payload.hex())
    print("  user token:", an_user.payload.hex())

    # Build MultiAsset with negative quantity (burn)
    ma = MultiAsset()
    ma[policy_id] = Asset({an_ref: -1, an_user: -1})

    builder = TransactionBuilder(context)
    builder.mint = ma
    burn_redeemer = Redeemer(MintAction.Burn.CONSTR_ID)  # MintAction.Burn -> constructor index 1
    builder.add_minting_script(mint.script, burn_redeemer)

    # Tìm UTxO ở store chứa ref token để Remove (validator yêu cầu)
    store_utxos = context.utxos(store.lock_address)
    store_ref = next(
        (u for u in store_utxos
        if u.output.amount.multi_asset.get(policy_id, {}).get(an_ref, 0) >= 1),
        None
    )
    if not store_ref:
        raise RuntimeError("Store UTxO with reference token not found (required for burn)")
    # Spend store UTxO với redeemer Remove=1 và kèm datum gốc
    builder.add_script_input(store_ref, script=store.script, datum=store_ref.output.datum, redeemer=Redeemer(StoreAction.Remove.CONSTR_ID))

    # Add input utxo(s) from user to provide tokens to burn / cover fees
    builder.add_input_address(user_addr)

    # No outputs besides change (we allow builder to create change)
    try:
        signed_tx = builder.build_and_sign([issuer_xsk, user_xsk], change_address=user_addr, auto_required_signers=True)
    except TransactionFailedException as e:
        print("Builder build failed:", e)
        raise

    return _simulate_or_submit(context, signed_tx, submit)

def action_update_store(debug=False, submit=True):
    """Spend the store UTxO and re-create it (Update) with new datum (same address)."""
    if not MNEMONIC:
        raise RuntimeError("MNEMONIC missing in config")

    issuer_xsk, issuer_xvk, issuer_addr = _mk_keys_from_mnemonic(MNEMONIC, 0)
    user_xsk, user_xvk, user_addr = _mk_keys_from_mnemonic(MNEMONIC, 1)

    context = mk_context()
    
    # Load validators với parameters
    store = load_applied_store_validator(issuer_vkh=issuer_xvk.hash())
    mint = load_applied_mint_policy(
        issuer_vkh=issuer_xvk.hash(),
        store_script_hash=store.script_hash
    )

    # Find a UTxO locked by store script that contains the ref token
    utxos = context.utxos(store.lock_address)
    if not utxos:
        raise RuntimeError("No UTxO found at store script address")

    # Pick first store utxo
    store_utxo = utxos[0]
    # Extract policy & name from that utxo (expect 1 non-ada asset)
    flat = store_utxo.output.amount.multi_asset
    # find first policy/name
    # Convert to first asset entry
    policy_ids = list(flat.keys())
    policy_id = policy_ids[0]
    assets_for_policy = flat[policy_id]
    # pick first asset name
    an_ref = list(assets_for_policy.keys())[0]

    print("Updating store UTxO:", store_utxo.input.transaction_id.hex(), store_utxo.input.index)
    print("  policy:", policy_id.payload.hex())
    print("  asset name:", an_ref.payload.hex())

    # Prepare new datum (for example, read metadata and bump version)
    meta_path = Path(__file__).resolve().parent / "nft-metadata.json"
    if meta_path.exists():
        meta_json = json.loads(meta_path.read_text(encoding="utf-8"))
    else:
        meta_json = {"name": "CIP-68 NFT", "description": "updated", "version": 2}

    inline_datum = metadatum_from_json(meta_json, version=meta_json.get("version", 1))

    # Build tx: spend the store UTxO (script) with Redeemer(StoreAction.Update) and recreate it
    builder = TransactionBuilder(context)
    # Add the store utxo as input (script spend)
    builder.add_script_input(
        store_utxo,
        script=store.script,
        datum=store_utxo.output.datum,
        redeemer=Redeemer(StoreAction.Update.CONSTR_ID)  # Update -> 0
    )

    # Recreate script output containing same asset + new datum with INLINE
    out_ref = TransactionOutput(
        store.lock_address,
        Value(0, MultiAsset({policy_id: Asset({an_ref: 1})})),
        datum=inline_datum,
        post_alonzo=True  # Enable inline datum
    )
    out_ref.amount.coin = min_lovelace(context, out_ref)
    builder.add_output(out_ref)

    # Thêm input từ ví issuer để trả phí và yêu cầu ký
    builder.add_input_address(issuer_addr)
    # Sign by issuer (and user if needed); let builder auto add required signers
    try:
        signed_tx = builder.build_and_sign([issuer_xsk, user_xsk], change_address=user_addr, auto_required_signers=True)
    except TransactionFailedException as e:
        print("Builder build failed:", e)
        raise

    return _simulate_or_submit(context, signed_tx, submit)

def action_remove_store(debug=False, submit=True):
    """Spend the store UTxO and remove it from script (send to user)"""
    if not MNEMONIC:
        raise RuntimeError("MNEMONIC missing in config")

    issuer_xsk, issuer_xvk, issuer_addr = _mk_keys_from_mnemonic(MNEMONIC, 0)
    _, _, user_addr = _mk_keys_from_mnemonic(MNEMONIC, 1)

    context = mk_context()
    
    # Load store validator với parameter
    store = load_applied_store_validator(issuer_vkh=issuer_xvk.hash())

    utxos = context.utxos(store.lock_address)
    if not utxos:
        raise RuntimeError("No store UTxO found")
    store_utxo = utxos[0]
    flat = store_utxo.output.amount.multi_asset
    policy_id = list(flat.keys())[0]
    an_ref = list(flat[policy_id].keys())[0]

    # decide recipient (send to issuer for example)
    recipient_addr = user_addr

    builder = TransactionBuilder(context)
    builder.add_script_input(store_utxo, script=store.script, redeemer=Redeemer(StoreAction.Remove.CONSTR_ID))  # Remove -> 1

    # Recreate UTxO anywhere (non-script) preserving asset + datum shape (validator wants shape)
    out_any = TransactionOutput(
        recipient_addr,
        Value(0, MultiAsset({policy_id: Asset({an_ref: 1})})),
        # preserve inline datum from original? To be safe, attach same datum
        datum=store_utxo.output.datum if store_utxo.output.datum is not None else None
    )
    out_any.amount.coin = min_lovelace(context, out_any)
    builder.add_output(out_any)

    try:
        signed_tx = builder.build_and_sign([issuer_xsk], change_address=None)
    except TransactionFailedException as e:
        print("Builder build failed:", e)
        raise

    return _simulate_or_submit(context, signed_tx, submit)


# ---------- CLI ----------
def main():
    if len(sys.argv) < 2:
        print("Usage: python -m off_chain.cip68_offchain <mint|burn|update|remove> [--debug] [--no-submit]")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    debug = "--debug" in sys.argv
    no_submit = "--no-submit" in sys.argv

    if cmd == "mint":
        action_mint(debug=debug, submit=not no_submit)
    elif cmd == "burn":
        action_burn(debug=debug, submit=not no_submit)
    elif cmd == "update":
        action_update_store(debug=debug, submit=not no_submit)
    elif cmd == "remove":
        action_remove_store(debug=debug, submit=not no_submit)
    else:
        print("Unknown command:", cmd)
        sys.exit(2)

if __name__ == "__main__":
    main()
