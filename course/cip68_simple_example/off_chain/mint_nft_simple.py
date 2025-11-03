#!/usr/bin/env python3
"""
Simple CIP-68 NFT Minting Example (Simplified version following lesson pattern)

This script demonstrates how to mint a CIP-68 NFT pair (reference + user token)
using PyCardano with the same pattern as lesson6/lesson7.

Usage:
    python mint_nft_simple.py [--debug] [--no-submit]
"""
import argparse
import hashlib
from dataclasses import dataclass
from pathlib import Path

from pycardano import (
    Address,
    BlockFrostChainContext,
    ExtendedSigningKey,
    PlutusData,
    TransactionBuilder,
    TransactionOutput,
    Value,
    Redeemer,
    plutus_script_hash,
    script_hash,
    AssetName,
    Asset,
    MultiAsset,
)
from pycardano import crypto

import config
import utils


def generate_or_load_keys(mnemonic_file: Path):
    """Generate new keys or load from mnemonic."""
    if mnemonic_file.exists():
        print(f"Loading keys from {mnemonic_file}")
        with open(mnemonic_file, 'r') as f:
            mnemonic = f.read().strip()
        
        new_wallet = crypto.bip32.HDWallet.from_mnemonic(mnemonic)
        payment_key = new_wallet.derive_from_path("m/1852'/1815'/0'/0/0")
        staking_key = new_wallet.derive_from_path("m/1852'/1815'/0'/2/0")
        
        payment_skey = ExtendedSigningKey.from_hdwallet(payment_key)
        staking_skey = ExtendedSigningKey.from_hdwallet(staking_key)
        
        payment_vkey = payment_skey.to_verification_key()
        staking_vkey = staking_skey.to_verification_key()
    else:
        print(f"Generating new keys and saving to {mnemonic_file}")
        from mnemonic import Mnemonic
        mnemo = Mnemonic("english")
        new_mnemonic = mnemo.generate(strength=256)
        
        with open(mnemonic_file, 'w') as f:
            f.write(new_mnemonic)
        
        new_wallet = crypto.bip32.HDWallet.from_mnemonic(new_mnemonic)
        payment_key = new_wallet.derive_from_path("m/1852'/1815'/0'/0/0")
        staking_key = new_wallet.derive_from_path("m/1852'/1815'/0'/2/0")
        
        payment_skey = ExtendedSigningKey.from_hdwallet(payment_key)
        staking_skey = ExtendedSigningKey.from_hdwallet(staking_key)
        
        payment_vkey = payment_skey.to_verification_key()
        staking_vkey = staking_skey.to_verification_key()
    
    return payment_skey, payment_vkey, staking_skey, staking_vkey


