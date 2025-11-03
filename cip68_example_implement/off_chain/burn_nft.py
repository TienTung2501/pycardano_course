#!/usr/bin/env python3
"""
Burn CIP-68 NFT

Burns user token (222) using native script minting policy.
Note: Reference token (100) requires validator script to burn from script address.

Usage:
    python burn_nft.py --policy-id <POLICY_ID> --name <TOKEN_NAME>
    
Example:
    python burn_nft.py --policy-id 1f32f479... --name DragonNFT
"""
import argparse
from pycardano import (
    TransactionBuilder,
    TransactionOutput,
    Value,
    MultiAsset,
    Asset,
    AssetName,
    Address,
    ScriptAll,
    ScriptPubkey,
    BlockFrostChainContext,
    Redeemer,
    plutus_script_hash,
)

import config
from utils.helpers import (
    generate_or_load_wallet,
    build_token_name,
    create_or_load_policy_keys,
    apply_params_to_script,
    sync_protocol_parameters,
    CIP68RedeemerBurn,
)


def main():
    parser = argparse.ArgumentParser(description="Burn CIP-68 NFT")
    parser.add_argument("--policy-id", required=True, help="Policy ID (hex)")
    parser.add_argument("--name", required=True, help="Token name (e.g., 'TestNFT001')")
    args = parser.parse_args()
    
    print("=" * 70)
    print("CIP-68 NFT Burn")
    print("=" * 70)
    
    # 1. Connect
    print("\n[1] Connecting...")
    context = BlockFrostChainContext(
        project_id=config.BLOCKFROST_PROJECT_ID,
        base_url=config.BLOCKFROST_URL,
    )
    sync_protocol_parameters(context)
    print("    [OK] Protocol parameters đã được đồng bộ chính xác")
    
    # 2. Load issuer wallet (who has policy key)
    print("\n[2] Loading issuer wallet...")
    issuer_skey, issuer_vkey, _, issuer_addr = generate_or_load_wallet('issuer.mnemonic')
    print(f"    Issuer: {issuer_addr}")
    
    # 3. Load policy keys
    print("\n[3] Loading policy keys...")
    policy_skey, policy_vkey, policy_key_hash = create_or_load_policy_keys()
    
    # Build native script
    pub_key_policy = ScriptPubkey(policy_key_hash)
    native_script = ScriptAll([pub_key_policy])
    policy_id_check = native_script.hash()
    print(f"    Policy ID: {policy_id_check.to_primitive().hex()}")
    
    # 4. Build token names
    ref_token_name_bytes = build_token_name(config.LABEL_100, args.name)
    user_token_name_bytes = build_token_name(config.LABEL_222, args.name)
    
    ref_token_name = AssetName(ref_token_name_bytes)
    user_token_name = AssetName(user_token_name_bytes)
    
    from pycardano import ScriptHash
    policy_id = ScriptHash.from_primitive(bytes.fromhex(args.policy_id))
    
    print(f"    Burning: {ref_token_name_bytes.hex()} and {user_token_name_bytes.hex()}")
    
    # 5. Find reference token at script (need to spend it first!)
    print("\n[4] Finding reference token at script...")
    parameterized_validator = apply_params_to_script(
        config.UPDATE_VALIDATOR_TITLE,
        args.policy_id
    )
    script_hash = plutus_script_hash(parameterized_validator)
    script_addr = Address(script_hash, network=config.NETWORK)
    
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
                        print(f"    [OK] Found at script")
                        break
                if ref_utxo:
                    break
        if ref_utxo:
            break
    
    if not ref_utxo:
        print("    [ERROR] Reference token not found at script - nothing to burn")
        return

    # 6. Find user token at wallet
    print("\n[5] Finding user token at wallet...")
    user_skey, user_vkey, _, user_addr = generate_or_load_wallet('user.mnemonic')
    
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
                        print(f"    [OK] Found in wallet")
                        break
                if user_utxo:
                    break
        if user_utxo:
            break
    
    # 7. Build burn transaction
    print("\n[6] Building burn transaction...")
    if not user_utxo:
        print("    [ERROR] User token not found!")
        return

    builder = TransactionBuilder(context)

    ada_only_utxos = sorted(
        (u for u in user_utxos if not u.output.amount.multi_asset),
        key=lambda u: u.output.amount.coin,
        reverse=True,
    )
    if not ada_only_utxos:
        print("    [ERROR] No pure ADA UTxO available for collateral.")
        return

    collateral_utxo = ada_only_utxos[0]
    builder.collaterals.append(collateral_utxo)

    fee_utxo = next((u for u in ada_only_utxos if u.input != collateral_utxo.input), None)

    if fee_utxo:
        builder.add_input(fee_utxo)
    else:
        print("    [WARN] Only one ADA-only UTxO available. Reusing collateral UTxO for fees.")
        builder.add_input(collateral_utxo)

    # Add user token input explicitly (for ownership proof)
    builder.add_input(user_utxo)

    # Spend reference token from script with burn redeemer
    redeemer = Redeemer(CIP68RedeemerBurn(args.name.encode('utf-8')))
    builder.add_script_input(ref_utxo, parameterized_validator, None, redeemer)

    # Burn both reference (100) and user (222) tokens
    burn_assets = MultiAsset({
        policy_id: Asset({
            ref_token_name: -1,
            user_token_name: -1,
        })
    })
    builder.mint = burn_assets
    builder.native_scripts = [native_script]

    # Return previously locked ADA to user wallet
    builder.add_output(
        TransactionOutput(
            address=user_addr,
            amount=Value(coin=ref_utxo.output.amount.coin),
        )
    )

    builder.ttl = context.last_block_slot + config.TTL_OFFSET
    
    # 8. Sign and submit
    print("\n[7] Signing transaction...")
    signed_tx = builder.build_and_sign(
        signing_keys=[policy_skey, user_skey],
        change_address=user_addr
    )
    
    print(f"    TX ID: {signed_tx.id}")
    print(f"    Fee: {signed_tx.transaction_body.fee / 1_000_000} ADA")
    
    print("\n[8] Submitting transaction...")
    try:
        tx_hash = context.submit_tx(signed_tx.to_cbor())
        print(f"    [OK] Transaction submitted!")
        print(f"    TX Hash: {tx_hash}")
        print(f"\n    Burned reference token (100) và user token (222)")
    except Exception as error:
        print(f"    [ERROR] Failed: {error}")
    
    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == "__main__":
    main()
