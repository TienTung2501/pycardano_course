import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from pycardano.plutus import PlutusV2Script, script_hash
from pycardano.hash import ScriptHash
from pycardano.address import Address
from pycardano.network import Network

from ..common.config import PLUTUS_JSON_PATH, BLOCKFROST_NETWORK

# Tên validator đúng theo aiken blueprint (giống hello_world: lấy compiledCode từ plutus.json)
MINT_VALIDATOR_TITLE = "mint.mint_policy.mint"
STORE_VALIDATOR_TITLE = "reference_store.reference_store.spend"

@dataclass
class AppliedMintPolicy:
    script: PlutusV2Script
    policy_id: ScriptHash

@dataclass
class AppliedStoreValidator:
    script: PlutusV2Script
    lock_address: Address
    script_hash: ScriptHash

def _pc_network(net: str) -> Network:
    # PREVIEW/PREPROD đều là TESTNET
    return Network.MAINNET if net.upper() == "MAINNET" else Network.TESTNET

def _load_compiled_code(plutus_json_path: Path, title: str) -> bytes:
    if not plutus_json_path.exists():
        raise FileNotFoundError(f"plutus.json not found at: {plutus_json_path}")
    data = json.loads(plutus_json_path.read_text(encoding="utf-8"))
    vals = data.get("validators") or []
    for v in vals:
        if v.get("title") == title:
            code_hex = v.get("compiledCode") or v.get("compiled_code")
            if not code_hex:
                raise ValueError(f"Validator '{title}' missing compiledCode")
            return bytes.fromhex(code_hex)
    available = [v.get("title") for v in vals]
    raise FileNotFoundError(f"Validator '{title}' not found in {plutus_json_path}. Available: {available}")

def load_applied_mint_policy(plutus_json_path: Optional[Path] = None) -> AppliedMintPolicy:
    p = plutus_json_path or PLUTUS_JSON_PATH
    script_bytes = _load_compiled_code(p, MINT_VALIDATOR_TITLE)
    script = PlutusV2Script(script_bytes)
    pid = script_hash(script)
    return AppliedMintPolicy(script=script, policy_id=pid)

def load_applied_store_validator(
    plutus_json_path: Optional[Path] = None,
    network: Optional[str] = None,
) -> AppliedStoreValidator:
    p = plutus_json_path or PLUTUS_JSON_PATH
    script_bytes = _load_compiled_code(p, STORE_VALIDATOR_TITLE)
    script = PlutusV2Script(script_bytes)
    sh = script_hash(script)
    net = _pc_network(network or BLOCKFROST_NETWORK)
    # Giống hello_world: địa chỉ khóa bởi script hash, không staking part
    lock_addr = Address(payment_part=sh, staking_part=None, network=net)
    return AppliedStoreValidator(script=script, lock_address=lock_addr, script_hash=sh)