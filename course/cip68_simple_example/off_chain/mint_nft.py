#!/usr/bin/env python3
"""
Simple CIP-68 NFT Minting Example
This script demonstrates how to mint a CIP-68 NFT pair (reference + user token)
using PyCardano with a clean, straightforward implementation.
Usage:
    python mint_nft.py [--debug] [--no-submit]
"""
import argparse
import hashlib
import time  # Thêm để retry delay
from dataclasses import dataclass
from pathlib import Path
from pycardano import (
    Address,
    BlockFrostChainContext,
    PaymentSigningKey,
    PaymentVerificationKey,
    PlutusData,
    TransactionBuilder,
    TransactionOutput,
    Value,
    PlutusV3Script,
    Redeemer,
    plutus_script_hash,
    script_hash,
    ExtendedSigningKey,
    AssetName,
    Asset,
    MultiAsset,
    ExecutionUnits,
    Transaction,
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

def create_context(network_name: str, project_id: str):
    """Tạo context với network đúng để tránh mismatch."""
    if network_name == "mainnet":
        base_url = "https://cardano-mainnet.blockfrost.io/api"
        network = 0  # Mainnet network magic
    elif network_name == "preprod":
        base_url = "https://cardano-preprod.blockfrost.io/api"
        network = 1
    elif network_name == "preview":
        base_url = "https://cardano-preview.blockfrost.io/api"
        network = 2
    else:
        raise ValueError(f"Unsupported network: {network_name}")
    
    # SỬA: Truyền network param để consistent
    return BlockFrostChainContext(
        project_id=project_id,
        base_url=base_url,
        network=network,  # Thêm dòng này
    )

def main():
    parser = argparse.ArgumentParser(description="Mint CIP-68 NFT")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--no-submit", action="store_true", help="Build but don't submit")
    args = parser.parse_args()
   
    print("=" * 60)
    print("CIP-68 Simple NFT Minting Example")
    print("=" * 60)
   
    # 1. Setup blockchain context
    print("\n[1] Setting up blockchain context...")
    context = create_context(config.NETWORK_NAME, config.BLOCKFROST_PROJECT_ID)  # SỬA: Dùng function để consistent network
   
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
   
    print(f" Issuer PKH: {issuer_pkh.to_primitive().hex()}")
    print(f" User PKH: {user_pkh.to_primitive().hex()}")
    print(f" Issuer Address: {issuer_addr}")
    print(f" User Address: {user_addr}")
   
    # 3. Build validators with parameters
    print("\n[3] Building parameterized validators...")
   
    # Create parameter data structures matching Aiken types
    # StoreParams { issuer_pkh: ByteArray }
    from dataclasses import dataclass
   
    @dataclass
    class StoreParams(PlutusData):
        CONSTR_ID = 0
        issuer_pkh: bytes
   
    # MintParams { store_validator_hash: ByteArray, issuer_pkh: ByteArray }
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
   
    print(f" Store Hash: {store_hash.to_primitive().hex()}")
    print(f" Store Address: {store_addr}")
   
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
   
    print(f" Policy ID: {policy_id.to_primitive().hex()}")
   
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
   
    print(f" Asset name suffix (hex): {asset_name_suffix.hex()}")
    print(f" Ref token name (hex): {ref_token_name_bytes.hex()}")
    print(f" User token name (hex): {user_token_name_bytes.hex()}")
   
    # 5. Create metadata
    print("\n[5] Creating metadata...")
    metadata = {
        "name": "My Simple CIP-68 NFT",
        "description": "A simple CIP-68 NFT created with PyCardano",
        "image": "ipfs://QmExample123456789",
        "artist": "Aiken & PyCardano Tutorial",
    }
   
    datum = utils.create_cip68_datum(metadata)
    print(f" Metadata: {metadata}")
   
    # 6. Build transaction
    print("\n[6] Building transaction...")
   
    # SỬA: Dùng cùng context cho build và submit để tránh mismatch params
    # Fetch fresh params ngay trước build
    print(" Fetching latest protocol params...")
    _ = context.protocol_params()  # Trigger fetch
    
    builder = TransactionBuilder(context)  # Dùng context chung
   
    # Disable automatic execution unit estimation to bypass validation errors
    # Prefer automatic execution unit estimation for correct fees and integrity hash
    builder._should_estimate_execution_units = True
   
    # Add issuer's UTXOs as inputs
    builder.add_input_address(issuer_addr)
   
    # Mint both tokens (use MultiAsset for proper type)
    builder.mint = MultiAsset({
        policy_id: Asset({
            ref_token_name: 1,
            user_token_name: 1,
        })
    })
   
    # Add mint redeemer
    @dataclass
    class MintAction(PlutusData):
        CONSTR_ID = 0 # Mint variant
   
    # Let PyCardano estimate execution units; fallback to generous limits if estimation fails
    mint_redeemer = Redeemer(
        data=MintAction()
    )
    builder.add_minting_script(mint_script, mint_redeemer)
   
    # Output 1: Reference token to store with inline datum
    # SỬA: Tăng min ADA lên 2.5M để buffer fee (giảm rủi ro FeeTooSmall)
    ref_output = TransactionOutput(
        address=store_addr,
        amount=Value(
            coin=2_500_000, # Tăng từ 2M
            multi_asset={policy_id: Asset({ref_token_name: 1})}
        ),
        datum=datum, # Inline datum
    )
    builder.outputs.append(ref_output)
   
    # Output 2: User token to user
    # SỬA: Tăng min ADA lên 2.5M
    user_output = TransactionOutput(
        address=user_addr,
        amount=Value(
            coin=2_500_000, # Tăng từ 2M
            multi_asset={policy_id: Asset({user_token_name: 1})}
        ),
    )
    builder.outputs.append(user_output)
   
    # SỬA: Bỏ user_vkey khỏi required_signers (chỉ issuer mint, user không cần sign lúc này)
    builder.required_signers = [issuer_vkey.hash()]
   
    # Set collateral (need enough for potential script failure)
    issuer_utxos = context.utxos(issuer_addr)
    # Use UTxOs with at least 5 ADA for collateral
    suitable_collateral = [utxo for utxo in issuer_utxos if utxo.output.amount.coin >= 5_000_000]
    if suitable_collateral:
        builder.collaterals = suitable_collateral[:1]
    else:
        # If no large UTxO, use multiple smaller ones
        builder.collaterals = issuer_utxos[:3]
   
    # Build and sign
    # 7. Sign transaction
    print("\n[7] Signing transaction...")
    signed_tx = None
    max_retries = 3  # SỬA: Thêm retry loop để handle PPViewHashesDontMatch
    for attempt in range(max_retries):
        try:
            tx_body = builder.build(change_address=issuer_addr)
            break  # Success
        except Exception as build_err:
            print(f" Build attempt {attempt+1} failed: {build_err}")
            if "PPViewHashesDontMatch" in str(build_err) or "FeeTooSmall" in str(build_err):
                print(" Retrying with fresh params...")
                time.sleep(2)  # Delay 2s để network ổn định
                _ = context.protocol_params()  # Refetch params
                # Reset builder cho retry (clear outputs/scripts để rebuild)
                builder = TransactionBuilder(context)
                builder._should_estimate_execution_units = True
                builder.add_input_address(issuer_addr)
                builder.mint = MultiAsset({
                    policy_id: Asset({
                        ref_token_name: 1,
                        user_token_name: 1,
                    })
                })
                mint_redeemer = Redeemer(data=MintAction())
                builder.add_minting_script(mint_script, mint_redeemer)
                builder.outputs = [ref_output, user_output]  # Re-add outputs
                builder.required_signers = [issuer_vkey.hash()]
                # Re-set collaterals
                issuer_utxos = context.utxos(issuer_addr)
                suitable_collateral = [utxo for utxo in issuer_utxos if utxo.output.amount.coin >= 5_000_000]
                if suitable_collateral:
                    builder.collaterals = suitable_collateral[:1]
                else:
                    builder.collaterals = issuer_utxos[:3]
                continue
            else:
                # Fallback manual nếu không phải params error
                print(" Build failed during execution unit estimation; retrying with manual limits...")
                builder._should_estimate_execution_units = False
                # SỬA: Giảm ex_units để tránh tx size lớn → fee cao
                mint_redeemer = Redeemer(
                    data=MintAction(),
                    ex_units=ExecutionUnits(mem=1_000_000, steps=200_000_000)  # Giảm từ 14M/10B
                )
                builder.mint = MultiAsset({
                    policy_id: Asset({
                        ref_token_name: 1,
                        user_token_name: 1,
                    })
                })
                builder.native_scripts = []
                builder.plutus_scripts = []
                builder._redeemers = []
                builder.add_minting_script(mint_script, mint_redeemer)
                tx_body = builder.build(change_address=issuer_addr)
                break
        if attempt == max_retries - 1:
            raise build_err
   
    # Sign with issuer key only (bỏ user)
    witness_set = builder.build_witness_set()
    witness_set.vkey_witnesses = []
   
    # Add signature
    sig1 = issuer_skey.sign(tx_body.hash())
   
    from pycardano import VerificationKeyWitness
    witness_set.vkey_witnesses.append(VerificationKeyWitness(issuer_vkey, sig1))
   
    signed_tx = Transaction(tx_body, witness_set)
   
    print(f" Transaction ID: {signed_tx.id}")
    print(f" Transaction size: {len(signed_tx.to_cbor())} bytes")
   
    if args.debug:
        print("\n[DEBUG] Transaction CBOR:")
        print(f" {signed_tx.to_cbor().hex()}")
   
    # 8. Submit transaction
    if args.no_submit:
        print("\n[SKIP] Transaction built but not submitted (--no-submit flag)")
        print(f"\n Transaction CBOR (for manual submission):")
        print(f" {signed_tx.to_cbor().hex()}")
    else:
        print("\n[8] Submitting transaction...")
       
        # Save transaction CBOR to file for backup/manual submission
        tx_cbor_file = Path("tx_mint.cbor")
        with open(tx_cbor_file, 'w') as f:
            f.write(signed_tx.to_cbor().hex())
        print(f" Transaction CBOR saved to: {tx_cbor_file}")
       
        try:
            # SỬA: Dùng cùng context để submit, refetch params trước submit
            _ = context.protocol_params()
            tx_hash = context.submit_tx(signed_tx)
            print(f" ✓ Transaction submitted successfully!")
            print(f" TX Hash: {tx_hash}")
            print(f"\n View on explorer:")
            # SỬA: Dynamic explorer URL dựa trên network
            if config.NETWORK_NAME == "mainnet":
                explorer = "https://cardanoscan.io"
            elif config.NETWORK_NAME == "preprod":
                explorer = "https://preprod.cardanoscan.io"
            else:  # preview
                explorer = "https://preview.cardanoscan.io"
            print(f" {explorer}/transaction/{tx_hash}")
           
            print(f"\n Your NFT tokens:")
            print(f" - Reference token: {policy_id.to_primitive().hex()}.{ref_token_name.hex()}")
            print(f" - User token: {policy_id.to_primitive().hex()}.{user_token_name.hex()}")
           
        except Exception as e:
            print(f" ✗ Transaction submission failed:")
            print(f" {e}")
            import traceback
            traceback.print_exc()
            print("\nTips để fix manual:")
            print("1. Kiểm tra protocol params mới nhất: cardano-cli query protocol-parameters --testnet-magic 2")
            print("2. Tăng fee thủ công bằng cách chỉnh tx.raw với cardano-cli (nếu dùng CLI submit)")
            print("3. Đợi 1 epoch nếu params thay đổi lớn.")
   
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

if __name__ == "__main__":
    main()