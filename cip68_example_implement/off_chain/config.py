"""
Configuration cho CIP-68 Example
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from pycardano import Network, BlockFrostChainContext

# Load environment variables
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent
OFF_CHAIN_DIR = PROJECT_ROOT / "wallets"  # Mnemonics stored in wallets/ folder
CONTRACTS_DIR = PROJECT_ROOT.parent / "contracts"
PLUTUS_FILE = CONTRACTS_DIR / "plutus.json"

# Network configuration
NETWORK_NAME = os.getenv("NETWORK", "preview")  # preview, preprod, mainnet
BLOCKFROST_PROJECT_ID = os.getenv("BLOCKFROST_PROJECT_ID", "")

# Map network name to PyCardano Network enum
if NETWORK_NAME == "mainnet":
    NETWORK = Network.MAINNET
else:
    NETWORK = Network.TESTNET

# Blockfrost base URL
if NETWORK_NAME == "mainnet":
    BLOCKFROST_URL = "https://cardano-mainnet.blockfrost.io/api"
elif NETWORK_NAME == "preprod":
    BLOCKFROST_URL = "https://cardano-preprod.blockfrost.io/api"
else:  # preview
    BLOCKFROST_URL = "https://cardano-preview.blockfrost.io/api"

# Create chain context
context = BlockFrostChainContext(
    project_id=BLOCKFROST_PROJECT_ID,
    base_url=BLOCKFROST_URL,
    network=NETWORK
)

# Wallet files
WALLET_DIR = PROJECT_ROOT / "wallets"
WALLET_DIR.mkdir(exist_ok=True)

ISSUER_MNEMONIC_FILE = WALLET_DIR / "issuer.mnemonic"
USER_MNEMONIC_FILE = WALLET_DIR / "user.mnemonic"

# Policy keys (cho native script)
POLICY_DIR = PROJECT_ROOT / "policy"
POLICY_DIR.mkdir(exist_ok=True)

POLICY_SKEY_FILE = POLICY_DIR / "policy.skey"
POLICY_VKEY_FILE = POLICY_DIR / "policy.vkey"

# CIP-68 Labels
LABEL_100 = 100  # Reference token
LABEL_222 = 222  # User token

# Validator titles (trong plutus.json)
UPDATE_VALIDATOR_TITLE = "update_metadata.update_metadata.spend"

# Min ADA amounts
MIN_ADA_OUTPUT = 2_000_000  # 2 ADA
MIN_ADA_SCRIPT_OUTPUT = 3_000_000  # 3 ADA (có datum lớn hơn)

# TTL offset (seconds)
TTL_OFFSET = 1000

print(f"[OK] Loaded configuration for {NETWORK_NAME} network")
