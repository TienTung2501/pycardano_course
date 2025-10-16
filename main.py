# main.py
# Entry point để test nhanh các chức năng cơ bản

from services.transaction_service import TransactionService
from services.mint_service import MintService
from config.logging_config import logger

if __name__ == "__main__":
    logger.info("🚀 Khởi động demo PyCardano Course...")

    tx_service = TransactionService()
    mint_service = MintService()

    # Ví dụ gửi ADA
    # tx_service.send_ada("addr_test1vq...", 1_000_000)

    # Ví dụ mint token
    mint_service.mint_ft("PYTOKEN", 10)
