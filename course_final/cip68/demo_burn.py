#!/usr/bin/env python3
"""
Demo Burn CIP-68 Token
======================
Script để burn một CIP-68 Dynamic NFT.

SIMPLIFIED VERSION: Non-parameterized contracts
"""
import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from offchain.cip68_operations import (
    get_chain_context,
    get_scripts,
    get_wallet_from_seed,
    burn_cip68_token,
    list_all_tokens,
)

load_dotenv()

def main():
    print("=" * 60)
    print("DEMO: Burn CIP-68 Token (Simplified)")
    print("=" * 60)

     # Load wallet
    seed_phrase = os.getenv("SEED_PHRASE")
    if not seed_phrase:
        print("ERROR: SEED_PHRASE không tìm thấy trong .env")
        return
    payment_skey, payment_vkey, stake_skey, stake_vkey, address = get_wallet_from_seed(seed_phrase)
    mint_script, store_script, policy_id, store_address = get_scripts()
    print(f"\nWallet address: {address}")
    POLICY_ID ="9127f9f55834f6c71fba24ae5712e381cfeb54aabce7072ecfb4739f"  # Thay thế bằng POLICY_ID thực tế sau khi có nft để burn
    print(f"Policy ID: {POLICY_ID}")
     # Get chain context
    context = get_chain_context()

     # List tokens owned by this address
    print("\nTìm tokens bạn sở hữu...")
    tokens = list_all_tokens(context, address,store_address)

    if not tokens:
        print("Không tìm thấy token nào! Hãy chạy demo_mint.py trước.")
        return
    print(f"\nTìm thấy {len(tokens)} token(s):")
    for i, token in enumerate(tokens):
        print(f"  {i + 1}. {token['token_name']} (version {token.get('version', '?')})")

     # Select token to burn
    if len(tokens) == 1:
        selected = tokens[0]
        confirm = input(f"\nBạn có chắc muốn burn '{selected['token_name']}'? (y/n): ")
        if confirm.lower() != 'y':
            print("Đã hủy.")
            return
    else:
        choice = input("\nChọn token để burn (số): ").strip()
        try:
            idx = int(choice) - 1
            selected = tokens[idx]
        except (ValueError, IndexError):
            print("Lựa chọn không hợp lệ!")
            return
    token_name = selected['token_name']
    print(f"\nBurning token: {token_name}")
    print("-" * 60)

    try: 
        result = burn_cip68_token(
            context=context,
            payment_skey=payment_skey,
            payment_vkey=payment_vkey,
            owner_address=address,
            token_name=token_name,
        )
        print("\n" + "=" * 60)
        print("BURN THÀNH CÔNG!")
        print(f"Transaction Hash: {result['tx_hash']}")
        print(f"\nXem tại: https://preprod.cardanoscan.io/transaction/{result['tx_hash']}")
        print("=" * 60)
    except Exception as e:
        print(f"\nLỗi: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
