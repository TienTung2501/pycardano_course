"""
wallet/wallet_manager.py
------------------------
Quản lý HD Wallet trên Cardano (testnet/mainnet) bằng PyCardano + Blockfrost.
- Hỗ trợ tạo ví, xuất khóa, kiểm tra balance, UTxO.
- Chuẩn CIP-1852 (m/1852'/1815'/0'/0/0).
"""

import os
import sys
from typing import Optional, List
from pycardano.crypto.bip32 import HDWallet
from pycardano.key import VerificationKey, SigningKey
from pycardano.address import Address
from pycardano.network import Network


from blockfrost import BlockFrostApi, ApiError, ApiUrls
from config.settings import MNEMONIC, NETWORK, BLOCKFROST_PROJECT_ID


class WalletManager:
    """HD Wallet đầy đủ cho Cardano (payment + stake)."""

    def __init__(self, mnemonic: Optional[str] = None):
        mnemonic_to_use = mnemonic or MNEMONIC
        if not mnemonic_to_use:
            raise ValueError("❌ Chưa có MNEMONIC trong .env hoặc tham số.")

        # Tạo HDWallet
        self.wallet = HDWallet.from_mnemonic(mnemonic_to_use)

        # Payment key (path m/1852'/1815'/0'/0/0)
        payment_path = "m/1852'/1815'/0'/0/0"
        payment_wallet = self.wallet.derive_from_path(payment_path)
        self.payment_skey = SigningKey(payment_wallet.xprivate_key[:64])
        self.payment_vkey = VerificationKey(payment_wallet.public_key)

        # Stake key (path m/1852'/1815'/0'/2/0)
        stake_path = "m/1852'/1815'/0'/2/0"
        stake_wallet = self.wallet.derive_from_path(stake_path)
        self.stake_skey = SigningKey(stake_wallet.xprivate_key[:64])
        self.stake_vkey = VerificationKey(stake_wallet.public_key)

        # Base address (Shelley)
        self.address = Address(
            payment_part=self.payment_vkey.hash(),
            staking_part=self.stake_vkey.hash(),
            network=NETWORK
        )

    # ---------- MNEMONIC ----------
    @staticmethod
    def generate_new_mnemonic(strength: int = 256) -> str:
        """Sinh mnemonic ngẫu nhiên (24 từ nếu strength=256)."""
        return HDWallet.generate_mnemonic(strength=strength)

    def export_mnemonic(self) -> str:
        """Trả về mnemonic hiện tại (bảo mật)."""
        return self.wallet._mnemonic

    # ---------- KEYS ----------
    def get_signing_key(self) -> SigningKey:
        return self.payment_skey

    def get_verify_key(self) -> VerificationKey:
        return self.payment_vkey

    def export_keys(self, folder: str = "./wallet_data"):
        """Xuất khóa ra file .key (chỉ dùng test/dev)."""
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, "payment.skey"), "w") as f:
            f.write(self.payment_skey.hex())
        with open(os.path.join(folder, "payment.vkey"), "w") as f:
            f.write(self.payment_vkey.hex())
        with open(os.path.join(folder, "stake.skey"), "w") as f:
            f.write(self.stake_skey.hex())
        with open(os.path.join(folder, "stake.vkey"), "w") as f:
            f.write(self.stake_vkey.hex())
        print(f"✅ Đã lưu khóa ví tại {folder}/")

    # ---------- ADDRESS ----------
    def get_address(self) -> Address:
        return self.address

    def get_address_bech32(self) -> str:
        return str(self.address)

    def get_stake_address(self) -> str:
        """Trả về stake address (bech32)."""
        stake_addr = Address(
            staking_part=self.stake_vkey.hash(),
            network=NETWORK
        )
        return str(stake_addr)

    # ---------- BLOCKFROST ----------
    def _get_blockfrost_api(self) -> BlockFrostApi:
        """Khởi tạo kết nối Blockfrost API theo mạng đang cấu hình."""
        if not BLOCKFROST_PROJECT_ID:
            raise ValueError("❌ Thiếu BLOCKFROST_PROJECT_ID trong .env")

        # Lựa chọn URL chính xác theo network
        if NETWORK == Network.TESTNET:
            # Có thể là preview hoặc preprod, tùy bạn đang dùng project_id nào
            # Gợi ý: đặt thêm biến BLOCKFROST_ENV trong .env nếu muốn linh hoạt hơn
            base_url = ApiUrls.preview.value
        else:
            base_url = ApiUrls.mainnet.value

        print(f"🌐 Kết nối Blockfrost tại: {base_url}")
        return BlockFrostApi(project_id=BLOCKFROST_PROJECT_ID, base_url=base_url)


    def get_balance(self) -> Optional[float]:
        """Truy vấn số dư ADA từ Blockfrost."""
        try:
            api = self._get_blockfrost_api()
            address_info = api.address(self.get_address_bech32())

            # Lấy giá trị Lovelace (thường ở amount[0])
            lovelace = 0
            for amt in address_info.amount:
                if amt.unit == "lovelace":
                    lovelace = int(amt.quantity)
                    break

            ada_balance = lovelace / 1_000_000
            return ada_balance

        except ApiError as e:
            print(f"❌ Lỗi Blockfrost API: {e}")
        except Exception as e:
            print(f"❌ Không thể lấy balance: {e}")
        return None


    def get_utxos(self) -> Optional[List[dict]]:
        """Lấy danh sách UTxO tại địa chỉ."""
        try:
            api = self._get_blockfrost_api()
            utxos = api.address_utxos(self.get_address_bech32())
            return utxos
        except Exception as e:
            print(f"❌ Không thể truy vấn UTxO: {e}")
        return None


# ---------- CLI ----------
def main():
    args = sys.argv[1:]
    if not args:
        print("📘 Dùng: python -m wallet.wallet_manager <command>")
        print("Lệnh có sẵn: generate_mnemonic | get_address | get_stake | export_keys | get_balance | get_utxos | show_mnemonic")
        return

    command = args[0]
    wm = WalletManager()

    if command == "generate_mnemonic":
        print(WalletManager.generate_new_mnemonic())

    elif command == "get_address":
        print("Payment Address:", wm.get_address_bech32())

    elif command == "get_stake":
        print("Stake Address:", wm.get_stake_address())

    elif command == "export_keys":
        wm.export_keys()

    elif command == "get_balance":
        bal = wm.get_balance()
        print(f"💰 Số dư: {bal} ADA" if bal is not None else "Không thể lấy số dư.")

    elif command == "get_utxos":
        utxos = wm.get_utxos()
        if utxos:
            for u in utxos:
                print(f"- TX Hash: {u.tx_hash[:20]}..., Amount: {u.amount[0].quantity}")
        else:
            print("Không tìm thấy UTxO.")

    elif command == "show_mnemonic":
        print("Mnemonic:", wm.export_mnemonic())

    else:
        print(f"❌ Lệnh không hợp lệ: {command}")


if __name__ == "__main__":
    main()
