#!/usr/bin/env python3
"""
Update CIP-68 NFT Metadata

This script updates the metadata of an existing CIP-68 NFT by spending
the reference token and recreating it with new metadata.

Usage:
    python update_nft.py <policy_id> <asset_name_hex> [--debug] [--no-submit]
"""
import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from pycardano import (
    Address,
    AssetName,
    BlockFrostChainContext,
    PaymentSigningKey,
    PaymentVerificationKey,
    PlutusData,
    TransactionBuilder,
    TransactionOutput,
    UTxO,
    Value,
    Redeemer,
    plutus_script_hash,
    script_hash,
)

import config
import utils


def find_reference_token_utxo(context, store_addr, policy_id, ref_token_name):
    """Find the UTxO containing the reference token at store address."""
    utxos = context.utxos(store_addr)
    
    for utxo in utxos:
        # Check if this UTxO contains our reference token
        if utxo.output.amount.multi_asset:
            for pid, assets in utxo.output.amount.multi_asset.items():
                if pid.payload.hex() == policy_id:
                    for asset_name, qty in assets.items():
                        if asset_name.payload.hex() == ref_token_name and qty == 1:
                            return utxo
    
    return None


def main():
    parser = argparse.ArgumentParser(description="Update CIP-68 NFT metadata")
    parser.add_argument("policy_id", help="Policy ID (hex)")
    parser.add_argument("asset_name", help="28-byte asset name suffix (hex)")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--no-submit", action="store_true", help="Build but don't submit")
    args = parser.parse_args()
    
    print("=" * 60)
    print("CIP-68 NFT Metadata Update")
    print("=" * 60)
    
    # 1. Setup
    print("\n[1] Setting up...")
    context = BlockFrostChainContext(
        project_id=config.BLOCKFROST_PROJECT_ID,
        network=config.NETWORK,
    )
    
    # Load keys
    from off_chain.mint_nft import generate_or_load_keys
    issuer_skey, issuer_vkey = generate_or_load_keys(config.ISSUER_MNEMONIC_FILE)
    
    issuer_pkh = issuer_vkey.hash()
    issuer_addr = Address(issuer_pkh, network=context.network)
    
    print(f"   Issuer PKH: {issuer_pkh.to_primitive().hex()}")
    
    # 2. Rebuild validators
    print("\n[2] Rebuilding validators...")
    
    # Build store validator
    store_script = utils.apply_params_to_script(
        config.STORE_VALIDATOR_TITLE,
        [issuer_pkh.to_primitive()]
    )
    store_hash = plutus_script_hash(store_script)
    store_addr = Address(store_hash, network=context.network)
    
    print(f"   Store Address: {store_addr}")
    
    # 3. Find reference token UTxO
    print("\n[3] Finding reference token UTxO...")
    
    policy_id = bytes.fromhex(args.policy_id)
    asset_name_suffix = bytes.fromhex(args.asset_name)
    
    ref_token_name = utils.build_token_name(config.LABEL_100, asset_name_suffix)
    
    print(f"   Policy ID: {args.policy_id}")
    print(f"   Ref token name: {ref_token_name.hex()}")
    print(f"   Looking for UTxO at: {store_addr}")
    
    ref_utxo = find_reference_token_utxo(
        context, 
        store_addr, 
        args.policy_id,
        ref_token_name.hex()
    )
    
    if not ref_utxo:
        print(f"\n   ✗ Error: Reference token not found!")
        print(f"   Make sure the token exists at store address: {store_addr}")
        sys.exit(1)
    
    print(f"   ✓ Found reference token at:")
    print(f"     TxHash: {ref_utxo.input.transaction_id}")
    print(f"     Index: {ref_utxo.input.index}")
    
    # Get current datum
    current_datum = ref_utxo.output.datum
    print(f"   Current datum type: {type(current_datum)}")
    
    # 4. Create new metadata
    print("\n[4] Creating new metadata...")
    
    new_metadata = {
        "name": "Updated CIP-68 NFT",
        "description": "Metadata updated via PyCardano",
        "image": "ipfs://QmNewHash123456789",
        "updated_at": "2024-11-01",
        "version": "2.0",
    }
    
    new_datum = utils.create_cip68_datum(new_metadata)
    print(f"   New metadata: {new_metadata}")
    
    # 5. Build transaction
    print("\n[5] Building update transaction...")
    
    builder = TransactionBuilder(context)
    
    # Add issuer's UTXOs for fees
    builder.add_input_address(issuer_addr)
    
    # Spend the reference token UTxO from store
    @dataclass
    class StoreAction(PlutusData):
        CONSTR_ID = 0  # Update variant
    
    store_redeemer = Redeemer(StoreAction())
    builder.add_script_input(ref_utxo, store_script, None, store_redeemer)
    
    # Output: Send reference token back to store with new datum
    ref_output = TransactionOutput(
        address=store_addr,
        amount=ref_utxo.output.amount,  # Same amount (ADA + token)
        datum=new_datum,  # NEW datum
    )
    builder.outputs.append(ref_output)
    
    # Add required signers
    builder.required_signers = [issuer_vkey.hash()]
    
    # Set collateral
    builder.collaterals = context.utxos(issuer_addr)[:1]
    
    # Build and sign
    print("\n[6] Signing transaction...")
    tx_body = builder.build(change_address=issuer_addr)
    signed_tx = tx_body.sign([issuer_skey])
    
    print(f"   Transaction ID: {signed_tx.id}")
    
    if args.debug:
        print("\n[DEBUG] Transaction CBOR:")
        print(f"   {signed_tx.to_cbor().hex()}")
    
    # 7. Submit
    if args.no_submit:
        print("\n[SKIP] Transaction built but not submitted")
    else:
        print("\n[7] Submitting transaction...")
        try:
            tx_hash = context.submit_tx(signed_tx)
            print(f"   ✓ Metadata updated successfully!")
            print(f"   TX Hash: {tx_hash}")
            print(f"\n   View on explorer:")
            print(f"   https://preprod.cardanoscan.io/transaction/{tx_hash}")
            
        except Exception as e:
            print(f"   ✗ Transaction failed:")
            print(f"   {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
