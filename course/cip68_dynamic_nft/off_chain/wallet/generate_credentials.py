# filepath: d:\Code\cip68\cip68_v0\cip68-nfts\off-chain-pycardano\wallet\generate_credentials.py
import json
from pathlib import Path
from pycardano.crypto.bip32 import HDWallet
from pycardano.key import ExtendedSigningKey, ExtendedVerificationKey
from pycardano.address import Address
from pycardano.hash import VerificationKeyHash
from pycardano.network import Network
from ..common.config import PY_WALLETS_DIR
from ..utils.context import network

def _mk_payment_keys_from_mnemonic(mnemonic: str):
    hd = HDWallet.from_mnemonic(mnemonic)
    # 1852H/1815H/0H/0/0
    hd = hd.derive(1852, hardened=True).derive(1815, hardened=True).derive(0, hardened=True).derive(0).derive(0)
    xsk = ExtendedSigningKey(hd.xprivate_key)
    xvk = ExtendedVerificationKey(xsk.to_verification_key())
    return xsk, xvk

def _addr_from_vkey(xvk: ExtendedVerificationKey) -> Address:
    vkh = VerificationKeyHash.from_verification_key(xvk)
    return Address(payment_part=vkh, network=network())

def main():
    PY_WALLETS_DIR.mkdir(parents=True, exist_ok=True)
    for who in ["issuer", "user"]:
        mnemonic = HDWallet.generate_mnemonic()
        xsk, xvk = _mk_payment_keys_from_mnemonic(mnemonic)
        addr = _addr_from_vkey(xvk)
        out = {
            "mnemonic": mnemonic,
            "xsk_hex": xsk.to_cbor_hex(),
            "xvk_hex": xvk.to_cbor_hex(),
            "address": addr.encode(),
        }
        Path(PY_WALLETS_DIR / f"{who}.json").write_text(json.dumps(out, indent=2))
        print(f"Wrote {who}.json -> {addr.encode()}")

if __name__ == "__main__":
    main()