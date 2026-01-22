"""
Utility functions cho CIP-68 implementation
"""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from pycardano import (
    PlutusV3Script,
    PlutusData,
    PaymentSigningKey,
    PaymentVerificationKey,
    PaymentKeyPair,
    Address,
    Network,
    ExtendedSigningKey,
    ExtendedVerificationKey,
    RawCBOR,
)
from pycardano import crypto
from mnemonic import Mnemonic
import config


def generate_or_load_wallet(filename: str) -> Tuple[ExtendedSigningKey, ExtendedVerificationKey, bytes, Address]:
    """
    Generate hoặc load wallet từ mnemonic file.
    
    Args:
        filename: Tên file mnemonic (e.g., "issuer.mnemonic")
    
    Returns:
        (signing_key, verification_key, payment_key_hash, address)
    """
    mnemonic_file = config.OFF_CHAIN_DIR / filename
    
    if mnemonic_file.exists():
        # Load existing wallet
        with open(mnemonic_file, 'r') as f:
            mnemonic_phrase = f.read().strip()
        print(f"Loading existing wallet from {filename}")
    else:
        # Generate new wallet
        print(f"\nNo wallet found. Generating new wallet...")
        mnemo = Mnemonic("english")
        mnemonic_phrase = mnemo.generate(strength=256)  # 24 words
        
        print(f"\nMnemonic: {mnemonic_phrase}")
        print("\n⚠️  SAVE THIS MNEMONIC SAFELY!")
        print("=" * 60)
        
        # Save to file
        with open(mnemonic_file, 'w') as f:
            f.write(mnemonic_phrase)
        print(f"\nWallet saved to: {mnemonic_file}\n")
    
    # Derive keys from mnemonic using PyCardano's crypto module
    hdwallet = crypto.bip32.HDWallet.from_mnemonic(mnemonic_phrase)
    payment_hdwallet = hdwallet.derive_from_path("m/1852'/1815'/0'/0/0")
    staking_hdwallet = hdwallet.derive_from_path("m/1852'/1815'/0'/2/0")
    
    # Convert to ExtendedSigningKey
    payment_skey = ExtendedSigningKey.from_hdwallet(payment_hdwallet)
    staking_skey = ExtendedSigningKey.from_hdwallet(staking_hdwallet)
    
    # Get verification keys
    payment_vkey = payment_skey.to_verification_key()
    staking_vkey = staking_skey.to_verification_key()
    
    # Get payment key hash
    payment_key_hash = payment_vkey.hash()
    
    # Create address with both payment and staking parts
    network = Network.TESTNET if config.NETWORK_NAME in ["preview", "preprod"] else Network.MAINNET
    address = Address(
        payment_part=payment_vkey.hash(),
        staking_part=staking_vkey.hash(),
        network=network
    )
    
    return payment_skey, payment_vkey, payment_key_hash.to_primitive(), address


def create_or_load_policy_keys():
    """
    Tạo hoặc load policy keys cho Native Script minting.
    Returns: (signing_key, verification_key, key_hash)
    """
    if config.POLICY_SKEY_FILE.exists() and config.POLICY_VKEY_FILE.exists():
        print("Loading existing policy keys...")
        skey = PaymentSigningKey.load(str(config.POLICY_SKEY_FILE))
        vkey = PaymentVerificationKey.load(str(config.POLICY_VKEY_FILE))
    else:
        print("Generating new policy keys...")
        key_pair = PaymentKeyPair.generate()
        skey = key_pair.signing_key
        vkey = key_pair.verification_key
        
        # Save keys
        skey.save(str(config.POLICY_SKEY_FILE))
        vkey.save(str(config.POLICY_VKEY_FILE))
        print(f"  Saved to: {config.POLICY_DIR}")
    
    key_hash = vkey.hash()
    print(f"  Policy Key Hash: {key_hash.to_primitive().hex()}")
    
    return skey, vkey, key_hash


def build_token_name(label: int, name: str) -> bytes:
    """
    Build CIP-68 token name: label_string + name
    
    PPBL approach: concat strings, không dùng 4-byte label
    
    Args:
        label: 100 hoặc 222
        name: token name string
    
    Returns:
        bytes của full token name
    """
    label_str = str(label)
    full_name = label_str + name
    return full_name.encode('utf-8')


