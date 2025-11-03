#!/usr/bin/env python3
"""
Update CIP-68 NFT Metadata

Updates NFT metadata by spending reference token from validator script.
Requires ownership proof via user token (222).

Usage:
    python update_nft.py --policy-id <ID> --name <NAME> --metadata-file <FILE>
    
Example:
    python update_nft.py --policy-id 1f32f479... --name DragonNFT \
        --metadata-file ../examples/metadata-updated.json

Note: 
    Currently blocked by Conway era protocol parameter issue on Preview testnet.
    Validator logic is correct but awaiting testnet protocol stabilization.
"""
import argparse
import json
from multiprocessing import context
from pycardano import (
    TransactionBuilder,
    TransactionOutput,
    Value,
    MultiAsset,
    Asset,
    AssetName,
    Address,
    plutus_script_hash,
    Redeemer,
    BlockFrostChainContext,
)

import config
from utils.helpers import (
    generate_or_load_wallet,
    build_token_name,
    create_cip68_datum,
    apply_params_to_script,
    sync_protocol_parameters,
    CIP68MetadataPlutus,
    CIP68UpdateRedeemerData,
    CIP68RedeemerUpdate,
)


def main():
    parser = argparse.ArgumentParser(description="Update CIP-68 NFT")
    parser.add_argument("--policy-id", required=True, help="Policy ID (hex)")
    parser.add_argument("--name", required=True, help="Token name (e.g., 'TestNFT001')")
    parser.add_argument("--new-image", help="New image URL")
    parser.add_argument("--new-desc", help="New description")
    parser.add_argument("--metadata-file", help="JSON file with new metadata")
    args = parser.parse_args()
    
    print("=" * 70)
    print("CIP-68 NFT Update")
    print("=" * 70)
    
    # Load new metadata
    if args.metadata_file:
        with open(args.metadata_file, 'r', encoding='utf-8') as f:
            new_metadata = json.load(f)
        print(f"[OK] Loaded metadata from {args.metadata_file}")
    else:
        if not args.new_image or not args.new_desc:
            parser.error("--new-image and --new-desc required when not using --metadata-file")
        new_metadata = {
            "name": args.name,
            "image": args.new_image,
            "description": args.new_desc,
        }
    
    # 1. Connect
    print("\n[1] Connecting to blockchain...")
    context = BlockFrostChainContext(
        project_id=config.BLOCKFROST_PROJECT_ID,
        base_url=config.BLOCKFROST_URL,
    )
    sync_protocol_parameters(context)
    print("    [OK] Protocol parameters đã được đồng bộ chính xác")
    # 2. Load user wallet (who owns the user token)
    print("\n[2] Loading user wallet...")
    user_skey, user_vkey, _, user_addr = generate_or_load_wallet('user.mnemonic')
    print(f"    User: {user_addr}")
    
    # 3. Get script address
    print("\n[3] Getting script address...")
    parameterized_validator = apply_params_to_script(
        config.UPDATE_VALIDATOR_TITLE,
        args.policy_id
    )
    script_hash = plutus_script_hash(parameterized_validator)
    script_addr = Address(script_hash, network=config.NETWORK)
    print(f"    Script: {script_addr}")
    
    # 4. Build token names
    ref_token_name_bytes = build_token_name(config.LABEL_100, args.name)
    user_token_name_bytes = build_token_name(config.LABEL_222, args.name)
    
    ref_token_name = AssetName(ref_token_name_bytes)
    user_token_name = AssetName(user_token_name_bytes)
    
    from pycardano import ScriptHash
    policy_id = ScriptHash.from_primitive(bytes.fromhex(args.policy_id))
    
    # 5. Find reference token UTxO at script
    print("\n[4] Finding reference token at script...")
    script_utxos = context.utxos(script_addr)

    ref_utxo = None
    for utxo in script_utxos:
        if not utxo.output.amount.multi_asset:
            continue
        for pid, assets in utxo.output.amount.multi_asset.items():
            if pid.payload.hex() == args.policy_id:
                for asset_name, qty in assets.items():
                    if asset_name.payload == ref_token_name_bytes:
                        ref_utxo = utxo
                        print(f"    [OK] Found: {utxo.input.transaction_id}#{utxo.input.index}")
                        break
                if ref_utxo:
                    break
        if ref_utxo:
            break

    if not ref_utxo:
        print("    [ERROR] Reference token not found!")
        return
    
    # 6. Find user token UTxO in wallet
    print("\n[5] Finding user token in wallet...")
    user_utxos = context.utxos(user_addr)
    
    user_utxo = None
    for utxo in user_utxos:
        if not utxo.output.amount.multi_asset:
            continue
        for pid, assets in utxo.output.amount.multi_asset.items():
            if pid.payload.hex() == args.policy_id:
                for asset_name, qty in assets.items():
                    if asset_name.payload == user_token_name_bytes:
                        user_utxo = utxo
                        print(f"    [OK] Found: {utxo.input.transaction_id}#{utxo.input.index}")
                        break
                if user_utxo:
                    break
        if user_utxo:
            break

    if not user_utxo:
        print("    [ERROR] User token not found! Cannot prove ownership.")
        return
    
    # 7. Create new datum
    print("\n[6] Creating new metadata...")
    new_datum = create_cip68_datum(new_metadata)
    
    # Display summary
    print(f"    Name:  {new_metadata.get('name', args.name)}")
    print(f"    Image: {new_metadata.get('image', 'N/A')}")
    print(f"    Desc:  {new_metadata.get('description', 'N/A')[:50]}...")
    if 'attributes' in new_metadata:
        print(f"    Attributes: {len(new_metadata['attributes'])} traits")
    
    # 8. Create redeemer
    print("\n[7] Creating redeemer...")
    # Redeemer structure: { new_metadata: CIP68Metadata, token_name: ByteArray }
    metadata_cbor_bytes = new_datum.cbor
    metadata_plutus = CIP68MetadataPlutus.from_cbor(metadata_cbor_bytes)
    redeemer_data = CIP68RedeemerUpdate(
        CIP68UpdateRedeemerData(
            new_metadata=metadata_plutus,
            token_name=args.name.encode('utf-8'),
        )
    )
    redeemer = Redeemer(redeemer_data)
    
    # 9. Build transaction
    print("\n[8] Building update transaction...")
    builder = TransactionBuilder(context)

    ada_only_utxos = sorted(
        (u for u in user_utxos if not u.output.amount.multi_asset),
        key=lambda u: u.output.amount.coin,
        reverse=True,
    )
    if not ada_only_utxos:
        print("    [ERROR] No pure ADA UTxO found for collateral. Please top up wallet.")
        return

    collateral_utxo = ada_only_utxos[0]
    builder.collaterals.append(collateral_utxo)

    fee_utxo = next((u for u in ada_only_utxos if u.input != collateral_utxo.input), None)

    if fee_utxo:
        builder.add_input(fee_utxo)
    else:
        print("    [WARN] Only one ADA-only UTxO available. Reusing collateral UTxO for fees.")
        builder.add_input(collateral_utxo)
    
    # IMPORTANT: Add user token UTxO as input (to prove ownership)
    builder.add_input(user_utxo)
    
    # Spend reference token from script
    builder.add_script_input(ref_utxo, parameterized_validator, None, redeemer)
    
    # Output: reference token back to script with new datum
    builder.add_output(
        TransactionOutput(
            address=script_addr,
            amount=Value(
                coin=config.MIN_ADA_SCRIPT_OUTPUT,
                multi_asset={policy_id: Asset({ref_token_name: 1})}
            ),
            datum=new_datum,
        )
    )
    
    # Output: user token back to user wallet
    builder.add_output(
        TransactionOutput(
            address=user_addr,
            amount=Value(
                coin=config.MIN_ADA_OUTPUT,
                multi_asset={policy_id: Asset({user_token_name: 1})}
            ),
        )
    )
    
    builder.ttl = context.last_block_slot + config.TTL_OFFSET
    
    # 10. Sign and submit
    print("\n[9] Signing transaction...")
    signed_tx = builder.build_and_sign(
        signing_keys=[user_skey],
        change_address=user_addr
    )
    
    print(f"    TX ID: {signed_tx.id}")
    print(f"    Fee: {signed_tx.transaction_body.fee / 1_000_000} ADA")
    
    print("\n[10] Submitting transaction...")
    try:
        tx_hash = context.submit_tx(signed_tx.to_cbor())
        print(f"    [OK] Transaction submitted!")
        print(f"    TX Hash: {tx_hash}")
        print(f"\n    View on explorer:")
        print(f"    https://preprod.cardanoscan.io/transaction/{tx_hash}")
    except Exception as e:
        print(f"    [ERROR] Failed: {e}")
    
    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == "__main__":
    main()