def main():
    parser = argparse.ArgumentParser(description="Mint CIP-68 NFT")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--no-submit", action="store_true", help="Build but don't submit")
    args = parser.parse_args()
    
    print("=" * 60)
    print("CIP-68 Simple NFT Minting Example")
    print("=" * 60)
    
    # 1. Setup blockchain context (theo pattern lesson6/7)
    print("\n[1] Setting up blockchain context...")
    
    # Determine base URL based on network
    if config.NETWORK_NAME == "mainnet":
        base_url = "https://cardano-mainnet.blockfrost.io/api"
    elif config.NETWORK_NAME == "preprod":
        base_url = "https://cardano-preprod.blockfrost.io/api"
    elif config.NETWORK_NAME == "preview":
        base_url = "https://cardano-preview.blockfrost.io/api"
    else:
        raise ValueError(f"Unsupported network: {config.NETWORK_NAME}")
    
    # Tạo context một lần và dùng xuyên suốt
    context = BlockFrostChainContext(
        project_id=config.BLOCKFROST_PROJECT_ID,
        base_url=base_url,
    )
    
    # 2. Load or generate keys
    print("\n[2] Loading keys...")
    issuer_skey, issuer_vkey, issuer_staking_skey, issuer_staking_vkey = generate_or_load_keys(config.ISSUER_MNEMONIC_FILE)
    user_skey, user_vkey, user_staking_skey, user_staking_vkey = generate_or_load_keys(config.USER_MNEMONIC_FILE)
    
    issuer_pkh = issuer_vkey.hash()
    user_pkh = user_vkey.hash()
    
    # Create base addresses (with both payment and staking parts)
    issuer_addr = Address(
        payment_part=issuer_pkh,
        staking_part=issuer_staking_vkey.hash(),
        network=context.network
    )
    user_addr = Address(
        payment_part=user_pkh,
        staking_part=user_staking_vkey.hash(),
        network=context.network
    )
    
    print(f"   Issuer PKH: {issuer_pkh.to_primitive().hex()}")
    print(f"   User PKH: {user_pkh.to_primitive().hex()}")
    print(f"   Issuer Address: {issuer_addr}")
    print(f"   User Address: {user_addr}")
    
    # 3. Build validators with parameters
    print("\n[3] Building parameterized validators...")
    
    # Create parameter data structures matching Aiken types
    @dataclass
    class StoreParams(PlutusData):
        CONSTR_ID = 0
        issuer_pkh: bytes
    
    @dataclass
    class MintParams(PlutusData):
        CONSTR_ID = 0
        store_validator_hash: bytes
        issuer_pkh: bytes
    
    # First, build store validator (needs only issuer_pkh)
    store_params = StoreParams(issuer_pkh=issuer_pkh.to_primitive())
    store_script = utils.apply_params_to_script(
        config.STORE_VALIDATOR_TITLE,
        [store_params]
    )
    store_hash = plutus_script_hash(store_script)
    store_addr = Address(store_hash, network=context.network)
    
    print(f"   Store Hash: {store_hash.to_primitive().hex()}")
    print(f"   Store Address: {store_addr}")
    
    # Now build mint policy (needs store_hash and issuer_pkh)
    mint_params = MintParams(
        store_validator_hash=store_hash.to_primitive(),
        issuer_pkh=issuer_pkh.to_primitive()
    )
    mint_script = utils.apply_params_to_script(
        config.MINT_VALIDATOR_TITLE,
        [mint_params]
    )
    policy_id = script_hash(mint_script)
    
    print(f"   Policy ID: {policy_id.to_primitive().hex()}")
    
    # 4. Create token names
    print("\n[4] Creating token names...")
    
    # Generate unique 28-byte asset name from a hash
    asset_base = b"MyFirstCIP68NFT_001"
    asset_name_suffix = hashlib.sha256(asset_base).digest()[:config.ASSET_NAME_LENGTH]
    
    ref_token_name_bytes = utils.build_token_name(config.LABEL_100, asset_name_suffix)
    user_token_name_bytes = utils.build_token_name(config.LABEL_222, asset_name_suffix)
    
    # Convert to AssetName for PyCardano
    ref_token_name = AssetName(ref_token_name_bytes)
    user_token_name = AssetName(user_token_name_bytes)
    
    print(f"   Asset name suffix (hex): {asset_name_suffix.hex()}")
    print(f"   Ref token name (hex): {ref_token_name_bytes.hex()}")
    print(f"   User token name (hex): {user_token_name_bytes.hex()}")
    
    # 5. Create metadata
    print("\n[5] Creating metadata...")
    metadata = {
        "name": "My Simple CIP-68 NFT",
        "description": "A simple CIP-68 NFT created with PyCardano",
        "image": "ipfs://QmExample123456789",
        "artist": "Aiken & PyCardano Tutorial",
    }
    
    # QUAN TRỌNG: Truyền issuer_pkh vào datum (theo Lucid/Mesh implementation)
    # Validator sẽ verify field "_pk" này
    datum = utils.create_cip68_datum(metadata, author_pkh=issuer_pkh.to_primitive())
    print(f"   Metadata: {metadata}")
    print(f"   Author PKH in datum: {issuer_pkh.to_primitive().hex()}")
    
    # 6. Build transaction (theo pattern lesson6/7 - ĐƠN GIẢN)
    print("\n[6] Building transaction...")
    
    builder = TransactionBuilder(context)
    
    # Add issuer's UTXOs as inputs (builder tự chọn UTxO phù hợp)
    builder.add_input_address(issuer_addr)
    
    # Mint both tokens (use MultiAsset for proper type)
    my_nft = MultiAsset({
        policy_id: Asset({
            ref_token_name: 1,
            user_token_name: 1,
        })
    })
    builder.mint = my_nft
    
    # Add mint script with redeemer
    @dataclass
    class MintAction(PlutusData):
        CONSTR_ID = 0  # Mint variant
    
    mint_redeemer = Redeemer(data=MintAction())
    builder.add_minting_script(mint_script, mint_redeemer)
    
    # Output 1: Reference token to store with inline datum
    # Tăng ADA lên >2.05M để đáp ứng min UTxO requirement với datum lớn
    ref_output = TransactionOutput(
        address=store_addr,
        amount=Value(
            coin=2_100_000,  # Tăng từ 2M lên 2.1M (blockchain yêu cầu 2,051,560)
            multi_asset={policy_id: Asset({ref_token_name: 1})}
        ),
        datum=datum,  # Inline datum
    )
    builder.add_output(ref_output)
    
    # Output 2: User token to user
    user_output = TransactionOutput(
        address=user_addr,
        amount=Value(
            coin=2_000_000,  # Min ADA
            multi_asset={policy_id: Asset({user_token_name: 1})}
        ),
    )
    builder.add_output(user_output)
    
    # Add required signers
    builder.required_signers = [issuer_vkey.hash()]
    
    # Set collateral (cần cho Plutus script)
    issuer_utxos = context.utxos(issuer_addr)
    suitable_collateral = [utxo for utxo in issuer_utxos if utxo.output.amount.coin >= 5_000_000]
    if suitable_collateral:
        builder.collaterals = suitable_collateral[:1]
    else:
        builder.collaterals = issuer_utxos[:3]
    
    # Set TTL
    builder.ttl = context.last_block_slot + 1000
    
    # 7. Build and sign (THEO PATTERN LESSON6/7 - MỘT BƯỚC DUY NHẤT)
    print("\n[7] Building and signing transaction...")
    
    try:
        signed_tx = builder.build_and_sign(
            signing_keys=[issuer_skey],
            change_address=issuer_addr
        )
    except Exception as e:
        print(f"   Build/sign failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print(f"   Transaction ID: {signed_tx.id}")
    print(f"   Transaction size: {len(signed_tx.to_cbor())} bytes")
    print(f"   Fee: {signed_tx.transaction_body.fee / 1_000_000} ADA")
    
    if args.debug:
        print("\n[DEBUG] Transaction CBOR:")
        print(f"   {signed_tx.to_cbor().hex()}")
    
    # 8. Submit transaction
    if args.no_submit:
        print("\n[SKIP] Transaction built but not submitted (--no-submit flag)")
        print(f"\n   Transaction CBOR (for manual submission):")
        print(f"   {signed_tx.to_cbor().hex()}")
    else:
        print("\n[8] Submitting transaction...")
        
        # Save transaction CBOR to file
        tx_cbor_file = Path("tx_mint.cbor")
        with open(tx_cbor_file, 'w') as f:
            f.write(signed_tx.to_cbor().hex())
        print(f"   Transaction CBOR saved to: {tx_cbor_file}")
        
        try:
            tx_hash = context.submit_tx(signed_tx.to_cbor())
            print(f"   ✓ Transaction submitted successfully!")
            print(f"   TX Hash: {tx_hash}")
            
            # Explorer URL
            if config.NETWORK_NAME == "mainnet":
                explorer = "https://cardanoscan.io"
            elif config.NETWORK_NAME == "preprod":
                explorer = "https://preprod.cardanoscan.io"
            else:
                explorer = "https://preview.cardanoscan.io"
            
            print(f"\n   View on explorer:")
            print(f"   {explorer}/transaction/{tx_hash}")
            
            print(f"\n   Your NFT tokens:")
            print(f"   - Reference token: {policy_id.to_primitive().hex()}.{ref_token_name.hex()}")
            print(f"   - User token: {policy_id.to_primitive().hex()}.{user_token_name.hex()}")
            
        except Exception as e:
            print(f"   [x] Transaction submission failed:")
            print(f"   {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
