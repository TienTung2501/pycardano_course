"""
CIP-68 Dynamic Asset - Main Off-chain Operations
================================================
Cung cấp các hàm chính để mint, update metadata, và burn CIP-68 tokens.

Sử dụng PyCardano để xây dựng transactions.

SIMPLIFIED VERSION: Non-parameterized contracts
- Owner stored in datum (portable across devices)
"""
import os
import json
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from blockfrost import ApiError, ApiUrls, BlockFrostApi, BlockFrostIPFS
from pycardano import *

from .cip68_utils import (
    CIP68_REFERENCE_PREFIX,
    CIP68_USER_PREFIX,
    MintToken,
    BurnToken,
    UpdateMetadata,
    BurnReference,
    CIP68Datum,
    create_cip68_asset_names,
    create_cip68_datum,
    get_policy_id,
    get_script_address,
    load_mint_script,
    load_store_script,
    extract_owner_from_datum,
)
# Load environment variables
load_dotenv()

# Hàm tạo BlockFrost chain context
def get_chain_context() -> BlockFrostChainContext:
    """
    Tạo BlockFrost chain context từ environment variables.
    
    Returns:
        BlockFrostChainContext
    """
    network = os.getenv("NETWORK", "Preprod")
    blockfrost_key = os.getenv("BLOCKFROST_PROJECT_ID")

    # Map network (testnet → preview)
    if network == "Preprod":
        blockfrost_url = ApiUrls.preprod.value
    else:
        blockfrost_url = ApiUrls.mainnet.value

    return BlockFrostChainContext(
        project_id=blockfrost_key,
        base_url=blockfrost_url
    )
# Hàm tạo wallet từ seed phrase
def get_wallet_from_seed(seed_phrase: str) -> tuple:
    """
    Tạo wallet từ seed phrase.
    
    Args:
        seed_phrase: 24-word mnemonic
        
    Returns:
        Tuple (payment_skey, payment_vkey, stake_skey, stake_vkey, address)
    """
    hdwallet = crypto.bip32.HDWallet.from_mnemonic(seed_phrase)
    payment_key = hdwallet.derive_from_path(f"m/1852'/1815'/0'/0/0")
    staking_key = hdwallet.derive_from_path(f"m/1852'/1815'/0'/2/0")

    payment_skey = ExtendedSigningKey.from_hdwallet(payment_key)
    stake_skey = ExtendedSigningKey.from_hdwallet(staking_key)

    payment_vkey = payment_skey.to_verification_key()
    stake_vkey = stake_skey.to_verification_key()

    network_str = os.getenv("NETWORK", "Preprod")
    network = Network.TESTNET if network_str.lower() == "preprod" else Network.MAINNET
    address = Address(payment_vkey.hash(), stake_vkey.hash(), network=network)

    return payment_skey, payment_vkey, stake_skey, stake_vkey, address

# Hàm lấy network từ environment
def get_network() -> Network:
    """Get network from environment."""
    network_str = os.getenv("NETWORK", "Preprod")
    return Network.TESTNET if network_str.lower() == "preprod" else Network.MAINNET

# Hàm load scripts và lấy policy ID, store address
def get_scripts(blueprint_path: str = None) -> tuple:
    """
    Load mint and store scripts from blueprint.
    
    Args:
        blueprint_path: Path to plutus.json. If None, uses default path.
        
    Returns:
        Tuple (mint_script, store_script, policy_id, store_address)
    """
    if blueprint_path is None:
        blueprint_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "cip68_dynamic_asset",
            "plutus.json"
        )
    
    mint_script = load_mint_script(blueprint_path)
    store_script = load_store_script(blueprint_path)
    policy_id = get_policy_id(mint_script)
    network = get_network()
    store_address = get_script_address(store_script, network)

    return mint_script, store_script, policy_id, store_address
