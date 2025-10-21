import os
import sys
import random
from typing import Optional, Dict, List
from os.path import exists
from pycardano import (
    Address, TransactionBuilder, TransactionOutput, PaymentSigningKey,
    PaymentVerificationKey, Value, MultiAsset, AssetName, ScriptPubkey,
    ScriptAll, NativeScript, AuxiliaryData, AlonzoMetadata, Metadata, UTxO,
    PaymentKeyPair, BlockFrostChainContext
)
from config.blockfrost import get_blockfrost_context
from wallet.wallet_manager import WalletManager
from config.logging_config import logger

# Fix encoding tiếng Việt trên Windows
sys.stdout.reconfigure(encoding="utf-8")

def ensure_address(addr):
    """Đảm bảo addr là pycardano.Address hợp lệ"""
    if isinstance(addr, Address):
        return addr
    elif isinstance(addr, str):
        return Address.from_primitive(addr)
    elif isinstance(addr, dict) and "cborHex" in addr:
        return Address.from_primitive(bytes.fromhex(addr["cborHex"]))
    else:
        raise TypeError(f"❌ Invalid address type: {type(addr)} -> {addr}")

class MintService:
    """Dịch vụ mint/burn token (FT và NFT) trên Cardano blockchain."""
    
    def __init__(self, wallet: Optional[WalletManager] = None):
        self.wallet = wallet or WalletManager()
        self.context = get_blockfrost_context()
        self.payment_skey = self.wallet.get_signing_key()
        self.payment_vkey = PaymentVerificationKey.from_signing_key(self.payment_skey)
        self.address = ensure_address(self.wallet.get_address())
        self.policy_skey = None
        self.policy_vkey = None
        self._load_or_generate_policy_keys()
        logger.info("✅ MintService initialized successfully.")
        self.utxos = self._fetch_utxos()

    def _load_or_generate_policy_keys(self):
        """Tải hoặc tạo policy keys nếu chưa tồn tại."""
        policy_skey_path = "keys/policy.skey"
        policy_vkey_path = "keys/policy.vkey"
        if not exists(policy_skey_path) or not exists(policy_vkey_path):
            logger.info("🧩 Generating new policy keys...")
            key_pair = PaymentKeyPair.generate()
            key_pair.signing_key.save(policy_skey_path)
            key_pair.verification_key.save(policy_vkey_path)
        self.policy_skey = PaymentSigningKey.load(policy_skey_path)
        self.policy_vkey = PaymentVerificationKey.from_signing_key(self.policy_skey)
        logger.info("✅ Policy keys loaded/generated.")

    def _fetch_utxos(self):
        """Lấy UTxO mới nhất từ chain."""
        try:
            utxos = self.context.utxos(self.address)
            if not utxos:
                raise ValueError("❌ No UTxOs found. Fund wallet with ADA.")
            total_ada = sum(utxo.output.amount.coin for utxo in utxos)
            if total_ada < 5_000_000:
                raise ValueError(f"❌ Insufficient ADA: {total_ada/1_000_000} ADA. Need at least 5 ADA.")
            logger.info(f"✅ Fetched {len(utxos)} UTxOs with total {total_ada/1_000_000} ADA.")
            return utxos
        except Exception as e:
            logger.error(f"❌ Failed to fetch UTxOs: {e}")
            raise

    def _select_utxo_for_input(self, min_ada: int = 5_000_000):
        """Chọn UTxO có đủ ADA và không chứa asset."""
        for utxo in sorted(self.utxos, key=lambda u: u.output.amount.coin, reverse=True):
            if utxo.output.amount.coin >= min_ada and not utxo.output.amount.multi_asset:
                logger.info(f"✅ Selected UTxO: {utxo.input.transaction_id}#{utxo.input.index} with {utxo.output.amount.coin/1_000_000} ADA.")
                return utxo
        raise ValueError("❌ No suitable UTxO found with enough pure ADA.")

    def _select_utxo_for_burn(self, policy_id: str, token_name: str, amount: int):
        """Chọn UTxO chứa asset cần burn."""
        policy_hash = bytes.fromhex(policy_id)
        asset_name_bytes = token_name.encode("utf-8")
        for utxo in self.utxos:
            assets = utxo.output.amount.multi_asset
            if assets and policy_hash in assets and asset_name_bytes in assets[policy_hash] and assets[policy_hash][asset_name_bytes] >= amount:
                logger.info(f"✅ Selected UTxO for burn: {utxo.input.transaction_id}#{utxo.input.index}")
                return utxo
        raise ValueError(f"❌ No UTxO found containing at least {amount} of {token_name} under policy {policy_id}.")

    def _create_policy(self):
        """Tạo policy script dựa trên policy key."""
        pub_key_policy = ScriptPubkey(self.policy_vkey.hash())
        policy_script = ScriptAll([pub_key_policy])
        policy_id = policy_script.hash().payload.hex()
        logger.info(f"🧩 Created policy ID: {policy_id}")
        return policy_script, policy_id

    def mint_token(
        self,
        token_name: str,
        amount: int = 1,
        metadata: Optional[Dict] = None,
        is_nft: bool = False
    ) -> str:
        """Mint token (FT hoặc NFT) trên testnet/mainnet."""
        try:
            self.utxos = self._fetch_utxos()
            policy_script, policy_id = self._create_policy()
            builder = TransactionBuilder(self.context)
            builder.add_input(self._select_utxo_for_input())

            # Tạo multi-asset
            asset_name = AssetName(token_name.encode("utf-8"))
            multi_asset = MultiAsset.from_primitive({
                bytes.fromhex(policy_id): {asset_name.payload: amount}
            })

            # Tính min ADA và thêm output
            min_ada = self.context.min_lovelace(TransactionOutput(self.address, multi_asset))
            builder.add_output(TransactionOutput(self.address, Value(min_ada, multi_asset)))

            # Thêm metadata
            if metadata:
                safe_metadata = {
                    k: v.encode("utf-8", errors="replace").decode("utf-8") if isinstance(v, str) else v
                    for k, v in metadata.items()
                }
                if is_nft:
                    cip721_metadata = {721: {policy_id: {token_name: safe_metadata}}}
                    builder.auxiliary_data = AuxiliaryData(AlonzoMetadata(metadata=Metadata(cip721_metadata)))
                    logger.info("🧾 Added CIP-25 metadata (NFT)")
                else:
                    cip20_metadata = {
                        20: {
                            "name": safe_metadata.get("name", token_name),
                            "symbol": safe_metadata.get("symbol", token_name[:4].upper()),
                            "description": safe_metadata.get("description", f"{token_name} Token")
                        }
                    }
                    builder.auxiliary_data = AuxiliaryData(AlonzoMetadata(metadata=Metadata(cip20_metadata)))
                    logger.info("🧾 Added CIP-20 metadata (FT)")

            # Cấu hình minting
            builder.mint = multi_asset
            builder.native_scripts = [policy_script]
            builder.required_signers = [self.policy_vkey.hash()]
            builder.ttl = self.context.last_block_slot + 3600
            builder.add_change_if_needed(self.address)

            # Ký và submit
            signed_tx = builder.build_and_sign([self.payment_skey, self.policy_skey], change_address=self.address)
            logger.debug(f"Transaction CBOR: {signed_tx.to_cbor()}")
            tx_id = self.context.submit_tx(signed_tx.to_cbor())

            # Lưu policy script
            os.makedirs("data/policies", exist_ok=True)
            with open(f"data/policies/{policy_id}.policy", "w") as f:
                f.write(policy_script.to_cbor_hex())

            logger.success(f"✅ Minted {amount} {token_name} ({'NFT' if is_nft else 'FT'})! Tx ID: {tx_id}")
            logger.info(f"🧱 Policy ID: {policy_id} | Asset name (hex): {asset_name.payload.hex()}")
            return tx_id

        except Exception as e:
            logger.error(f"❌ Mint error: {str(e)}")
            return "ERROR"

    def mint_multiple_nfts(
        self,
        assets: List[Dict],
        is_nft: bool = True
    ) -> str:
        """Mint nhiều NFT trong một giao dịch."""
        try:
            self.utxos = self._fetch_utxos()
            policy_script, policy_id = self._create_policy()
            builder = TransactionBuilder(self.context)
            builder.add_input(self._select_utxo_for_input())

            # Tạo multi-asset cho nhiều NFT
            my_asset = Asset()
            multi_asset = MultiAsset()
            metadata = {721: {policy_id: {}}}
            for asset in assets:
                asset_name = asset["name"]
                asset_name_bytes = AssetName(asset_name.encode("utf-8"))
                my_asset[asset_name_bytes] = 1
                metadata[721][policy_id][asset_name] = {
                    k: v.encode("utf-8", errors="replace").decode("utf-8") if isinstance(v, str) else v
                    for k, v in asset.items()
                }
            multi_asset[bytes.fromhex(policy_id)] = my_asset

            # Tính min ADA và thêm output
            min_ada = self.context.min_lovelace(TransactionOutput(self.address, multi_asset))
            builder.add_output(TransactionOutput(self.address, Value(min_ada, multi_asset)))

            # Thêm metadata CIP-25
            if is_nft:
                builder.auxiliary_data = AuxiliaryData(AlonzoMetadata(metadata=Metadata(metadata)))
                logger.info("🧾 Added CIP-25 metadata for multiple NFTs")

            # Cấu hình minting
            builder.mint = multi_asset
            builder.native_scripts = [policy_script]
            builder.required_signers = [self.policy_vkey.hash()]
            builder.ttl = self.context.last_block_slot + 3600
            builder.add_change_if_needed(self.address)

            # Ký và submit
            signed_tx = builder.build_and_sign([self.payment_skey, self.policy_skey], change_address=self.address)
            logger.debug(f"Transaction CBOR: {signed_tx.to_cbor()}")
            tx_id = self.context.submit_tx(signed_tx.to_cbor())

            # Lưu policy script
            os.makedirs("data/policies", exist_ok=True)
            with open(f"data/policies/{policy_id}.policy", "w") as f:
                f.write(policy_script.to_cbor_hex())

            logger.success(f"✅ Minted {len(assets)} NFTs! Tx ID: {tx_id}")
            logger.info(f"🧱 Policy ID: {policy_id}")
            return tx_id

        except Exception as e:
            logger.error(f"❌ Mint multiple NFTs error: {str(e)}")
            return "ERROR"

    def burn_token(
        self,
        policy_id: str,
        token_name: str,
        amount: int = 1
    ) -> str:
        """Burn token hoặc NFT."""
        try:
            self.utxos = self._fetch_utxos()
            policy_path = f"data/policies/{policy_id}.policy"
            if not exists(policy_path):
                raise FileNotFoundError(f"❌ Policy script not found: {policy_path}")

            with open(policy_path, "r") as f:
                policy_script = NativeScript.from_cbor(f.read())

            builder = TransactionBuilder(self.context)
            builder.add_input(self._select_utxo_for_burn(policy_id, token_name, amount))

            # Tạo multi-asset để burn
            asset_name = AssetName(token_name.encode("utf-8"))
            multi_asset = MultiAsset.from_primitive({
                bytes.fromhex(policy_id): {asset_name.payload: -amount}
            })

            builder.mint = multi_asset
            builder.native_scripts = [policy_script]
            builder.required_signers = [self.policy_vkey.hash()]
            builder.ttl = self.context.last_block_slot + 3600
            builder.add_change_if_needed(self.address)

            # Ký và submit
            signed_tx = builder.build_and_sign([self.payment_skey, self.policy_skey], change_address=self.address)
            logger.debug(f"Burn Transaction CBOR: {signed_tx.to_cbor()}")
            tx_id = self.context.submit_tx(signed_tx.to_cbor())

            logger.warning(f"🔥 Burned {amount} {token_name}. Tx ID: {tx_id}")
            return tx_id

        except Exception as e:
            logger.error(f"❌ Burn error: {str(e)}")
            return "ERROR"

