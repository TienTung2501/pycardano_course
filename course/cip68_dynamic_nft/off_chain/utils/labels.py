# filepath: d:\Code\cip68\cip68_v0\cip68-nfts\off-chain-pycardano\utils\labels.py
from typing import Optional

def label_prefix(label: int) -> bytes:
    # 4-byte big-endian per CIP-67
    return label.to_bytes(4, "big")

def build_token_name(label: int, suffix28: bytes) -> bytes:
    assert len(suffix28) == 28
    return label_prefix(label) + suffix28