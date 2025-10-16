"""
wallet/wallet_manager.py

WalletManager: wrapper tiện lợi để quản lý HD wallet (mnemonic -> keys -> address)
Sử dụng pycardano.HDWallet.

Lưu ý bảo mật:
- KHÔNG commit .env chứa MNEMONIC lên git.
- Chỉ dùng MNEMONIC cho testnet trong môi trường học tập/demo.
- Với môi trường production, dùng HSM hoặc key management service.
"""

import os
from typing import Optional

from pycardano import HDWallet, Address, Network, VerificationKey, SigningKey
from config.settings import MNEMONIC, NETWORK

class WalletManager:
    """
    Wallet manager đơn giản:
    - Nếu truyền mnemonic vào constructor thì sẽ dùng mnemonic đó.
    - Nếu không, cố gắng đọc biến MNEMONIC từ config.settings (được load từ .env).
    - Expose: address, signing key, verify key, export mnemonic.
    """

    def __init__(self, mnemonic: Optional[str] = None, account_index: int = 0):
        """
        Args:
            mnemonic: (optional) 12/24-word mnemonic. Nếu None sẽ dùng MNEMONIC từ .env.
            account_index: index để derive key (nếu cần nhiều key/addresses).
        """
        mnemonic_to_use = mnemonic or MNEMONIC
        if not mnemonic_to_use:
            raise ValueError("MNEMONIC chưa được cung cấp. Thiết lập biến MNEMONIC trong .env hoặc truyền mnemonic vào constructor.")

        # Tạo HD wallet từ mnemonic
        self.wallet = HDWallet.from_mnemonic(mnemonic_to_use)
        # Lấy cặp key mặc định (index 0). pycardano HDWallet.key_pairs là danh sách keypairs.
        # Nếu muốn nhiều address, có thể mở rộng để derive thêm.
        self.key_pair = self.wallet.key_pairs[account_index]
        self.signing_key: SigningKey = self.key_pair.signing_key
        self.verify_key: VerificationKey = self.key_pair.verify_key

        # Địa chỉ tiền tệ (payment address) dùng verify_key.hash()
        self.address: Address = Address(payment_part=self.verify_key.hash(), network=NETWORK)

    def get_address(self) -> Address:
        """Trả về object Address (pycardano.Address)."""
        return self.address

    def get_address_bech32(self) -> str:
        """Trả về address dạng bech32 (chuỗi) để hiển thị hoặc gửi cho faucet."""
        return str(self.address)

    def get_signing_key(self) -> SigningKey:
        """Trả về SigningKey object (dùng để ký transaction)."""
        return self.signing_key

    def get_verify_key(self) -> VerificationKey:
        """Trả về VerifyKey object (dùng để lấy hash public key, policy,...)."""
        return self.verify_key

    def export_mnemonic(self) -> str:
        """Trả về mnemonic (cẩn trọng: bảo mật)."""
        return self.wallet.mnemonic

    @staticmethod
    def generate_new_mnemonic() -> str:
        """Sinh một mnemonic ngẫu nhiên (24 từ) và trả về (không lưu)."""
        new_wallet = HDWallet.from_random()
        return new_wallet.mnemonic

# Ví dụ nhanh (chạy file trực tiếp để test)
if __name__ == "__main__":
    # Lưu ý: chỉ chạy thử trên môi trường dev/test
    try:
        wm = WalletManager()
        print("Wallet address:", wm.get_address_bech32())
        # Không in mnemonic ra trong production
        print("Mnemonic (KEEP SECRET):", wm.export_mnemonic()[:40] + "..." )
    except Exception as e:
        print("Lỗi khi khởi tạo WalletManager:", e)