def create_cip68_datum(metadata: dict) -> PlutusData:
    """
    Create CIP-68 metadata datum from dictionary.
    
    NOTE: Cardano has 64-byte limit for bytestrings in PlutusData.
    Long descriptions should be truncated or stored off-chain (IPFS).
    """
    import cbor2
    from cbor2 import CBORTag
    
    # Parse attributes
    attributes = []
    if "attributes" in metadata and metadata["attributes"]:
        for attr in metadata["attributes"]:
            trait_type = attr.get("trait_type", "")
            value = str(attr.get("value", ""))
            # Truncate long values
            trait_bytes = trait_type.encode('utf-8')[:64]
            value_bytes = value.encode('utf-8')[:64]
            attributes.append([trait_bytes, value_bytes])
    
    # Parse files
    files = []
    if "files" in metadata and metadata["files"]:
        for f in metadata["files"]:
            files.append(f.encode('utf-8')[:64])
    
    # Truncate fields to 64 bytes
    name = metadata.get("name", "").encode('utf-8')[:64]
    image = metadata.get("image", "").encode('utf-8')[:64]
    description = metadata.get("description", "").encode('utf-8')[:64]
    media_type = metadata.get("media_type", "image/png").encode('utf-8')[:64]
    
    # Build CBOR: Constructor 0
    metadata_cbor = CBORTag(121, [
        name,
        image,
        description,
        attributes,
        media_type,
        files,
    ])
    
    cbor_bytes = cbor2.dumps(metadata_cbor)
    return RawCBOR(cbor_bytes)


def load_plutus_script(validator_title: str) -> PlutusV3Script:
    """Load Plutus script từ blueprint."""
    if not config.PLUTUS_FILE.exists():
        raise FileNotFoundError(
            f"plutus.json not found at {config.PLUTUS_FILE}. "
            "Run 'aiken build' trong contracts directory."
        )
    
    with open(config.PLUTUS_FILE, 'r', encoding='utf-8') as f:
        blueprint = json.load(f)
    
    # Find validator by title
    for validator in blueprint['validators']:
        if validator['title'] == validator_title:
            cbor_hex = validator['compiledCode']
            return PlutusV3Script(bytes.fromhex(cbor_hex))
    
    raise ValueError(f"Validator '{validator_title}' not found in blueprint")


def apply_params_to_script(
    validator_title: str,
    policy_id_hex: str,
) -> PlutusV3Script:
    """
    Apply policy ID parameter to validator using Aiken CLI.
    
    Args:
        validator_title: e.g., "update_metadata.update_metadata.spend"
        policy_id_hex: Policy ID hex string (28 bytes)
    
    Returns:
        Parameterized PlutusV3Script
    """
    import subprocess
    import tempfile
    import cbor2
    
    # Parse validator title to get module and validator name
    # Format: "module.validator.branch" -> module="module", validator="validator"
    parts = validator_title.split('.')
    if len(parts) < 2:
        raise ValueError(f"Invalid validator title '{validator_title}'")
    
    module_name = parts[0]
    validator_name = parts[1]
    
    # Encode policy ID as CBOR bytestring (not constructor!)
    # Just raw bytes for ScriptHash/PolicyId parameter
    policy_id_bytes = bytes.fromhex(policy_id_hex)
    param_cbor_hex = cbor2.dumps(policy_id_bytes).hex()
    
    # Temporary output file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        # Run aiken blueprint apply with correct options
        cmd = [
            'aiken',
            'blueprint',
            'apply',
            '-i', str(config.PLUTUS_FILE),  # Input blueprint
            '-o', tmp_path,                  # Output file
            '-m', module_name,               # Module name
            '-v', validator_name,            # Validator name
            param_cbor_hex,                  # Parameter CBOR hex
        ]
        
        result = subprocess.run(
            cmd,
            cwd=str(config.CONTRACTS_DIR),
            capture_output=True,
            text=True,
            check=False,
        )
        
        if result.returncode != 0:
            raise RuntimeError(
                f"Aiken blueprint apply failed:\n"
                f"Command: {' '.join(cmd)}\n"
                f"Stdout: {result.stdout}\n"
                f"Stderr: {result.stderr}"
            )
        
        # Load parameterized script from output
        with open(tmp_path, 'r', encoding='utf-8') as f:
            blueprint = json.load(f)
        
        # Find the applied validator
        for validator in blueprint['validators']:
            if validator_title in validator['title']:
                cbor_hex = validator['compiledCode']
                return PlutusV3Script(bytes.fromhex(cbor_hex))
        
        raise ValueError(f"Validator '{validator_title}' not found after applying params")
        
    finally:
        # Cleanup
        Path(tmp_path).unlink(missing_ok=True)


def hex_to_string(hex_str: str) -> str:
    """Convert hex string to UTF-8 string."""
    return bytes.fromhex(hex_str).decode('utf-8')


def string_to_hex(s: str) -> str:
    """Convert UTF-8 string to hex."""
    return s.encode('utf-8').hex()
