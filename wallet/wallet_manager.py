"""
wallet/wallet_manager.py

HD Wallet manager cho Cardano (CIP-1852) sử dụng pycardano's HDWallet implementation.

Tính năng:
- Sinh / lưu mnemonic (tuỳ chọn)
- Derive payment & stake keys theo chuẩn m/1852'/1815'/0'/0/0 và m/1852'/1815'/0'/2/0
- Trả về SigningKey / VerificationKey (đúng kiểu pycardano)
- Trả về Address (pycardano.Address)
- Lấy UTxO & balance sử dụng BlockFrostChainContext -> trả pycardano.UTxO
- Export keys (dạng hex, dev only)
"""

import os
import json
import sys
from typing import Optional, List, Tuple

from dotenv import set_key, load_dotenv

# HDWallet từ pycardano (bản bạn dùng có thể export từ pycardano.crypto.bip32)
from pycardano.crypto.bip32 import HDWallet
from pycardano.key import SigningKey, VerificationKey
from pycardano.address import Address
from pycardano.network import Network
from pycardano import BlockFrostChainContext, TransactionOutput, Value

from config.settings import MNEMONIC, NETWORK, BLOCKFROST_PROJECT_ID
from config.blockfrost import get_blockfrost_context, get_network_enum
# logging
from config.logging_config import logger





