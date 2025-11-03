#!/usr/bin/env python3
"""
CIP-68 NFT Minting Script (PPBL Approach)

Mint CIP-68 token pair sử dụng Native Script (signature-based policy).
Đơn giản, dễ hiểu, đã được chứng minh hoạt động.

Usage:
    python mint_nft.py --name "MyNFT" --image "ipfs://..." --desc "Description"
"""
import argparse
import json

from pycardano import (
    Address,
    BlockFrostChainContext,
    TransactionBuilder,
    TransactionOutput,
    Value,
    AssetName,
    Asset,
    MultiAsset,
    ScriptPubkey,
    ScriptAll,
)

import config
from utils.helpers import (
    create_or_load_policy_keys,
    build_token_name,
    create_cip68_datum,
    load_plutus_script,
    generate_or_load_wallet,
)


def main():
    parser = argparse.ArgumentParser(description="Mint CIP-68 NFT")
    parser.add_argument("--name", required=True, help="NFT name (e.g., 'MyNFT001')")
    parser.add_argument("--image", help="Image URL (ipfs://...)")
    parser.add_argument("--desc", help="Description")
    parser.add_argument("--metadata-file", help="JSON file with full metadata (optional)")
    parser.add_argument("--no-submit", action="store_true", help="Build but don't submit")
    args = parser.parse_args()
    
    # Load metadata
    if args.metadata_file:
        with open(args.metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        print(f"[OK] Loaded metadata from {args.metadata_file}")
        # Allow name override
        if args.name:
            metadata['name'] = args.name
        # Show attributes count
        if 'attributes' in metadata:
            print(f"     Attributes: {len(metadata['attributes'])}")
    else:
        # Require --image and --desc if no metadata file
        if not args.image or not args.desc:
            parser.error("--image and --desc are required when --metadata-file is not provided")
        metadata = {
            "name": args.name,
            "image": args.image,
            "description": args.desc,
        }
    
    print("=" * 70)
    print("CIP-68 NFT Minting (PPBL Approach - Native Script)")
    print("=" * 70)
    
    # 1. Setup blockchain context
    print("\n[1] Connecting to Cardano network...")
    context = BlockFrostChainContext(
        project_id=config.BLOCKFROST_PROJECT_ID,
        base_url=config.BLOCKFROST_URL,
    )
    print(f"    Network: {config.NETWORK_NAME}")
    
    # 2. Load/generate wallets
    print("\n[2] Loading wallets...")
    
    issuer_skey, issuer_vkey, _, issuer_addr = generate_or_load_wallet('issuer.mnemonic')
    user_skey, user_vkey, _, user_addr = generate_or_load_wallet('user.mnemonic')
    
    print(f"    Issuer: {issuer_addr}")
    print(f"    User:   {user_addr}")
    
    # 3. Create/load policy keys và build native script
    print("\n[3] Setting up minting policy (Native Script)...")
    policy_skey, policy_vkey, policy_key_hash = create_or_load_policy_keys()
    
    # Build native script: ScriptPubkey → ScriptAll
    pub_key_policy = ScriptPubkey(policy_key_hash)
    native_script = ScriptAll([pub_key_policy])
    policy_id = native_script.hash()
    
    print(f"    Policy ID: {policy_id.to_primitive().hex()}")
    
    # 4. Build token names (PPBL approach: string concat)
    print("\n[4] Building token names...")
    token_name = args.name
    
    ref_token_name_bytes = build_token_name(config.LABEL_100, token_name)
    user_token_name_bytes = build_token_name(config.LABEL_222, token_name)
    
    ref_token_name = AssetName(ref_token_name_bytes)
    user_token_name = AssetName(user_token_name_bytes)
    
    print(f"    Reference token: {ref_token_name_bytes.decode('utf-8')}")
    print(f"    User token:      {user_token_name_bytes.decode('utf-8')}")
    
    # 5. Get script address (cần validator script)
    print("\n[5] Getting validator script address...")
    
    # Load validator (chưa apply params)
    validator = load_plutus_script(config.UPDATE_VALIDATOR_TITLE)
    
    # Apply policy_id parameter
    print("    Applying policy ID parameter to validator...")
    from utils.helpers import apply_params_to_script
    parameterized_validator = apply_params_to_script(
        config.UPDATE_VALIDATOR_TITLE,
        policy_id.to_primitive().hex()
    )
    
    from pycardano import plutus_script_hash
    script_hash = plutus_script_hash(parameterized_validator)
    script_addr = Address(script_hash, network=config.NETWORK)
    
    print(f"    Script address: {script_addr}")
    
    # 6. Create datum
    print("\n[6] Creating CIP-68 metadata...")
    
    # Metadata already loaded in main(), just create datum

    datum = create_cip68_datum(metadata)
    print(f"    Name:  {metadata.get('name')}")
    print(f"    Image: {metadata.get('image')}")
    print(f"    Desc:  {metadata.get('description')[:50]}...")
    if metadata.get('attributes'):
        print(f"    Attributes: {len(metadata['attributes'])} traits")
    
    # 7. Build transaction
    print("\n[7] Building mint transaction...")
    
    builder = TransactionBuilder(context)
    builder.add_input_address(issuer_addr)
    
    # Mint both tokens
    mint_assets = MultiAsset({
        policy_id: Asset({
            ref_token_name: 1,
            user_token_name: 1,
        })
    })
    builder.mint = mint_assets
    
    # Add native script
    builder.native_scripts = [native_script]
    
    # Output 1: Reference token (100) → script address với datum
    builder.add_output(
        TransactionOutput(
            address=script_addr,
            amount=Value(
                coin=config.MIN_ADA_SCRIPT_OUTPUT,
                multi_asset={policy_id: Asset({ref_token_name: 1})}
            ),
            datum=datum,
        )
    )
    
    # Output 2: User token (222) → user wallet
    builder.add_output(
        TransactionOutput(
            address=user_addr,
            amount=Value(
                coin=config.MIN_ADA_OUTPUT,
                multi_asset={policy_id: Asset({user_token_name: 1})}
            ),
        )
    )
    
    # Set TTL
    builder.ttl = context.last_block_slot + config.TTL_OFFSET
    
    # 8. Sign transaction
    print("\n[8] Signing transaction...")
    
    # Sign với issuer và policy key
    signed_tx = builder.build_and_sign(
        signing_keys=[issuer_skey, policy_skey],
        change_address=issuer_addr
    )
    
    print(f"    Transaction ID: {signed_tx.id}")
    print(f"    Size: {len(signed_tx.to_cbor())} bytes")
    print(f"    Fee: {signed_tx.transaction_body.fee / 1_000_000} ADA")
    
    # 9. Submit transaction
    if args.no_submit:
        print("\n[SKIP] Transaction not submitted (--no-submit flag)")
        print(f"\n    CBOR: {signed_tx.to_cbor().hex()}")
    else:
        print("\n[9] Submitting transaction...")
        
        try:
            tx_hash = context.submit_tx(signed_tx.to_cbor())
            print(f"    ✓ Transaction submitted!")
            print(f"    TX Hash: {tx_hash}")
            
            # Explorer URL
            if config.NETWORK_NAME == "mainnet":
                explorer = "https://cardanoscan.io"
            elif config.NETWORK_NAME == "preprod":
                explorer = "https://preprod.cardanoscan.io"
            else:
                explorer = "https://preview.cardanoscan.io"
            
            print(f"\n    View on explorer:")
            print(f"    {explorer}/transaction/{tx_hash}")
            
            print(f"\n    Your CIP-68 NFT:")
            print(f"    - Policy ID: {policy_id.to_primitive().hex()}")
            print(f"    - Reference token: {policy_id.to_primitive().hex()}.{ref_token_name_bytes.hex()}")
            print(f"    - User token:      {policy_id.to_primitive().hex()}.{user_token_name_bytes.hex()}")
            
            print(f"\n    Reference token locked at: {script_addr}")
            print(f"    User token sent to: {user_addr}")
            
        except Exception as e:
            print(f"    ✗ Transaction failed:")
            print(f"    {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == "__main__":
    main()