if __name__ == "__main__":
    mint_service = MintService()

    # Mint single NFT
    tx_id_nft = mint_service.mint_token(
        token_name="MyNFT001",
        metadata={
            "name": "Demo NFT",
            "image": "ipfs://bafkreigh2akiscaildc5",
            "description": "Testing NFT Demo"
        },
        is_nft=True
    )
    print(f"NFT Tx: {tx_id_nft}")

    # Mint fungible token
    tx_id_ft = mint_service.mint_token(
        token_name="MyFT001",
        amount=1000,
        metadata={
            "name": "Demo Token",
            "symbol": "DMT",
            "description": "Testing fungible token"
        },
        is_nft=False
    )
    print(f"FT Tx: {tx_id_ft}")

    # Mint multiple NFTs
    types = ["lion", "elephant", "panda", "sloth", "tiger", "wolf"]
    assets = [
        {
            "name": f"CHARACTER{i:04d}",
            "attack": str(random.randint(1, 70)),
            "speed": str(random.randint(1, 70)),
            "defense": str(random.randint(1, 70)),
            "health": str(random.randint(1, 70)),
            "type": random.choice(types),
        } for i in range(1, 6)
    ]
    tx_id_multi_nft = mint_service.mint_multiple_nfts(assets=assets)
    print(f"Multiple NFTs Tx: {tx_id_multi_nft}")

    # Burn NFT (thay YOUR_POLICY_ID bằng policy_id thực từ log/file)
    tx_id_burn_nft = mint_service.burn_token(
        policy_id="YOUR_POLICY_ID",
        token_name="MyNFT001",
        amount=1
    )
    print(f"Burn NFT Tx: {tx_id_burn_nft}")