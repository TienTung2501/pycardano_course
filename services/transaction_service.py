"""
services/transaction_service.py

Tiêu chí:
- Luôn đảm bảo Address là pycardano.Address trước khi đưa vào TransactionBuilder.
- Hỗ trợ input address dưới dạng: pycardano.Address / bech32 string / dict chứa "cborHex".
- Đóng gói metadata đúng kiểu AuxiliaryData(Metadata(...)).
- Log thêm type để debug nhanh nếu vẫn có lỗi.
- Hỗ trợ chờ transaction confirm on-chain.
- Query balance trước và sau giao dịch.
"""

import time
import traceback
from typing import Optional, List, Dict, Any, Union
from pycardano import (
    TransactionBuilder,
    TransactionOutput,
    Address,
    Value,
    AuxiliaryData,
    Metadata,
)
from config.blockfrost import get_blockfrost_context
from wallet.wallet_manager import WalletManager
from config.logging_config import logger


class TransactionService:
    def __init__(self, wallet: Optional[WalletManager] = None):
        self.wallet = wallet or WalletManager()
        self.context = get_blockfrost_context()
        logger.info("✅ TransactionService đã được khởi tạo.")

    def get_balance(self) -> int:
        """Trả về tổng ADA (lovelace) trong ví hiện tại."""
        address = self.wallet.get_address()
        utxos = self.context.utxos(address)
        total = sum(utxo.output.amount.coin for utxo in utxos)
        logger.info(f"💰 Balance của {address}: {total / 1_000_000:.6f} ADA")
        return total

    def send_ada(
        self,
        to_address: Union[str, dict, Address],
        amount_lovelace: int,
        metadata: Optional[Dict[str, Any]] = None,
        wait_confirm: bool = True,
        timeout: int = 120,
        interval: int = 5,
    ) -> str:
        """
        Gửi ADA đến địa chỉ khác và log balance trước & sau giao dịch.
        """
        sender_addr = self.wallet.get_address()
        receiver_addr = to_address

        logger.info(
            f"🚀 Tạo giao dịch gửi {amount_lovelace / 1_000_000:.6f} ADA tới {receiver_addr}"
        )
        logger.debug(f"Sender type: {type(sender_addr)}, Receiver type: {type(receiver_addr)}")

        builder = TransactionBuilder(self.context)
        builder.add_input_address(sender_addr)
        builder.add_output(TransactionOutput(receiver_addr, Value(amount_lovelace)))

        if metadata:
            builder.auxiliary_data = AuxiliaryData(Metadata(metadata))
            logger.info("🧾 Đã thêm metadata vào transaction.")

        try:
            signed_tx = builder.build_and_sign(
                [self.wallet.get_signing_key()],
                change_address=sender_addr,
            )

            tx_hash = self.context.submit_tx(signed_tx)
            logger.info(f"✅ Giao dịch đã gửi: {tx_hash}")

            if wait_confirm:
                self._wait_tx_confirm(tx_hash, timeout=timeout, interval=interval)

            return tx_hash

        except Exception as e:
            logger.error(f"🚨 Lỗi khi gửi giao dịch: {e}")
            traceback.print_exc()
            raise

    def _wait_tx_confirm(self, tx_hash: str, timeout: int = 120, interval: int = 5):
        """Chờ transaction confirm on-chain."""
        elapsed = 0
        while elapsed < timeout:
            try:
                tx_info = self.context.transaction(tx_hash)
                if tx_info:
                    logger.info(f"✅ Transaction confirmed: {tx_hash}")
                    return True
            except Exception:
                pass

            time.sleep(interval)
            elapsed += interval
            logger.info(f"⏳ Đang chờ transaction confirm... {elapsed}/{timeout} giây trôi qua.")
        return False

    def get_utxos(self) -> List:
        """Trả về danh sách UTXO (pycardano.UTxO) của ví hiện tại."""
        address = self.wallet.get_address()
        utxos = self.context.utxos(address)
        logger.info(f"🔍 Tìm thấy {len(utxos)} UTXO cho ví {address}.")
        return utxos


# Quick test CLI
if __name__ == "__main__":
    tx_service = TransactionService()

    # --- Balance trước ---
    print("💰 Balance trước:")
    balance_before = tx_service.get_balance()

    to_address = (
        "addr_test1qqja25tffmwywjufeycgn86zj7slfj9w4wh5a7ft4png47ue0r2q9x4995mt5xscmehf5swm6qx4flkg98euf3rk45usuerp08"
    )
    amount = 2_000_000

    try:
        tx_id = tx_service.send_ada(to_address, amount, wait_confirm=True)
        print("✅ Transaction submitted:", tx_id)
    except Exception as e:
        print("❌ Lỗi khi gửi ADA:", e)
        traceback.print_exc()

    # --- Balance sau ---
    print("💰 Balance sau:")
    balance_after = tx_service.get_balance()
