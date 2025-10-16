"""
services/nft_service.py

Dịch vụ chuyên cho NFT:
- Mint NFT thường (CIP-25)
- Mint NFT động (CIP-68)
- Cập nhật metadata
- Burn NFT
"""

import os
import json
import time
from typing import Optional, Dict, Any
from pycardano import (
    TransactionBuilder,
    TransactionOutput,
    PaymentSigningKey,
    PaymentVerificationKey,
    Value,
    MultiAsset,
    AssetName,
    ScriptPubkey,
    InvalidHereAfter,
    ScriptAll,
    NativeScript,
)
from config.blockfrost import get_blockfrost_context
from wallet.wallet_manager import WalletManager
from config.logging_config import logger


class NFTService:
    """
    Xử lý toàn bộ logic NFT (mint, update, burn).
    """

    def __init__(self, wallet: Optional[WalletManager] = None):
        self.wallet = wallet or WalletManager()
        self.context = get_blockfrost_context()
        logger.info("✅ NFTService đã được khởi tạo.")

    # ======================================================================
    # 1️⃣ Tạo policy (giống MintService nhưng tái sử dụng ở đây)
    # ======================================================================
    def _create_policy(self, expire_in_minutes: int = 60):
        policy_skey = PaymentSigningKey.generate()
        policy_vkey = PaymentVerificationKey.from_signing_key(policy_skey)

        slot = self.context.last_block_slot() + expire_in_minutes * 60
        script_pubkey = ScriptPubkey(policy_vkey.hash())
        timelock = InvalidHereAfter(slot)
        policy_script = ScriptAll([script_pubkey, timelock])

        policy_id = policy_script.hash().payload.hex()
        logger.info(f"🧩 Policy NFT mới: {policy_id[:16]}... (hết hạn sau {expire_in_minutes} phút)")

        os.makedirs("data/policies", exist_ok=True)
        with open(f"data/policies/{policy_id}.policy", "w") as f:
            f.write(policy_script.to_cbor_hex())

        return policy_script, policy_id, policy_skey

    # ======================================================================
    # 2️⃣ Mint NFT cơ bản (CIP-25)
    # ======================================================================
    def mint_nft(self, nft_name: str, ipfs_link: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Mint NFT chuẩn CIP-25 (metadata tĩnh).

        Args:
            nft_name: Tên NFT.
            ipfs_link: Link IPFS chứa hình ảnh hoặc metadata JSON.
            metadata: Thông tin metadata thêm (dict).

        Returns:
            tx_id
        """
        policy_script, policy_id, policy_skey = self._create_policy()
        builder = TransactionBuilder(self.context)
        sender_addr = self.wallet.get_address()
        builder.add_input_address(sender_addr)

        # MultiAsset cấu hình token NFT
        asset_name = AssetName(nft_name.encode("utf-8"))
        multi_asset = MultiAsset.from_primitive({
            bytes.fromhex(policy_id): {
                asset_name.payload: 1
            }
        })

        # Metadata chuẩn CIP-25
        full_metadata = {
            721: {
                policy_id: {
                    nft_name: {
                        "name": nft_name,
                        "image": ipfs_link,
                        "mediaType": "image/png",
                        "description": metadata.get("description") if metadata else "PyCardano NFT Demo"
                    }
                }
            }
        }

        builder.add_output(TransactionOutput(sender_addr, Value(2_000_000, multi_asset)))
        builder.mint = multi_asset
        builder.native_scripts = [policy_script]
        builder.auxiliary_data = full_metadata

        signed_tx = builder.build_and_sign(
            [self.wallet.get_signing_key(), policy_skey],
            self.wallet.get_verify_key()
        )

        tx_id = self.context.submit_tx(signed_tx.to_cbor())
        logger.success(f"✅ Mint NFT {nft_name} thành công! Tx: {tx_id}")
        return tx_id

    # ======================================================================
    # 3️⃣ Mint NFT động (CIP-68)
    # ======================================================================
    def mint_dynamic_nft(self, nft_name: str, metadata: Dict[str, Any]) -> str:
        """
        Mint Dynamic NFT (CIP-68) cho phép cập nhật metadata sau này.

        Args:
            nft_name: Tên NFT.
            metadata: Thông tin metadata ban đầu (dict).
        """
        policy_script, policy_id, policy_skey = self._create_policy()
        builder = TransactionBuilder(self.context)
        sender_addr = self.wallet.get_address()
        builder.add_input_address(sender_addr)

        # Token chính (reference NFT)
        asset_name = AssetName(nft_name.encode("utf-8"))
        multi_asset = MultiAsset.from_primitive({
            bytes.fromhex(policy_id): {
                asset_name.payload: 1
            }
        })

        # Metadata CIP-68
        cip68_metadata = {
            68: {
                "referenceNFT": {
                    "name": nft_name,
                    "attributes": metadata,
                    "timestamp": int(time.time())
                }
            }
        }

        builder.add_output(TransactionOutput(sender_addr, Value(2_000_000, multi_asset)))
        builder.mint = multi_asset
        builder.native_scripts = [policy_script]
        builder.auxiliary_data = cip68_metadata

        signed_tx = builder.build_and_sign(
            [self.wallet.get_signing_key(), policy_skey],
            self.wallet.get_verify_key()
        )

        tx_id = self.context.submit_tx(signed_tx.to_cbor())
        logger.success(f"🧠 Mint Dynamic NFT {nft_name} thành công! Tx: {tx_id}")
        return tx_id

    # ======================================================================
    # 4️⃣ Cập nhật metadata NFT động
    # ======================================================================
    def update_dynamic_nft(self, policy_id: str, nft_name: str, new_metadata: Dict[str, Any]) -> str:
        """
        Cập nhật metadata của NFT động (CIP-68).

        Args:
            policy_id: Policy ID của NFT.
            nft_name: Tên NFT.
            new_metadata: Dữ liệu metadata mới.
        """
        builder = TransactionBuilder(self.context)
        sender_addr = self.wallet.get_address()
        builder.add_input_address(sender_addr)

        # Metadata cập nhật
        update_metadata = {
            68: {
                "referenceNFT": {
                    "name": nft_name,
                    "attributes": new_metadata,
                    "updated": int(time.time())
                }
            }
        }

        builder.auxiliary_data = update_metadata

        signed_tx = builder.build_and_sign(
            [self.wallet.get_signing_key()],
            self.wallet.get_verify_key()
        )

        tx_id = self.context.submit_tx(signed_tx.to_cbor())
        logger.info(f"♻️ Metadata NFT {nft_name} được cập nhật! Tx: {tx_id}")
        return tx_id

    # ======================================================================
    # 5️⃣ Burn NFT
    # ======================================================================
    def burn_nft(self, policy_id: str, nft_name: str) -> str:
        """
        Burn NFT theo policy và tên.

        Args:
            policy_id: Policy ID.
            nft_name: Tên NFT.
        """
        policy_path = f"data/policies/{policy_id}.policy"
        if not os.path.exists(policy_path):
            raise FileNotFoundError(f"Không tìm thấy policy script: {policy_path}")

        with open(policy_path, "r") as f:
            policy_script_cbor = f.read()

        policy_script = NativeScript.from_cbor(policy_script_cbor)
        builder = TransactionBuilder(self.context)
        sender_addr = self.wallet.get_address()
        builder.add_input_address(sender_addr)

        asset_name = AssetName(nft_name.encode("utf-8"))
        multi_asset = MultiAsset.from_primitive({
            bytes.fromhex(policy_id): {
                asset_name.payload: -1  # Burn 1 NFT
            }
        })

        builder.mint = multi_asset
        builder.native_scripts = [policy_script]

        signed_tx = builder.build_and_sign(
            [self.wallet.get_signing_key()],
            self.wallet.get_verify_key()
        )

        tx_id = self.context.submit_tx(signed_tx.to_cbor())
        logger.warning(f"🔥 Đã burn NFT {nft_name}! Tx: {tx_id}")
        return tx_id


# Test nhanh
if __name__ == "__main__":
    nft_service = NFTService()
    # Mint NFT demo
    tx = nft_service.mint_nft("DemoNFT01", "ipfs://bafybeig...", {"description": "NFT thử nghiệm"})
    print("Tx:", tx)
