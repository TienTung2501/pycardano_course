"""
Configuration for CIP-68 Simple Example

This module loads configuration from environment variables.
Copy .env.example to .env and fill in your values.
"""
import os
from pathlib import Path
from pycardano import Network

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"[OK] Loaded configuration from {env_file}")
    else:
        print(f"[WARNING] No .env file found. Using .env.example as template.")
        print(f"  Copy .env.example to .env and configure your settings.")
except ImportError:
    print("[WARNING] python-dotenv not installed. Using default values.")
    print("  Install with: pip install python-dotenv")

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
CONTRACT_DIR = PROJECT_ROOT / "contract"
PLUTUS_FILE = CONTRACT_DIR / os.getenv("PLUTUS_FILE", "plutus.json")

# Network configuration
NETWORK_NAME = os.getenv("NETWORK", "preprod").lower()

# Map network names to PyCardano Network enum
if NETWORK_NAME in ["preview", "preprod", "testnet"]:
    NETWORK = Network.TESTNET
elif NETWORK_NAME == "mainnet":
    NETWORK = Network.MAINNET
else:
    raise ValueError(f"Invalid network: {NETWORK_NAME}. Use 'preview', 'preprod', or 'mainnet'")

# Blockfrost API configuration
if NETWORK_NAME == "preprod":
    BLOCKFROST_PROJECT_ID = os.getenv("BLOCKFROST_PROJECT_ID_PREPROD", "")
elif NETWORK_NAME == "preview":
    BLOCKFROST_PROJECT_ID = os.getenv("BLOCKFROST_PROJECT_ID_PREVIEW", "")
else:  # mainnet
    BLOCKFROST_PROJECT_ID = os.getenv("BLOCKFROST_PROJECT_ID_MAINNET", "")

# Validate Blockfrost API key
if not BLOCKFROST_PROJECT_ID or BLOCKFROST_PROJECT_ID.startswith("your_"):
    print("\n" + "=" * 70)
    print("[WARNING] Blockfrost API key not configured!")
    print("=" * 70)
    print("Please follow these steps:")
    print("1. Copy .env.example to .env")
    print("2. Sign up at https://blockfrost.io/")
    print("3. Create a preprod project")
    print("4. Copy your project ID to .env")
    print("5. Replace BLOCKFROST_PROJECT_ID_PREPROD with your key")
    print("=" * 70)

# Wallet paths (relative to off_chain directory)
ISSUER_MNEMONIC_FILE = Path(os.getenv("ISSUER_MNEMONIC_FILE", "issuer.mnemonic"))
USER_MNEMONIC_FILE = Path(os.getenv("USER_MNEMONIC_FILE", "user.mnemonic"))

# Validator titles (from Aiken blueprint)
MINT_VALIDATOR_TITLE = os.getenv("MINT_VALIDATOR_TITLE", "mint_policy.mint")
STORE_VALIDATOR_TITLE = os.getenv("STORE_VALIDATOR_TITLE", "store_validator.spend")

# CIP-68 Labels (4-byte big-endian)
LABEL_100 = int(os.getenv("LABEL_100", "0x00000064"), 16)  # Reference token (100)
LABEL_222 = int(os.getenv("LABEL_222", "0x000000de"), 16)  # User token (222)

# Token name configuration
TOKEN_NAME_LENGTH = int(os.getenv("TOKEN_NAME_LENGTH", "32"))
LABEL_LENGTH = int(os.getenv("LABEL_LENGTH", "4"))
ASSET_NAME_LENGTH = int(os.getenv("ASSET_NAME_LENGTH", "28"))

# Optional: Advanced configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
TX_TIMEOUT = int(os.getenv("TX_TIMEOUT", "300"))
MIN_ADA_OUTPUT = int(os.getenv("MIN_ADA_OUTPUT", "2000000"))

# Validation
assert TOKEN_NAME_LENGTH == LABEL_LENGTH + ASSET_NAME_LENGTH, \
    f"Invalid token name length: {TOKEN_NAME_LENGTH} != {LABEL_LENGTH} + {ASSET_NAME_LENGTH}"

# Display configuration summary
if os.getenv("DEBUG_CONFIG"):
    print("\n" + "=" * 70)
    print("Configuration Summary")
    print("=" * 70)
    print(f"Network: {NETWORK_NAME} -> {NETWORK}")
    print(f"Blockfrost API: {'[OK] Configured' if BLOCKFROST_PROJECT_ID and not BLOCKFROST_PROJECT_ID.startswith('your_') else '[X] Not configured'}")
    print(f"Plutus file: {PLUTUS_FILE}")
    print(f"Issuer wallet: {ISSUER_MNEMONIC_FILE}")
    print(f"User wallet: {USER_MNEMONIC_FILE}")
    print(f"CIP-68 Labels: Ref={hex(LABEL_100)}, User={hex(LABEL_222)}")
    print("=" * 70 + "\n")
