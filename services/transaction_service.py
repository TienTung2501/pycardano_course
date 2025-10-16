"""
services/transaction_service.py

Cung cấp các hàm tiện ích để gửi ADA, kiểm tra UTXO và tạo transaction cơ bản.
Tái sử dụng Blockfrost context từ config.blockfrost.
"""

from typing import Optional, List
from pycardano import (
    TransactionBuilder,
    PaymentSigningKey,
    PaymentVerificationKey,
    TransactionOutput,
    Transaction,
    Address,
    Network,
    Value,
)
from config.blockfrost import get_blockfrost_context
from wallet.wallet_manager import WalletManager
from config.logging_config import logger


class TransactionService:
    """
    Service để gửi ADA, tạo transaction cơ bản.
    Tự động load context từ Blockfrost.
    """

    def __init__(self, wallet: Optional[WalletManager] = None):
        """
        Args:
            wallet: (Optional) WalletManager instance. Nếu None, dùng mặc định từ .env.
        """
        self.wallet = wallet or WalletManager()
        self.context = get_blockfrost_context()
        logger.info("✅ TransactionService đã được khởi tạo.")

    def get_balance(self) -> int:
        """
        Trả về tổng ADA (lovelace) trong ví hiện tại.
        """
        address = self.wallet.get_address()
        utxos = self.context.utxos(address)
        total = sum(utxo.output.amount.coin for utxo in utxos)
        logger.info(f"💰 Balance của {address}: {total / 1_000_000} ADA")
        return total

    def send_ada(self, to_address: str, amount_lovelace: int, metadata: Optional[dict] = None) -> str:
        """
        Gửi ADA đến địa chỉ khác.

        Args:
            to_address: Địa chỉ người nhận (bech32).
            amount_lovelace: Số lượng ADA (đơn vị: lovelace, 1 ADA = 1_000_000 lovelace).
            metadata: Optional JSON metadata (nếu cần).

        Returns:
            transaction_id (hash) sau khi submit.
        """
        sender_addr = self.wallet.get_address()
        receiver_addr = Address.from_primitive(to_address)

        logger.info(f"🚀 Đang tạo giao dịch gửi {amount_lovelace / 1_000_000} ADA tới {to_address[:20]}...")

        builder = TransactionBuilder(self.context)

        # UTXOs từ ví người gửi
        builder.add_input_address(sender_addr)

        # Output cho người nhận
        builder.add_output(TransactionOutput(receiver_addr, Value(amount_lovelace)))

        # Thêm metadata nếu có
        if metadata:
            builder.auxiliary_data = metadata
            logger.info("🧾 Đã thêm metadata vào transaction.")

        # Ký giao dịch
        signed_tx = builder.build_and_sign(
            [self.wallet.get_signing_key()],
            self.wallet.get_verify_key()
        )

        # Submit
        tx_id = self.context.submit_tx(signed_tx.to_cbor())
        logger.info(f"✅ Gửi giao dịch thành công! Tx ID: {tx_id}")
        return tx_id

    def get_utxos(self) -> List:
        """
        Trả về danh sách UTXO (đối tượng pycardano.UTxO) của ví hiện tại.
        """
        utxos = self.context.utxos(self.wallet.get_address())
        logger.info(f"🔍 Tìm thấy {len(utxos)} UTXO cho ví {self.wallet.get_address_bech32()}.")
        return utxos


# Chạy thử nhanh
if __name__ == "__main__":
    tx_service = TransactionService()
    balance = tx_service.get_balance()
    print("Balance:", balance, "Lovelace")
    # Gửi thử 1 ADA (chỉ chạy nếu có test ADA)
    # tx_service.send_ada("addr_test1v...", 1_000_000)