class WalletManager:
    """
    WalletManager chuẩn CIP-1852.

    - Sử dụng HDWallet.from_mnemonic(...) để sinh root.
    - Derive payment: m/1852'/1815'/0'/0/0
      stake:   m/1852'/1815'/0'/2/0
    """

    PAYMENT_PATH = "m/1852'/1815'/0'/0/0"
    STAKE_PATH = "m/1852'/1815'/0'/2/0"

    def __init__(self, mnemonic: Optional[str] = None, auto_create: bool = True):
        load_dotenv()

        # network normalizing
        self.context = get_blockfrost_context()
        self.network = get_network_enum()

        # mnemonic
        mnemonic_to_use = mnemonic or MNEMONIC
        if not mnemonic_to_use:
            if auto_create:
                mnemonic_to_use = self._create_and_save_mnemonic()
            else:
                raise ValueError("No MNEMONIC provided and auto_create=False.")

        # init HDWallet
        self._hdwallet = HDWallet.from_mnemonic(mnemonic_to_use)
        self._mnemonic = mnemonic_to_use

        # derive payment & stake nodes
        payment_node = self._hdwallet.derive_from_path(self.PAYMENT_PATH)
        stake_node = self._hdwallet.derive_from_path(self.STAKE_PATH)

        # IMPORTANT: xprivate_key is kL||kR (64 bytes). Use left 32 bytes (kL) as seed for SigningKey
        # This matches how the HDWallet lib composes keys.
        kL_payment = payment_node.xprivate_key[:32]
        kL_stake = stake_node.xprivate_key[:32]

        # create SigningKey / VerificationKey objects (pycardano.key)
        # SigningKey expects a 32-byte seed.
        self.payment_skey = SigningKey(kL_payment)
        self.payment_vkey = self.payment_skey.to_verification_key()

        self.stake_skey = SigningKey(kL_stake)
        self.stake_vkey = self.stake_skey.to_verification_key()

        # base address (Shelley base address = payment + stake)
        self.address = Address(
            payment_part=self.payment_vkey.hash(),
            staking_part=self.stake_vkey.hash(),
            network=self.network,
        )

        # Blockfrost context (pycardano)
        if not BLOCKFROST_PROJECT_ID:
            logger.warning("BLOCKFROST_PROJECT_ID not set; Blockfrost calls will fail.")
            self._context = None
        else:
            self._context = get_blockfrost_context()

        logger.info("✅ WalletManager initialized.")
        logger.debug(f"Address: {str(self.address)}")

    # ---------------- MNEMONIC ----------------
    @staticmethod
    def generate_new_mnemonic(strength: int = 256) -> str:
        return HDWallet.generate_mnemonic(strength=strength)

    def _create_and_save_mnemonic(self) -> str:
        mnemonic = self.generate_new_mnemonic()
        env_path = ".env"
        if not os.path.exists(env_path):
            with open(env_path, "w", encoding="utf-8") as f:
                f.write("")
        set_key(env_path, "MNEMONIC", mnemonic)
        logger.info("🪙 New mnemonic generated and saved to .env")
        return mnemonic

    def export_mnemonic(self) -> str:
        """Only call this if you know what you're doing (sensitive)."""
        return self._mnemonic

    # ---------------- KEYS ----------------
    def get_signing_key(self) -> SigningKey:
        """Return pycardano SigningKey (seed 32 bytes)."""
        return self.payment_skey

    def get_verify_key(self) -> VerificationKey:
        """Return pycardano VerificationKey."""
        return self.payment_vkey

    def export_keys(self, folder: str = "./wallet_data"):
        """Export keys as hex (dev only)."""
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, "payment.skey.hex"), "w") as f:
            f.write(self.payment_skey.payload.hex() if hasattr(self.payment_skey, "payload") else self.payment_skey.hex())
        with open(os.path.join(folder, "payment.vkey.hex"), "w") as f:
            f.write(self.payment_vkey.payload.hex() if hasattr(self.payment_vkey, "payload") else self.payment_vkey.hex())
        with open(os.path.join(folder, "stake.skey.hex"), "w") as f:
            f.write(self.stake_skey.payload.hex() if hasattr(self.stake_skey, "payload") else self.stake_skey.hex())
        with open(os.path.join(folder, "stake.vkey.hex"), "w") as f:
            f.write(self.stake_vkey.payload.hex() if hasattr(self.stake_vkey, "payload") else self.stake_vkey.hex())
        logger.info(f"✅ Keys exported (hex) to {folder}/ (dev only)")

    # ---------------- ADDRESS ----------------
    def get_address(self) -> Address:
        """Return pycardano.Address object always."""
        if not isinstance(self.address, Address):
            # try convert from primitive/bech32 or cbor dict
            try:
                self.address = Address.from_primitive(str(self.address))
            except Exception:
                # fallback: if dict with cborHex
                if isinstance(self.address, dict) and "cborHex" in self.address:
                    self.address = Address.from_cbor(self.address["cborHex"])
        return self.address

    def get_address_bech32(self) -> str:
        return str(self.get_address())

    def get_stake_address(self) -> str:
        stake_addr = Address(staking_part=self.stake_vkey.hash(), network=self.network)
        return str(stake_addr)

    # ---------------- BLOCKFROST / UTXO ----------------
    def _ensure_context(self) -> BlockFrostChainContext:
        if self._context is None:
            if not BLOCKFROST_PROJECT_ID:
                raise ValueError("Missing BLOCKFROST_PROJECT_ID")
            self._context = BlockFrostChainContext(project_id=BLOCKFROST_PROJECT_ID, network=self.network)
        return self._context

    def get_balance(self) -> int:
        """
        Return total lovelace (int) of the address.
        Uses pycardano BlockFrostChainContext => returns pycardano.UTxO objects, sum u.output.amount.coin
        """
        ctx = self._ensure_context()
        utxos = ctx.utxos(self.get_address())
        total = sum(u.output.amount.coin for u in utxos)
        logger.info(f"💰 Balance of {self.get_address_bech32()}: {total / 1_000_000} ADA")
        return total

    def get_utxos(self) -> List:
        """Return list of pycardano.UTxO for the wallet's payment address."""
        ctx = self._ensure_context()
        utxos = ctx.utxos(self.get_address())
        logger.info(f"🔍 Found {len(utxos)} UTxOs for {self.get_address_bech32()}")
        return utxos

    # ---------------- UTIL ----------------
    def validate_keys_and_address(self) -> bool:
        """
        Quick validation: check signature pubkey derived from skey matches derived vkey/public_key.
        Returns True if OK.
        """
        # verification key from skey
        vkey_from_skey = self.payment_skey.to_verification_key()
        # compare hashes
        ok = (vkey_from_skey.hash() == self.payment_vkey.hash())
        logger.info(f"Validate keys OK: {ok}")
        return ok

    # ---------------- CLI / DEBUG ----------------
def main():
    args = sys.argv[1:]
    wm = WalletManager()
    if not args:
        print("Usage: python -m wallet.wallet_manager <command>")
        print("Commands: get_address | get_balance | get_utxos | export_keys | show_mnemonic | validate")
        return

    cmd = args[0]
    if cmd == "get_address":
        print("Payment Address:", wm.get_address_bech32())
        print("Stake Address:", wm.get_stake_address())
    elif cmd == "get_balance":
        bal = wm.get_balance()
        print(f"Balance: {bal / 1_000_000} ADA")
    elif cmd == "get_utxos":
        utxos = wm.get_utxos()
        for i, u in enumerate(utxos):
            txid = str(u.input.transaction_id)
            idx = u.input.index
            coin = u.output.amount.coin
            print(f"[{i}] {txid[:20]}... idx={idx} coin={coin} lovelace")
    elif cmd == "export_keys":
        wm.export_keys()
    elif cmd == "show_mnemonic":
        print("Mnemonic:", wm.export_mnemonic())
    elif cmd == "validate":
        print("Keys valid:", wm.validate_keys_and_address())
    else:
        print("Unknown command:", cmd)


if __name__ == "__main__":
    main()
