"""
Utility functions for CIP-68 simple example
"""
import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from pycardano import (
    PlutusV3Script,
    PlutusData,
    plutus_script_hash,
)

import config


def load_plutus_script(validator_title: str) -> PlutusV3Script:
    """Load a Plutus script from the blueprint."""
    with open(config.PLUTUS_FILE, "r") as f:
        blueprint = json.load(f)
    
    # Find validator by title
    for validator in blueprint["validators"]:
        if validator["title"] == validator_title:
            cbor_hex = validator["compiledCode"]
            return PlutusV3Script(bytes.fromhex(cbor_hex))
    
    raise ValueError(f"Validator '{validator_title}' not found in blueprint")


def apply_params_to_script(
    validator_title: str,
    params: List,
) -> PlutusV3Script:
    """
    Apply parameters to a Plutus script using Aiken CLI.
    
    Args:
        validator_title: Full title like "mint_policy.mint_policy.mint"
        params: List of parameters (bytes for hashes, int, or PlutusData objects)
        
    Returns:
        Parameterized PlutusV3Script
    """
    import cbor2
    import tempfile
    
    # Parse validator title: "module.validator.branch"
    parts = validator_title.split(".")
    if len(parts) != 3:
        raise ValueError(f"Invalid validator title format: {validator_title}. Expected 'module.validator.branch'")
    
    module_name, validator_name, branch = parts
    
    # Convert params to CBOR hex strings
    param_cbor_hex_list = []
    for param in params:
        if isinstance(param, bytes):
            # Encode bytes directly
            param_cbor_hex_list.append(cbor2.dumps(param).hex())
        elif isinstance(param, int):
            param_cbor_hex_list.append(cbor2.dumps(param).hex())
        elif isinstance(param, PlutusData):
            param_cbor_hex_list.append(param.to_cbor().hex())
        else:
            raise TypeError(f"Unsupported parameter type: {type(param)}")
    
    # Create temporary output file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        # Apply each parameter sequentially
        current_input = config.PLUTUS_FILE
        for i, param_cbor in enumerate(param_cbor_hex_list):
            # For intermediate steps after first, use previous output as input
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
                "-i", str(current_input),
                "-o", tmp_path,
                "-m", module_name,
                "-v", validator_name,
                param_cbor
            ]
            
            # Run aiken command
            result = subprocess.run(
                cmd,
                cwd=str(config.CONTRACT_DIR),
                capture_output=True,
                text=True,
            )
            
            if result.returncode != 0:
                raise RuntimeError(
                    f"Aiken blueprint apply failed:\n"
                    f"Command: {' '.join(cmd)}\n"
                    f"STDOUT: {result.stdout}\n"
                    f"STDERR: {result.stderr}\n"
                    f"Return code: {result.returncode}"
                )
        
        # Read the final applied blueprint
        with open(tmp_path, 'r') as f:
            blueprint = json.load(f)
        
        # Find the validator
        full_title = f"{module_name}.{validator_name}.{branch}"
        for validator in blueprint.get("validators", []):
            if validator.get("title") == full_title:
                cbor_hex = validator["compiledCode"]
                return PlutusV3Script(bytes.fromhex(cbor_hex))
        
        raise ValueError(f"Applied validator '{full_title}' not found in output blueprint")
        
    finally:
        # Cleanup temp files
        if Path(tmp_path).exists():
            Path(tmp_path).unlink()


def build_token_name(label: int, asset_name_suffix: bytes) -> bytes:
    """
    Build a CIP-68 token name.
    
    Args:
        label: 100 for reference token, 222 for user token
        asset_name_suffix: 28-byte unique identifier
        
    Returns:
        32-byte token name (4-byte label + 28-byte suffix)
    """
    if len(asset_name_suffix) != config.ASSET_NAME_LENGTH:
        raise ValueError(
            f"Asset name suffix must be exactly {config.ASSET_NAME_LENGTH} bytes, "
            f"got {len(asset_name_suffix)}"
        )
    
    # Encode label as 4-byte big-endian integer
    label_bytes = label.to_bytes(4, byteorder='big')
    
    return label_bytes + asset_name_suffix


def create_cip68_datum(metadata: Dict[str, str], author_pkh: bytes = None) -> PlutusData:
    """
    Create CIP-68 metadata datum.
    
    QUAN TRỌNG: Theo CIP-68 và validator logic (như trong Lucid/Mesh implementation),
    datum PHẢI chứa field "_pk" (author key) để validator verify signature.
    
    Args:
        metadata: Dictionary of metadata key-value pairs
        author_pkh: Author/issuer public key hash (REQUIRED for validator checks)
        
    Returns:
        PlutusData object with structure:
        {
            "metadata": [[key1, val1], [key2, val2], ...],
            "version": 1,
            "extra": b""
        }
    """
    @dataclass
    class CIP68Datum(PlutusData):
        CONSTR_ID = 0
        metadata: List[List[bytes]]
        version: int
        extra: bytes
    
    # Convert metadata dict to list of [bytes, bytes] pairs
    metadata_list = []
    
    # QUAN TRỌNG: Thêm "_pk" field TRƯỚC (như trong Lucid/Mesh)
    # Validator kiểm tra field này để verify author signature
    if author_pkh:
        metadata_list.append([b"_pk", author_pkh])
    
    for key, value in metadata.items():
        key_bytes = key.encode('utf-8') if isinstance(key, str) else key
        val_bytes = value.encode('utf-8') if isinstance(value, str) else value
        metadata_list.append([key_bytes, val_bytes])
    
    return CIP68Datum(
        metadata=metadata_list,
        version=1,
        extra=b""
    )
