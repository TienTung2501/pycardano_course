#!/usr/bin/env python3
"""
Query CIP-68 NFT Information

This script queries and displays information about a CIP-68 NFT,
including its metadata, current owner, and token locations.

Usage:
    python query_nft.py <policy_id> <asset_name_hex>
"""
import argparse
import json
import sys
from pathlib import Path

from pycardano import (
    Address,
    BlockFrostChainContext,
    PaymentVerificationKey,
    plutus_script_hash,
)

import config
import utils


def decode_metadata_datum(datum):
    """Decode CIP-68 metadata datum to human-readable format."""
    try:
        # Datum should be CIP68Datum with metadata, version, extra
        metadata_list = []
        
        if hasattr(datum, 'metadata'):
            for pair in datum.metadata:
                if len(pair) == 2:
                    key = pair[0].decode('utf-8') if isinstance(pair[0], bytes) else str(pair[0])
                    val = pair[1].decode('utf-8') if isinstance(pair[1], bytes) else str(pair[1])
                    metadata_list.append({key: val})
        
        return {
            "metadata": metadata_list,
            "version": getattr(datum, 'version', 'unknown'),
            "extra": getattr(datum, 'extra', b'').hex() if hasattr(datum, 'extra') else 'unknown'
        }
    except Exception as e:
        return {"error": f"Failed to decode: {e}", "raw": str(datum)}


def find_tokens(context, policy_id_hex, ref_token_hex, user_token_hex, store_addr):
    """Find both reference and user tokens."""
    # Find reference token at store
    ref_info = None
    for utxo in context.utxos(store_addr):
        if utxo.output.amount.multi_asset:
            for pid, assets in utxo.output.amount.multi_asset.items():
                if pid.payload.hex() == policy_id_hex:
                    for asset_name, qty in assets.items():
                        if asset_name.payload.hex() == ref_token_hex and qty == 1:
                            ref_info = {
                                "utxo": utxo,
                                "address": str(store_addr),
                                "datum": utxo.output.datum,
                                "amount": utxo.output.amount.coin
                            }
                            break
    
    # Try to find user token by querying blockchain
    # (In production, you'd need to track where user sent it)
    user_info = {
        "note": "User token location unknown (could be in any wallet after transfer)"
    }
    
    return ref_info, user_info


def main():
    parser = argparse.ArgumentParser(description="Query CIP-68 NFT information")
    parser.add_argument("policy_id", help="Policy ID (hex)")
    parser.add_argument("asset_name", help="28-byte asset name suffix (hex)")
    args = parser.parse_args()
    
    print("=" * 70)
    print("CIP-68 NFT Query")
    print("=" * 70)
    
    # Setup
    print("\n[1] Connecting to blockchain...")
    context = BlockFrostChainContext(
        project_id=config.BLOCKFROST_PROJECT_ID,
        network=config.NETWORK,
    )
    
    # Load issuer key to rebuild validators
    from off_chain.mint_nft import generate_or_load_keys
    issuer_skey, issuer_vkey = generate_or_load_keys(config.ISSUER_MNEMONIC_FILE)
    
    issuer_pkh = issuer_vkey.hash()
    
    # Rebuild store validator to get address
    print("\n[2] Rebuilding validators...")
    store_script = utils.apply_params_to_script(
        config.STORE_VALIDATOR_TITLE,
        [issuer_pkh.to_primitive()]
    )
    store_hash = plutus_script_hash(store_script)
    store_addr = Address(store_hash, network=context.network)
    
    print(f"   Store Address: {store_addr}")
    
    # Build token names
    asset_name_suffix = bytes.fromhex(args.asset_name)
    ref_token_name = utils.build_token_name(config.LABEL_100, asset_name_suffix)
    user_token_name = utils.build_token_name(config.LABEL_222, asset_name_suffix)
    
    print(f"\n[3] Token Information:")
    print(f"   Policy ID: {args.policy_id}")
    print(f"   Asset Name Suffix: {args.asset_name}")
    print(f"   Reference Token: {ref_token_name.hex()}")
    print(f"   User Token: {user_token_name.hex()}")
    
    # Find tokens
    print(f"\n[4] Searching for tokens...")
    ref_info, user_info = find_tokens(
        context,
        args.policy_id,
        ref_token_name.hex(),
        user_token_name.hex(),
        store_addr
    )
    
    # Display results
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    
    if ref_info:
        print("\n📍 Reference Token (Label 100):")
        print(f"   ✓ Found at: {ref_info['address']}")
        print(f"   UTxO: {ref_info['utxo'].input.transaction_id}#{ref_info['utxo'].input.index}")
        print(f"   ADA Amount: {ref_info['amount'] / 1_000_000:.6f} ADA")
        
        print("\n📋 Metadata:")
        if ref_info['datum']:
            metadata = decode_metadata_datum(ref_info['datum'])
            print(json.dumps(metadata, indent=2))
        else:
            print("   ⚠ No datum found")
    else:
        print("\n📍 Reference Token (Label 100):")
        print("   ✗ Not found at store address")
        print("   (Token may have been burned or moved)")
    
    print("\n👤 User Token (Label 222):")
    if "note" in user_info:
        print(f"   ℹ {user_info['note']}")
        print(f"   Full asset ID: {args.policy_id}.{user_token_name.hex()}")
        print(f"   Check on explorer or use wallet to locate")
    else:
        print(f"   ✓ Found at: {user_info.get('address', 'unknown')}")
    
    print("\n" + "=" * 70)
    print(f"\n💡 Tip: View full details on Cardano explorer:")
    print(f"   https://preprod.cardanoscan.io/token/{args.policy_id}{ref_token_name.hex()}")
    print("=" * 70)


if __name__ == "__main__":
    main()