# Hàm mint CIP-68 token
def mint_cip68_token(
    context: BlockFrostChainContext,
    payment_skey: PaymentSigningKey,
    payment_vkey: PaymentVerificationKey,
    owner_address: Address,
    token_name: str,
    description: str,
    blueprint_path: str = None,
)-> dict:
    """
    Mint một CIP-68 Dynamic NFT.
    
    SIMPLIFIED VERSION: Uses non-parameterized contracts.
    policy_id, asset_name, và owner được lưu trong datum.
    
    Args:
        context: BlockFrost chain context
        payment_skey: Payment signing key
        payment_vkey: Payment verification key
        owner_address: Địa chỉ của owner
        token_name: Tên token (sẽ được thêm prefix)
        description: Mô tả ban đầu của NFT
        blueprint_path: Path to plutus.json (optional)
        
    Returns:
        Dict with tx_hash, policy_id, and asset info
    """

    network = get_network()
    # Load scripts
    mint_script, store_script, policy_id, store_address = get_scripts(blueprint_path)
    # Get owner's public key hash
    owner_pkh = bytes(payment_vkey.hash())

    # Tạo asset names theo CIP-68
    token_name_bytes = token_name.encode('utf-8')
    ref_asset_name, user_asset_name = create_cip68_asset_names(token_name_bytes)

      # Policy ID as bytes for datum
    policy_id_bytes = bytes(policy_id)
     # Tạo CIP68 Datum - lưu policy_id, asset_name, owner
    datum = create_cip68_datum(
        policy_id=policy_id_bytes,
        asset_name=token_name_bytes,
        owner_pkh=owner_pkh,
        metadata=description,
        version=1
    )
    # Tạo MultiAsset cho minting
    mint_asset = Asset()
    mint_asset[ref_asset_name] = 1   # Reference token
    mint_asset[user_asset_name] = 1  # User token
    mint_assets = MultiAsset()
    mint_assets[policy_id] = mint_asset

    # Tạo redeemer
    redeemer = Redeemer(MintToken(token_name=token_name_bytes))

    # Tính reference token output value
    ref_asset = Asset()
    ref_asset[ref_asset_name] = 1
    ref_multi = MultiAsset()
    ref_multi[policy_id] = ref_asset
    ref_value = Value(2_000_000, ref_multi)

    # Build transaction

    builder = TransactionBuilder(context)
    builder.add_input_address(owner_address)
     # Mint tokens
    builder.mint = mint_assets
    builder.add_minting_script(mint_script, redeemer=redeemer)
     # Output: Reference token đến store script với datum
    builder.add_output(
        TransactionOutput(
            store_address,
            ref_value,
            datum=datum,
        )
    )
    # Output: User token đến owner
    user_asset = Asset()
    user_asset[user_asset_name] = 1
    user_multi = MultiAsset()
    user_multi[policy_id] = user_asset
    user_value = Value(2_000_000, user_multi)
    builder.add_output(
        TransactionOutput(
            owner_address,
            user_value,
        )
    )
     # Required signers
    builder.required_signers = [payment_vkey.hash()]
     # Build and sign
    signed_tx = builder.build_and_sign(
        signing_keys=[payment_skey],
        change_address=owner_address
    )
     # Submit
    tx_hash = context.submit_tx(signed_tx)
    print(f"Transaction submitted: {tx_hash}")
    return {
        "tx_hash": str(tx_hash),
        "policy_id": str(policy_id),
        "token_name": token_name,
        "ref_asset_name": ref_asset_name.payload.hex(),
        "user_asset_name": user_asset_name.payload.hex(),
        "store_address": str(store_address),
    }
