# filepath: d:\Code\cip68\cip68_v0\cip68-nfts\off-chain-pycardano\utils\assets.py
from hashlib import blake2b
from typing import Tuple
from pycardano.transaction import UTxO

def derive_suffix_28_from_input(utxo: UTxO) -> bytes:
    # Theo ý tưởng trong TS: dùng tx hash + index, nén 28 bytes
    h = blake2b(digest_size=28)
    h.update(bytes.fromhex(utxo.input.transaction_id.payload.hex()))
    h.update(utxo.input.index.to_bytes(2, "big"))
    return h.digest()

def ensure_index_lt_256(utxo: UTxO) -> bool:
    return utxo.input.index < 256