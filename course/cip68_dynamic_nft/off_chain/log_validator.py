from off_chain.utils.validators import load_applied_mint_policy, load_applied_store_validator
from off_chain.utils.context import network
from off_chain.common.config import MNEMONIC

from pycardano import Address
from pycardano.key import ExtendedSigningKey, ExtendedVerificationKey
from pycardano.crypto.bip32 import HDWallet
from typing import Tuple


def _mk_keys_from_mnemonic(mnemonic: str, idx: int) -> Tuple[ExtendedSigningKey, ExtendedVerificationKey, Address]:
    """
    Tạo cặp khóa (xsk, xvk) và địa chỉ tương ứng từ mnemonic,
    theo chuẩn CIP-1852 (Shelley derivation path).
    Path: m/1852'/1815'/0'/0/{idx}
    """
    hd = HDWallet.from_mnemonic(mnemonic)

    # Payment key
    payment_hd = (
        hd.derive(1852, hardened=True)
        .derive(1815, hardened=True)
        .derive(0, hardened=True)
        .derive(0)
        .derive(idx)
    )

    # Staking key
    staking_hd = (
        hd.derive(1852, hardened=True)
        .derive(1815, hardened=True)
        .derive(0, hardened=True)
        .derive(2)
        .derive(0)
    )

    xsk = ExtendedSigningKey.from_hdwallet(payment_hd)
    xvk = xsk.to_verification_key()

    addr = Address(
        payment_part=xvk.hash(),
        staking_part=ExtendedSigningKey.from_hdwallet(staking_hd)
        .to_verification_key()
        .hash(),
        network=network(),
    )

    return xsk, xvk, addr


def _log_validator():
    """
    In ra thông tin validator (mint policy và store validator).
    """
    mint = load_applied_mint_policy()
    store = load_applied_store_validator()

    print("\n============== VALIDATOR INFO ==============")
    print("[Mint Policy]")
    print(f"  Policy ID     : {mint.policy_id}")

    print("\n[Store Validator]")
    print(f"  Address       : {store.lock_address}")
    print(f"  Script Hash   : {store.script_hash}")
    print("============================================\n")

    return mint, store


if __name__ == "__main__":
    print(">>> Loading validator info...\n")
    mint, store = _log_validator()

    # Derive Issuer (index 0) và User (index 1)
    issuer_xsk, issuer_xvk, issuer_addr = _mk_keys_from_mnemonic(MNEMONIC, 0)
    user_xsk, user_xvk, user_addr = _mk_keys_from_mnemonic(MNEMONIC, 1)

    print("============== WALLET INFO =================")
    print("[Issuer Wallet]")
    print(f"  Address : {issuer_addr}")
    print(f"  PubKey  : {issuer_xvk.hash()}")
    print()
    print("[User Wallet]")
    print(f"  Address : {user_addr}")
    print(f"  PubKey  : {user_xvk.hash()}")
    print("============================================\n")