def update_metadata(
    context: BlockFrostChainContext,
    payment_skey: PaymentSigningKey,
    payment_vkey: PaymentVerificationKey,
    owner_address: Address,
    token_name: str,
    new_description: str,
    blueprint_path: str = None,
) -> dict:
    """
    Update metadata của một CIP-68 NFT.
    
    SIMPLIFIED VERSION: Uses non-parameterized contracts.
    Verifies owner from datum. Giữ nguyên policy_id, asset_name, owner.
    
    Args:
        context: BlockFrost chain context
        payment_skey: Payment signing key
        payment_vkey: Payment verification key  
        owner_address: Địa chỉ của owner
        token_name: Tên token
        new_description: Mô tả mới
        blueprint_path: Path to plutus.json (optional)
        
    Returns:
        Dict with tx_hash and updated info
    """
    network = get_network()

    # Load scripts
    mint_script, store_script, policy_id, store_address = get_scripts(blueprint_path)
     # Get owner's public key hash for verification
    owner_pkh = bytes(payment_vkey.hash())
    # Policy ID as bytes
    policy_id_bytes = bytes(policy_id)
    # Tạo asset name cho reference token
    token_name_bytes = token_name.encode('utf-8')
    ref_asset_name = AssetName(CIP68_REFERENCE_PREFIX + token_name_bytes)

    # Tìm UTxO chứa reference token
    utxos = context.utxos(store_address)
    ref_utxo = None
    for utxo in utxos:
        if utxo.output.amount.multi_asset:
            for pid, assets in utxo.output.amount.multi_asset.items():
                if pid == policy_id and ref_asset_name in assets:
                    ref_utxo = utxo
                    break
    if not ref_utxo:
        raise ValueError("Không tìm thấy reference token UTxO!")
    
    # Xử lý datum để lấy ra pkh owner
    current_datum = ref_utxo.output.datum
    if isinstance(current_datum, CIP68Datum):
        current_owner = extract_owner_from_datum(current_datum)
        if current_owner != owner_pkh:
            raise ValueError("Bạn không phải owner của NFT này!")
        new_version = current_datum.version + 1
    else:
        # Try to parse from raw data
        new_version = 2
    # Tạo datum mới - giữ nguyên policy_id, asset_name, owner
    new_datum = create_cip68_datum(
        policy_id=policy_id_bytes,
        asset_name=token_name_bytes,
        owner_pkh=owner_pkh,
        metadata=new_description,
        version=new_version
    )
    # Tạo redeemer cho spending
    redeemer = Redeemer(UpdateMetadata())

    # Build transaction
    builder = TransactionBuilder(context)
    builder.add_input_address(owner_address)
    # Spend reference token UTxO
    builder.add_script_input(
        ref_utxo,
        store_script,
        redeemer=redeemer
    )
    # Output: Reference token trở lại store script với datum mới
    ref_asset = Asset()
    ref_asset[ref_asset_name] = 1
    ref_multi = MultiAsset()
    ref_multi[policy_id] = ref_asset
    ref_value = Value(
        ref_utxo.output.amount.coin,
        ref_multi
    )
    builder.add_output(
        TransactionOutput(
            store_address,
            ref_value,
            datum=new_datum,
        )
    )
     # Required signers
    builder.required_signers = [payment_vkey.hash()]

     # Build and sign
    signed_tx = builder.build_and_sign(
        signing_keys=[payment_skey],
        change_address=owner_address
    )

    # Submit
    tx_hash = context.submit_tx(signed_tx)
    print(f"Update transaction submitted: {tx_hash}")

    return {
        "tx_hash": str(tx_hash),
        "policy_id": str(policy_id),
        "token_name": token_name,
        "new_version": new_version,
    }

def burn_cip68_token(
    context: BlockFrostChainContext,
    payment_skey: PaymentSigningKey,
    payment_vkey: PaymentVerificationKey,
    owner_address: Address,
    token_name: str,
    blueprint_path: str = None,    
)-> dict:
    """
    Burn một CIP-68 NFT (cả reference token và user token).
    
    SIMPLIFIED VERSION: Uses non-parameterized contracts.
    Verifies owner from datum.
    
    Args:
        context: BlockFrost chain context
        payment_skey: Payment signing key
        payment_vkey: Payment verification key
        owner_address: Địa chỉ của owner
        token_name: Tên token
        blueprint_path: Path to plutus.json (optional)
        
    Returns:
        Dict with tx_hash and burn info
    """
    network = get_network()
     # Load scripts
    mint_script, store_script, policy_id, store_address = get_scripts(blueprint_path)
     # Get owner's public key hash
    owner_pkh = bytes(payment_vkey.hash())
     # Tạo asset names
    token_name_bytes = token_name.encode('utf-8')
    ref_asset_name, user_asset_name = create_cip68_asset_names(token_name_bytes)

    # Tìm UTxO chứa reference token
    store_utxos = context.utxos(store_address)
    ref_utxo = None
    for utxo in store_utxos:
        if utxo.output.amount.multi_asset:
            for pid, assets in utxo.output.amount.multi_asset.items():
                if pid == policy_id and ref_asset_name in assets:
                    ref_utxo = utxo
                    break
    if not ref_utxo:
        raise ValueError("Không tìm thấy reference token UTxO!")
    # Verify owner from datum

    current_datum = ref_utxo.output.datum
    if isinstance(current_datum, CIP68Datum):
        current_owner = extract_owner_from_datum(current_datum)
        if current_owner != owner_pkh:
            raise ValueError("Bạn không phải owner của NFT này!")
        
    # Tìm UTxO chứa user token trong ví owner
    owner_utxos = context.utxos(owner_address)
    user_utxo = None
    for utxo in owner_utxos:
        if utxo.output.amount.multi_asset:
            for pid, assets in utxo.output.amount.multi_asset.items():
                if pid == policy_id and user_asset_name in assets:
                    user_utxo = utxo
                    break
    if not user_utxo:
        raise ValueError("Không tìm thấy user token UTxO!")
    
    # Tạo MultiAsset cho burning (số âm)
    burn_asset = Asset()
    burn_asset[ref_asset_name] = -1   #
    # Burn reference token
    burn_asset[user_asset_name] = -1  # Burn user token
    burn_assets = MultiAsset()
    burn_assets[policy_id] = burn_asset

    # Tạo redeemers
    mint_redeemer = Redeemer(BurnToken(token_name=token_name_bytes))
    spend_redeemer = Redeemer(BurnReference())
    # Build transaction
    builder = TransactionBuilder(context)
    builder.add_input_address(owner_address)
    # Spend reference token UTxO
    builder.add_script_input(
        ref_utxo,
        store_script,
        redeemer=spend_redeemer
    )
     # Add user token input
    builder.add_input(user_utxo)

    # Burn tokens
    builder.mint = burn_assets
    builder.add_minting_script(mint_script, redeemer=mint_redeemer)
    # Required signers
    builder.required_signers = [payment_vkey.hash()]

    # Build and sign
    signed_tx = builder.build_and_sign(
        signing_keys=[payment_skey],
        change_address=owner_address
    )

    # Submit
    tx_hash = context.submit_tx(signed_tx)
    print(f"Burn transaction submitted: {tx_hash}")

    return {
        "tx_hash": str(tx_hash),
        "policy_id": str(policy_id),
        "token_name": token_name,
        "burned": True,
    }
