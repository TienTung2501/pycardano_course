"""
Service hợp nhất UTXO - GIỮ TỐI THIỂU 1.5 ADA
Đơn giản, an toàn, tự chờ transaction confirm!
"""

import time
from typing import Optional
from pycardano import TransactionBuilder, TransactionOutput, Value
from pycardano.utils import min_lovelace
from config.blockfrost import get_blockfrost_context
from wallet.wallet_manager import WalletManager
from config.logging_config import logger


class ConsolidationService:
    def __init__(self, wallet: Optional[WalletManager] = None):
        self.wallet = wallet or WalletManager()
        self.context = get_blockfrost_context()
        logger.info("✅ ConsolidationService (Auto min ADA, safe mode)")

    def consolidate(self, min_utxo_threshold: int = 5, wait_confirm: bool = True) -> Optional[str]:
        """
        Hợp nhất các UTXO nhỏ về 1 UTXO duy nhất.

        Args:
            min_utxo_threshold: số lượng UTXO tối thiểu để thực hiện hợp nhất
            wait_confirm: có chờ transaction confirm on-chain không
        """
        address = self.wallet.get_address()
        utxos = self.context.utxos(address)
        logger.info(f"🔍 Có {len(utxos)} UTXO tại {str(address)[:20]}...")

        if len(utxos) < min_utxo_threshold:
            logger.warning(f"⚠️ Ít hơn {min_utxo_threshold} UTXO, bỏ qua.")
            return None

        total_lovelace = sum(u.output.amount.coin for u in utxos)
        logger.info(f"💰 Tổng số dư: {total_lovelace / 1_000_000:.6f} ADA")

        # Khởi tạo transaction
        builder = TransactionBuilder(self.context)
        builder.add_input_address(address)

        # Tính output = tổng ADA - giữ MIN_ADA (1.5 ADA)
        MIN_ADA = 1_500_000
        FEE_ESTIMATE = 200_000  # ước lượng trước
        output_amount = max(total_lovelace - MIN_ADA - FEE_ESTIMATE, MIN_ADA)

        builder.add_output(TransactionOutput(address, Value(output_amount)))

        try:
            signed_tx = builder.build_and_sign(
                [self.wallet.get_signing_key()],
                change_address=address
            )

            tx_hash = self.context.submit_tx(signed_tx)
            logger.info(f"✅ Giao dịch hợp nhất đã gửi: {tx_hash}")

            if wait_confirm:
                logger.info("⏳ Chờ transaction confirm on-chain...")
                self._wait_tx_confirm(tx_hash)

            return tx_hash

        except Exception as e:
            logger.error(f"🚨 Lỗi khi gửi giao dịch: {e}")
            return None

    def _wait_tx_confirm(self, tx_hash: str, timeout: int = 120, interval: int = 5):
        """
        Chờ transaction confirm trên chain.

        Args:
            tx_hash: hash của transaction
            timeout: thời gian tối đa chờ (giây)
            interval: khoảng thời gian check (giây)
        """
        elapsed = 0
        while elapsed < timeout:
            try:
                tx_info = self.context.transaction(tx_hash)
                if tx_info:  # transaction đã appear
                    logger.info(f"✅ Transaction confirmed: {tx_hash}")
                    return True
            except Exception:
                pass

            time.sleep(interval)
            elapsed += interval

        logger.warning(f"⚠️ Transaction chưa confirm sau {timeout}s: {tx_hash}")
        return False


# -------------------------------------------------------------------
# ✅ TEST SIÊU ĐƠN GIẢN
# -------------------------------------------------------------------
if __name__ == "__main__":
    from services.query_service import QueryService

    q = QueryService()
    c = ConsolidationService(q.wallet)

    print("\n=== 📊 TRƯỚC ===")
    utxos = q.get_utxos()
    print(f"UTXO: {len(utxos)}")
    print(f"Tổng: {sum(u.output.amount.coin for u in utxos) / 1_000_000:.6f} ADA")

    print("\n🔄 HỢP NHẤT (giữ 1.5 ADA)...")
    tx_hash = c.consolidate(min_utxo_threshold=2, wait_confirm=True)

    if tx_hash:
        print(f"🎉 TX: {tx_hash}")
    else:
        print("⚠️ Không hợp nhất")

    print("\n=== 📊 SAU ===")
    utxos_after = q.get_utxos()
    print(f"UTXO: {len(utxos_after)}")
