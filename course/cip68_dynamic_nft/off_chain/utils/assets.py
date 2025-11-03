import hashlib
from pycardano import TransactionInput, UTxO


def derive_suffix_28_from_input(utxo: UTxO) -> bytes:
    """
    Derive a 28-byte suffix from a UTxO input (CIP-68 standard).
    """
    txid_bytes = utxo.input.transaction_id.payload  # ✅ Lấy từ input
    idx_bytes = utxo.input.index.to_bytes(2, "big")  # ✅ Lấy từ input

    digest = hashlib.blake2b(txid_bytes + idx_bytes, digest_size=28).digest()
    return digest


def ensure_index_lt_256(utxo: UTxO) -> bool:
    """
    Ensure UTxO index < 256 as required by CIP-68.
    """
    return utxo.input.index < 256  # ✅ Lấy index qua input