# list token khi cần thiết

def list_all_tokens (context, user_address_str, store_address):
    # Định nghĩa prefix chuẩn theo CIP-68 (dạng bytes)
    REF_PREFIX = bytes.fromhex("000643b0")  # (100)
    USER_PREFIX = bytes.fromhex("000de140") # (222)
    user_tokens_list = []
    holding_token_names = set()

    # BƯỚC 1: Lấy danh sách tên token trong ví User
    user_utxos = context.utxos(user_address_str)
    for utxo in user_utxos:
        for pid, assets in utxo.output.amount.multi_asset.items():
            for asset_name, qty in assets.items():
                if qty > 0 and asset_name.payload.startswith(USER_PREFIX):
                    # Lấy phần tên sau prefix (222)
                    base_name = asset_name.payload[len(USER_PREFIX):]
                    holding_token_names.add(base_name)
    print(f"User đang giữ các base names: {holding_token_names}")
    # BƯỚC 2: Tìm Reference Token tương ứng trong Store
    store_utxos = context.utxos(store_address)
    for utxo in store_utxos:
        for pid, assets in utxo.output.amount.multi_asset.items():
            for asset_name, qty in assets.items():
                if asset_name.payload.startswith(REF_PREFIX):
                     # Lấy phần tên sau prefix (100)
                    base_name = asset_name.payload[len(REF_PREFIX):]
                    if base_name in holding_token_names:
                        # Giải mã Datum
                        try:
                            # Sử dụng PlutusData.from_cbor trực tiếp từ RawCBOR
                            raw_datum = utxo.output.datum
                            if hasattr(raw_datum, 'cbor'):
                                datum = CIP68Datum.from_cbor(raw_datum.cbor)

                            else:
                                datum = CIP68Datum.from_cbor(raw_datum)

                            # Build thông tin trả về
                            meta_dict = {}
                            for k, v in datum.metadata.items():
                                key = k.decode() if isinstance(k, bytes) else str(k)
                                val = v.decode() if isinstance(v, bytes) else str(v)
                                meta_dict[key] = val
                            user_tokens_list.append({
                                "token_name": base_name.decode(),
                                "policy_id": pid.payload.hex(),
                                "metadata": meta_dict,
                                "version": datum.version})
                        except Exception as e:
                            print(f"Lỗi parse datum cho {base_name}: {e}")


    return user_tokens_list


             
if __name__ == "__main__":
    # Test basic functionality
    print("CIP-68 Off-chain module loaded successfully!")
    
    # Load environment
    seed_phrase = os.getenv("SEED_PHRASE")
    if seed_phrase:
        payment_skey, payment_vkey, stake_skey, stake_vkey, address = get_wallet_from_seed(seed_phrase)
        print(f"Wallet address: {address}")
