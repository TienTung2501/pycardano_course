import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List
import subprocess
import tempfile
import os

from pycardano import PlutusV3Script, Address
from pycardano.hash import ScriptHash, VerificationKeyHash
from pycardano.plutus import plutus_script_hash
from pycardano.network import Network

from ..common.config import PLUTUS_JSON_PATH, BLOCKFROST_NETWORK


# === Helper: encode hash as Plutus Data CBOR ===
def hash_to_plutus_data_cbor(hash_bytes: bytes) -> str:
    """
    Encode a hash (28 bytes) as CBOR hex-encoded Plutus Data bytestring.
    
    Plutus Data bytestring format: CBOR byte string
    For 28-byte hash: 0x581C (major type 2, length 28) + hex data
    
    Args:
        hash_bytes: 28-byte hash
    
    Returns:
        Hex string of CBOR-encoded bytestring
    """
    import cbor2
    # CBOR encode a bytestring
    cbor_bytes = cbor2.dumps(hash_bytes)
    return cbor_bytes.hex()


# === Helper: apply_params_to_script using Aiken CLI ===
def apply_params_to_script_via_aiken(
    plutus_json_path: Path,
    validator_title: str,
    param_cbor_hex_list: List[str]
) -> bytes:
    """
    Apply parameters to a validator using Aiken CLI.
    
    Args:
        plutus_json_path: Path to plutus.json
        validator_title: Validator title like "module.validator" (e.g., "mint.mint_policy")
        param_cbor_hex_list: List of CBOR hex-encoded Plutus Data parameters
    
    Returns:
        bytes: Applied script CBOR
    """
    # Parse module and validator from title
    # Format: "module.validator" or "module.validator.branch"
    parts = validator_title.split('.')
    if len(parts) < 2:
        raise ValueError(f"Invalid validator title '{validator_title}'. Expected format: 'module.validator' or 'module.validator.branch'")
    
    # Take first 2 parts as module.validator for Aiken CLI
    module_name = parts[0]
    validator_name = parts[1]
    
    # Create temporary output file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        contract_dir = plutus_json_path.parent
        
        # Apply each parameter sequentially
        current_input = plutus_json_path
        for i, param_cbor in enumerate(param_cbor_hex_list):
            # For intermediate steps, create temp input
            if i > 0:
                intermediate_tmp = tempfile.NamedTemporaryFile(
                    mode='w', suffix='.json', delete=False
                )
                intermediate_tmp.close()
                current_input = Path(intermediate_tmp.name)
                # Copy previous output to current input
                with open(tmp_path, 'r') as src, open(current_input, 'w') as dst:
                    dst.write(src.read())
            
            # Build aiken blueprint apply command
            cmd = [
                "aiken",
                "blueprint",
                "apply",
                "-i", str(current_input) if i > 0 else str(plutus_json_path),
                "-o", tmp_path,
                "-m", module_name,
                "-v", validator_name,
                param_cbor
            ]
            
            # Run aiken command
            result = subprocess.run(
                cmd,
                cwd=str(contract_dir),
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                raise RuntimeError(
                    f"Aiken blueprint apply failed (parameter {i+1}):\n"
                    f"Command: {' '.join(cmd)}\n"
                    f"Stdout: {result.stdout}\n"
                    f"Stderr: {result.stderr}"
                )
            
            # Clean up intermediate input
            if i > 0 and current_input != plutus_json_path:
                os.unlink(current_input)
        
        # Read applied validator from final output file
        applied_data = json.loads(Path(tmp_path).read_text(encoding="utf-8"))
        
        # Extract compiledCode from applied blueprint
        validators = applied_data.get("validators", [])
        if not validators:
            raise ValueError("No validators found in applied blueprint")
        
        # Get first validator's compiledCode
        compiled_code_hex = validators[0].get("compiledCode")
        if not compiled_code_hex:
            raise ValueError("No compiledCode in applied validator")
        
        return bytes.fromhex(compiled_code_hex)
        
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


from ..common.config import PLUTUS_JSON_PATH, BLOCKFROST_NETWORK


# === Constants: Tên validator trong blueprint Aiken ===
# Note: Blueprint có format "module.validator.branch" nhưng Aiken CLI chỉ cần "module.validator"
MINT_VALIDATOR_TITLE = "mint.mint_policy.mint"  # Full title để load từ blueprint
STORE_VALIDATOR_TITLE = "reference_store.reference_store.spend"  # Full title để load từ blueprint


# === Data Classes ===
@dataclass
class AppliedMintPolicy:
    """Đại diện cho minting policy script (CIP-68 mint)."""
    script: PlutusV3Script
    policy_id: ScriptHash


@dataclass
class AppliedStoreValidator:
    """Đại diện cho validator script để lưu dữ liệu (CIP-68 store)."""
    script: PlutusV3Script
    lock_address: Address
    script_hash: ScriptHash


# === Helper Functions ===
def _pc_network(net: str) -> Network:
    """Chuyển tên mạng (MAINNET / PREVIEW / PREPROD) sang enum của pycardano."""
    return Network.MAINNET if net.upper() == "MAINNET" else Network.TESTNET


def _load_compiled_code(plutus_json_path: Path, title: str) -> bytes:
    """Đọc compiledCode từ blueprint (plutus.json) theo title."""
    if not plutus_json_path.exists():
        raise FileNotFoundError(f"plutus.json not found at: {plutus_json_path}")

    data = json.loads(plutus_json_path.read_text(encoding="utf-8"))
    validators = data.get("validators") or []

    for v in validators:
        if v.get("title") == title:
            code_hex = v.get("compiledCode") or v.get("compiled_code")
            if not code_hex:
                raise ValueError(f"Validator '{title}' missing compiledCode")
            return bytes.fromhex(code_hex)

    available = [v.get("title") for v in validators]
    raise FileNotFoundError(
        f"Validator '{title}' not found in {plutus_json_path}. "
        f"Available validators: {available}"
    )


# === Public Loader Functions ===
def load_applied_mint_policy(
    issuer_vkh: VerificationKeyHash,
    store_script_hash: ScriptHash,
    plutus_json_path: Optional[Path] = None
) -> AppliedMintPolicy:
    """Load và tạo AppliedMintPolicy từ plutus.json, apply parameters (issuer, store) via Aiken CLI."""
    path = plutus_json_path or PLUTUS_JSON_PATH
    
    # Encode parameters as Plutus Data CBOR
    issuer_cbor = hash_to_plutus_data_cbor(issuer_vkh.payload)
    store_cbor = hash_to_plutus_data_cbor(store_script_hash.payload)
    
    # Apply parameters via Aiken CLI
    applied_cbor = apply_params_to_script_via_aiken(
        plutus_json_path=path,
        validator_title=MINT_VALIDATOR_TITLE,
        param_cbor_hex_list=[issuer_cbor, store_cbor]
    )
    
    applied_script = PlutusV3Script(applied_cbor)
    policy_id = plutus_script_hash(applied_script)
    return AppliedMintPolicy(script=applied_script, policy_id=policy_id)


def load_applied_store_validator(
    issuer_vkh: VerificationKeyHash,
    plutus_json_path: Optional[Path] = None,
    network: Optional[str] = None,
) -> AppliedStoreValidator:
    """Load và tạo AppliedStoreValidator từ plutus.json, apply parameter (issuer) via Aiken CLI."""
    path = plutus_json_path or PLUTUS_JSON_PATH
    
    # Encode parameter as Plutus Data CBOR
    issuer_cbor = hash_to_plutus_data_cbor(issuer_vkh.payload)
    
    # Apply parameter via Aiken CLI
    applied_cbor = apply_params_to_script_via_aiken(
        plutus_json_path=path,
        validator_title=STORE_VALIDATOR_TITLE,
        param_cbor_hex_list=[issuer_cbor]
    )
    
    applied_script = PlutusV3Script(applied_cbor)
    script_hash = plutus_script_hash(applied_script)
    net = _pc_network(network or BLOCKFROST_NETWORK)
    lock_address = Address(payment_part=script_hash, staking_part=None, network=net)

    return AppliedStoreValidator(script=applied_script, lock_address=lock_address, script_hash=script_hash)
