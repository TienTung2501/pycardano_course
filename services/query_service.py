"""
services/query_service.py

Các hàm tiện ích để truy vấn dữ liệu từ blockchain:
- Lấy số dư ví (ADA, token)
- Lấy UTXO
- Lấy thông tin giao dịch hoặc metadata
"""

from typing import Optional, Dict, Any, List
from pycardano import Address, Value
from config.blockfrost import get_blockfrost_context
from wallet.wallet_manager import WalletManager
from config.logging_config import logger


class QueryService:
    """
    Service để truy vấn dữ liệu từ blockchain Cardano qua Blockfrost.
    """

    def __init__(self, wallet: Optional[WalletManager] = None):
        self.wallet = wallet or WalletManager()
        self.context = get_blockfrost_context()
        logger.info("✅ QueryService đã được khởi tạo.")

    def get_address_info(self, address: Optional[str] = None) -> Dict[str, Any]:
        """
        Lấy thông tin chi tiết của địa chỉ: số dư ADA và token.

        Args:
            address: Nếu None → lấy địa chỉ mặc định từ ví.

        Returns:
            dict chứa số dư ADA và token list.
        """
        addr = address or self.wallet.get_address_bech32()
        utxos = self.context.utxos(addr)

        total_ada = 0
        tokens = {}

        for utxo in utxos:
            total_ada += utxo.output.amount.coin
            if utxo.output.amount.multi_asset:
                for policy_id, assets in utxo.output.amount.multi_asset.items():
                    for asset_name, qty in assets.items():
                        token_id = f"{policy_id.hex()}:{asset_name.decode('utf-8')}"
                        tokens[token_id] = tokens.get(token_id, 0) + qty

        logger.info(f"📫 Địa chỉ {addr[:15]}... có {total_ada/1_000_000} ADA và {len(tokens)} token.")
        return {
            "address": addr,
            "balance_ada": total_ada / 1_000_000,
            "tokens": tokens
        }

    def get_utxos(self, address: Optional[str] = None) -> List:
        """
        Lấy danh sách UTXO của địa chỉ.

        Args:
            address: bech32 address hoặc None để dùng ví mặc định.
        """
        addr = address or self.wallet.get_address_bech32()
        utxos = self.context.utxos(addr)
        logger.info(f"🔍 Tìm thấy {len(utxos)} UTXO cho {addr[:15]}...")
        return utxos

    def get_transaction_info(self, tx_hash: str) -> Dict[str, Any]:
        """
        Lấy thông tin chi tiết của transaction qua Blockfrost API.

        Args:
            tx_hash: hash của giao dịch.

        Returns:
            dict chứa thông tin cơ bản.
        """
        try:
            tx_info = self.context.api.transaction(tx_hash)
            logger.info(f"🧾 Transaction {tx_hash[:10]}... được truy vấn thành công.")
            return tx_info
        except Exception as e:
            logger.error(f"Lỗi khi truy vấn transaction {tx_hash}: {e}")
            return {}

    def get_asset_info(self, policy_id: str, asset_name: str) -> Dict[str, Any]:
        """
        Lấy thông tin về 1 token cụ thể (FT/NFT) từ Blockfrost.

        Args:
            policy_id: ID của policy.
            asset_name: tên token (chuỗi gốc).

        Returns:
            dict thông tin token (name, supply, metadata, ...).
        """
        asset_id = f"{policy_id}{asset_name.encode('utf-8').hex()}"
        try:
            info = self.context.api.asset(asset_id)
            logger.info(f"📦 Token {asset_name} ({policy_id[:10]}...) được truy vấn thành công.")
            return info
        except Exception as e:
            logger.error(f"Lỗi khi truy vấn token {asset_id}: {e}")
            return {}

    def get_latest_block(self) -> Dict[str, Any]:
        """
        Lấy thông tin block mới nhất.
        """
        block = self.context.api.block_latest()
        logger.info(f"⛓️ Block mới nhất: {block['hash'][:10]}... slot {block['slot']}")
        return block


# Chạy thử nhanh
if __name__ == "__main__":
    q = QueryService()
    info = q.get_address_info()
    print(info)
    block = q.get_latest_block()
    print("Latest block:", block["slot"])
