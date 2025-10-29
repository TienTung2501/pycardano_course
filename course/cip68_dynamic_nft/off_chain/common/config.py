from pathlib import Path
import os

# Gốc module CIP-68 trong repo hiện tại: .../course/cip68_dynamic_nft
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Ưu tiên contract/plutus.json; fallback plutus.json ở gốc module
_PLUTUS_CANDIDATES = [
    PROJECT_ROOT / "contract" / "plutus.json",
    PROJECT_ROOT / "plutus.json",
]
PLUTUS_JSON_PATH = next((p for p in _PLUTUS_CANDIDATES if p.exists()), _PLUTUS_CANDIDATES[0])

# Blockfrost (hỗ trợ: testnet|preview|preprod|mainnet)
_BLOCKFROST_API_URLS = {
    "PREVIEW": "https://cardano-preview.blockfrost.io/api/v0",
    "PREPROD": "https://cardano-preprod.blockfrost.io/api/v0",
    "MAINNET": "https://cardano-mainnet.blockfrost.io/api/v0",
}
_raw_net = os.getenv("BLOCKFROST_NETWORK", "preview").upper()
# map 'TESTNET' -> PREVIEW cho phù hợp .env hiện tại
if _raw_net in ("TESTNET", "TEST"):
    BLOCKFROST_NETWORK = "PREVIEW"
elif _raw_net in ("PREVIEW", "PREPROD", "MAINNET"):
    BLOCKFROST_NETWORK = _raw_net
else:
    raise ValueError(f"Unsupported BLOCKFROST_NETWORK: {_raw_net}. Use preview|preprod|mainnet|testnet")

BLOCKFROST_BASE_URL = _BLOCKFROST_API_URLS[BLOCKFROST_NETWORK]
# Ưu tiên BLOCKFROST_PROJECT_ID; fallback BLOCKFROST_API_KEY
BLOCKFROST_PROJECT_ID = os.getenv("BLOCKFROST_PROJECT_ID") or os.getenv("BLOCKFROST_API_KEY") or ""

# CIP-68 labels (CIP-67, 4-byte big endian)
REFERENCE_TOKEN_LABEL = 100
NON_FUNGIBLE_TOKEN_LABEL = 222

# TTL (slots) có thể dùng khi build tx
TX_TTL_SLOTS = int(os.getenv("CIP68_TX_TTL_SLOTS", "3600"))

# ADA ước lượng tối thiểu (off-chain vẫn nên tính min-ADA chuẩn từ context)
MIN_ADA_REF = int(os.getenv("CIP68_MIN_ADA_REF", "3000000"))
MIN_ADA_USER = int(os.getenv("CIP68_MIN_ADA_USER", "3000000"))

# MNEMONIC từ .env để off-chain wallet dùng
MNEMONIC = os.getenv("MNEMONIC", "")