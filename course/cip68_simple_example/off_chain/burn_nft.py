#!/usr/bin/env python3
"""
Burn CIP-68 NFT

This script burns both the reference token and user token of a CIP-68 NFT pair.

Usage:
    python burn_nft.py <policy_id> <asset_name_hex> [--debug] [--no-submit]
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


def find_token_utxos(context, policy_id_hex, ref_token_hex, user_token_hex, store_addr, user_addr):
    """Find UTxOs containing both reference and user tokens."""
    # Find reference token at store
    ref_utxo = None
    for utxo in context.utxos(store_addr):
        if utxo.output.amount.multi_asset:
            for pid, assets in utxo.output.amount.multi_asset.items():
                if pid.payload.hex() == policy_id_hex:
                    for asset_name, qty in assets.items():
                        if asset_name.payload.hex() == ref_token_hex and qty == 1:
                            ref_utxo = utxo
                            break
    
    # Find user token at user wallet
    user_utxo = None
    for utxo in context.utxos(user_addr):
        if utxo.output.amount.multi_asset:
            for pid, assets in utxo.output.amount.multi_asset.items():
                if pid.payload.hex() == policy_id_hex:
                    for asset_name, qty in assets.items():
                        if asset_name.payload.hex() == user_token_hex and qty == 1:
                            user_utxo = utxo
                            break
    
    return ref_utxo, user_utxo


def main():
    parser = argparse.ArgumentParser(description="Burn CIP-68 NFT pair")
    parser.add_argument("policy_id", help="Policy ID (hex)")
    parser.add_argument("asset_name", help="28-byte asset name suffix (hex)")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--no-submit", action="store_true", help="Build but don't submit")
    args = parser.parse_args()
    
    print("=" * 60)
    print("CIP-68 NFT Burn")
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
    user_skey, user_vkey = generate_or_load_keys(config.USER_MNEMONIC_FILE)
    
    issuer_pkh = issuer_vkey.hash()
    user_pkh = user_vkey.hash()
    
    issuer_addr = Address(issuer_pkh, network=context.network)
    user_addr = Address(user_pkh, network=context.network)
    
    print(f"   Issuer Address: {issuer_addr}")
    print(f"   User Address: {user_addr}")
    
    # 2. Rebuild validators
    print("\n[2] Rebuilding validators...")
    
    # Build store validator
    store_script = utils.apply_params_to_script(
        config.STORE_VALIDATOR_TITLE,
        [issuer_pkh.to_primitive()]
    )
    store_hash = plutus_script_hash(store_script)
    store_addr = Address(store_hash, network=context.network)
    
    # Build mint policy
    mint_script = utils.apply_params_to_script(
        config.MINT_VALIDATOR_TITLE,
        [
            store_hash.to_primitive(),
            issuer_pkh.to_primitive(),
        ]
    )
    policy_id = script_hash(mint_script)
    
    print(f"   Policy ID: {policy_id.to_primitive().hex()}")
    print(f"   Store Address: {store_addr}")
    
    # 3. Find tokens
    print("\n[3] Finding tokens to burn...")
    
    asset_name_suffix = bytes.fromhex(args.asset_name)
    ref_token_name = utils.build_token_name(config.LABEL_100, asset_name_suffix)
    user_token_name = utils.build_token_name(config.LABEL_222, asset_name_suffix)
    
    print(f"   Ref token: {ref_token_name.hex()}")
    print(f"   User token: {user_token_name.hex()}")
    
    ref_utxo, user_utxo = find_token_utxos(
        context,
        args.policy_id,
        ref_token_name.hex(),
        user_token_name.hex(),
        store_addr,
        user_addr
    )
    
    if not ref_utxo:
        print(f"\n   ✗ Error: Reference token not found at store!")
        sys.exit(1)
    
    if not user_utxo:
        print(f"\n   ✗ Error: User token not found at user wallet!")
        sys.exit(1)
    
    print(f"   ✓ Found reference token at: {ref_utxo.input.transaction_id}#{ref_utxo.input.index}")
    print(f"   ✓ Found user token at: {user_utxo.input.transaction_id}#{user_utxo.input.index}")
    
    # 4. Build burn transaction
    print("\n[4] Building burn transaction...")
    
    builder = TransactionBuilder(context)
    
    # Add issuer's UTXOs for fees
    builder.add_input_address(issuer_addr)
    
    # Spend reference token from store
    @dataclass
    class StoreAction(PlutusData):
        CONSTR_ID = 1  # Burn variant
    
    store_redeemer = Redeemer(StoreAction())
    builder.add_script_input(ref_utxo, store_script, None, store_redeemer)
    
    # Spend user token from user wallet (regular input, no script)
    builder.add_input(user_utxo)
    
    # Burn both tokens (negative mint)
    builder.mint = Value(multi_asset={
        policy_id: {
            ref_token_name: -1,
            user_token_name: -1,
        }
    })
    
    # Add mint redeemer
    @dataclass
    class MintAction(PlutusData):
        CONSTR_ID = 1  # Burn variant
    
    mint_redeemer = Redeemer(MintAction())
    builder.add_minting_script(mint_script, mint_redeemer)
    
    # Add required signers
    builder.required_signers = [issuer_vkey.hash(), user_vkey.hash()]
    
    # Set collateral
    builder.collaterals = context.utxos(issuer_addr)[:1]
    
    # Build and sign
    print("\n[5] Signing transaction...")
    tx_body = builder.build(change_address=issuer_addr)
    signed_tx = tx_body.sign([issuer_skey, user_skey])
    
    print(f"   Transaction ID: {signed_tx.id}")
    
    if args.debug:
        print("\n[DEBUG] Transaction CBOR:")
        print(f"   {signed_tx.to_cbor().hex()}")
    
    # 6. Submit
    if args.no_submit:
        print("\n[SKIP] Transaction built but not submitted")
    else:
        print("\n[6] Submitting transaction...")
        try:
            tx_hash = context.submit_tx(signed_tx)
            print(f"   ✓ Tokens burned successfully!")
            print(f"   TX Hash: {tx_hash}")
            print(f"\n   View on explorer:")
            print(f"   https://preprod.cardanoscan.io/transaction/{tx_hash}")
            print(f"\n   Both tokens have been removed from circulation.")
            
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
