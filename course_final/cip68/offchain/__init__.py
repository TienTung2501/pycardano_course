"""
CIP-68 Offchain Package
=======================
Package chứa các module để tương tác với CIP-68 smart contract.

SIMPLIFIED VERSION: Non-parameterized contracts
"""
from .cip68_utils import (
    CIP68_REFERENCE_PREFIX,
    CIP68_USER_PREFIX,
    MintToken,
    BurnToken,
    UpdateMetadata,
    BurnReference,
    CIP68Datum,
    create_cip68_asset_names,
    create_cip68_metadata,
    create_cip68_datum,
    get_policy_id,
    get_script_address,
    load_mint_script,
    load_store_script,
    extract_owner_from_datum,
)
from .cip68_operations import (
    get_chain_context,
    get_wallet_from_seed,
    get_network,
    get_scripts,
    mint_cip68_token,
    update_metadata,
    burn_cip68_token,
    list_all_tokens,
)

__all__ = [
    # Utils
    'CIP68_REFERENCE_PREFIX',
    'CIP68_USER_PREFIX',
    'MintToken',
    'BurnToken',
    'UpdateMetadata',
    'BurnReference',
    'CIP68Datum',
    'create_cip68_asset_names',
    'create_cip68_metadata',
    'create_cip68_datum',
    'get_policy_id',
    'get_script_address',
    'get_fixed_policy_id',
    'get_fixed_store_address',
    'load_mint_script',
    'load_store_script',
    'extract_owner_from_datum',
    # Operations
    'get_chain_context',
    'get_wallet_from_seed',
    'get_network',
    'get_scripts',
    'mint_cip68_token',
    'update_metadata',
    'burn_cip68_token',
    'list_all_tokens',
]
