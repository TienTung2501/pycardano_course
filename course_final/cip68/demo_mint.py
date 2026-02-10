"""
Demo Mint CIP-68 Token
======================
Script để mint một CIP-68 Dynamic NFT.
"""
import os
import sys
import time
import json

from dotenv import load_dotenv

from offchain.cip68_operations import (
    get_chain_context,
    get_wallet_from_seed,
    mint_cip68_token,
)

load_dotenv()
# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("=" * 60)
    print("DEMO: Mint CIP-68 Dynamic NFT (Simplified)")
    print("=" * 60)
    # Load wallet
    seed_phrase = os.getenv("SEED_PHRASE")

    if not seed_phrase:
        print("ERROR: SEED_PHRASE không tìm thấy trong .env")
        return
    payment_skey, payment_vkey, stake_skey, stake_vkey, address = get_wallet_from_seed(seed_phrase)

    print(f"\nWallet address: {address}")
    # Get chain context
    context = get_chain_context()

    # Check balance
    utxos = context.utxos(address)
    total_ada = sum(utxo.output.amount.coin for utxo in utxos) / 1_000_000
    print(f"Balance: {total_ada:.2f} ADA")

    if total_ada < 10:
        print("ERROR: Không đủ ADA để mint (cần ít nhất 10 ADA)")
        return
    # Token info - sử dụng timestamp để tạo tên unique
    timestamp = int(time.time())
    token_name = f"DemoNFT_{timestamp}"
    description = f"Demo CIP-68 NFT created at {timestamp}"

    print(f"\nMinting token:")
    print(f"  Name: {token_name}")
    print(f"  Description: {description}")
    print("-" * 60)

    try:
        result = mint_cip68_token(
            context=context,
            payment_skey=payment_skey,
            payment_vkey=payment_vkey,
            owner_address=address,
            token_name=token_name,
            description=description,
        )
        print("\n" + "=" * 60)
        print("MINT THÀNH CÔNG!")
        print(f"Transaction Hash: {result['tx_hash']}")
        print(f"Policy ID: {result['policy_id']}")
        print(f"Token Name: {result['token_name']}")
        print(f"Store Address: {result['store_address']}")
        print("=" * 60)
        
        print(f"\nXem transaction tại:")
        print(f"https://preprod.cardanoscan.io/transaction/{result['tx_hash']}")

         # Save token info for later use
        token_info = {
            "tx_hash": result['tx_hash'],
            "policy_id": result['policy_id'],
            "token_name": token_name,
            "description": description,
            "timestamp": timestamp,
        }
        with open(f"minted_{token_name}.json", "w") as f:
            json.dump(token_info, f, indent=2)
        print(f"\nToken info saved to: minted_{token_name}.json")
    except Exception as e:
        print(f"\nLỗi: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()