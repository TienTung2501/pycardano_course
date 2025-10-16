"""
services/mint_service.py

Xử lý các thao tác mint và burn token (FT và NFT) bằng PyCardano.
Tự động tái sử dụng Blockfrost context và WalletManager.
"""

import os
import time
from typing import Optional, Dict
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


class MintService:
    """
    Dịch vụ mint/burn token (FT và NFT).
    """

    def __init__(self, wallet: Optional[WalletManager] = None):
        self.wallet = wallet or WalletManager()
        self.context = get_blockfrost_context()
        logger.info("✅ MintService đã được khởi tạo.")

    def _create_policy(self, expire_in_minutes: int = 30):
        """
        Tạo policy script tạm thời (policy key + policy script).
        Policy này cho phép mint token trong 30 phút.

        Returns:
            (policy_script, policy_id, skey)
        """
        policy_skey = PaymentSigningKey.generate()
        policy_vkey = PaymentVerificationKey.from_signing_key(policy_skey)

        slot = self.context.last_block_slot() + expire_in_minutes * 60
        script_pubkey = ScriptPubkey(policy_vkey.hash())
        timelock = InvalidHereAfter(slot)
        policy_script = ScriptAll([script_pubkey, timelock])

        policy_id = policy_script.hash().payload.hex()

        logger.info(f"🧩 Policy được tạo với ID: {policy_id[:16]}..., hết hạn sau {expire_in_minutes} phút.")
        return policy_script, policy_id, policy_skey

    def mint_token(
        self,
        token_name: str,
        amount: int = 1,
        metadata: Optional[Dict] = None,
        is_nft: bool = False,
        expire_in_minutes: int = 30,
    ) -> str:
        """
        Mint token (FT hoặc NFT) trên testnet/mainnet.

        Args:
            token_name: Tên token (ví dụ: "MyToken").
            amount: Số lượng (FT có thể >1, NFT luôn =1).
            metadata: Optional metadata (dict).
            is_nft: Nếu True → NFT, False → Fungible token.
            expire_in_minutes: Thời gian hết hạn policy (mặc định 30 phút).

        Returns:
            tx_id (hash)
        """
        policy_script, policy_id, policy_skey = self._create_policy(expire_in_minutes)
        builder = TransactionBuilder(self.context)

        # Địa chỉ ví người mint
        sender_addr = self.wallet.get_address()
        builder.add_input_address(sender_addr)

        # Token name và multiasset
        asset_name = AssetName(token_name.encode("utf-8"))
        multi_asset = MultiAsset.from_primitive({
            bytes.fromhex(policy_id): {
                asset_name.payload: amount
            }
        })

        # Output: gửi token về chính ví người mint
        output = TransactionOutput(sender_addr, Value(2_000_000, multi_asset))
        builder.add_output(output)

        # Metadata (nếu có)
        if metadata:
            builder.auxiliary_data = metadata
            logger.info("🧾 Thêm metadata vào transaction mint.")

        # Thêm thông tin minting
        builder.mint = multi_asset
        builder.native_scripts = [policy_script]

        # Ký
        signed_tx = builder.build_and_sign(
            [self.wallet.get_signing_key(), policy_skey],
            self.wallet.get_verify_key()
        )

        tx_id = self.context.submit_tx(signed_tx.to_cbor())
        logger.success(f"✅ Mint thành công {amount} {token_name} ({'NFT' if is_nft else 'FT'})!")
        logger.info(f"🔗 Transaction ID: {tx_id}")

        # Lưu policy vào file để burn sau này
        os.makedirs("data/policies", exist_ok=True)
        with open(f"data/policies/{policy_id}.policy", "w") as f:
            f.write(policy_script.to_cbor_hex())

        return tx_id

    def burn_token(
        self,
        policy_id: str,
        token_name: str,
        amount: int = 1,
    ) -> str:
        """
        Burn token đã mint trước đó.

        Args:
            policy_id: ID của policy script (đã dùng khi mint).
            token_name: Tên token.
            amount: Số lượng cần burn.

        Returns:
            tx_id (hash)
        """
        # Tải lại policy script
        policy_path = f"data/policies/{policy_id}.policy"
        if not os.path.exists(policy_path):
            raise FileNotFoundError(f"Không tìm thấy policy script: {policy_path}")

        with open(policy_path, "r") as f:
            policy_script_cbor = f.read()

        policy_script = NativeScript.from_cbor(policy_script_cbor)
        policy_skey = self.wallet.get_signing_key()  # Có thể cần policy key riêng nếu policy khác

        builder = TransactionBuilder(self.context)
        sender_addr = self.wallet.get_address()
        builder.add_input_address(sender_addr)

        asset_name = AssetName(token_name.encode("utf-8"))
        multi_asset = MultiAsset.from_primitive({
            bytes.fromhex(policy_id): {
                asset_name.payload: -amount  # âm → burn
            }
        })

        builder.mint = multi_asset
        builder.native_scripts = [policy_script]

        signed_tx = builder.build_and_sign(
            [self.wallet.get_signing_key(), policy_skey],
            self.wallet.get_verify_key()
        )

        tx_id = self.context.submit_tx(signed_tx.to_cbor())
        logger.warning(f"🔥 Burn thành công {amount} {token_name}. Tx ID: {tx_id}")
        return tx_id


# Chạy thử
if __name__ == "__main__":
    mint_service = MintService()
    # Mint thử NFT
    tx_id = mint_service.mint_token("MyNFT001", metadata={"name": "Demo NFT"}, is_nft=True)
    print("Tx:", tx_id)
