#!/usr/bin/env python3
"""Check wallet balances"""
from config import context

# Addresses from mint_nft.py output
issuer_addr = "addr_test1qp0w79aen4gek54u5hmq4wpzvwla4as4w0zjtqneu2vdkrh5hkxs54ravf80yf8t4y4a8st6mk54y6lschdjq0d6l9mqku2nua"
user_addr = "addr_test1qqdpq8qm24gh27mkjkrmpc5nkdnm8lexejxsqqk7t6lschhgjmsespyacxfeugclune4x5rsc50sx6xel0enhct6x2rqspx8uf"

print("Checking wallet balances on Preview testnet...")
print("=" * 70)

# Check issuer
print(f"\nIssuer: {issuer_addr}")
try:
    issuer_utxos = context.utxos(issuer_addr)
    issuer_balance = sum([u.output.amount.coin for u in issuer_utxos])
    print(f"  Balance: {issuer_balance / 1_000_000:.6f} ADA")
    print(f"  UTxOs: {len(issuer_utxos)}")
    if len(issuer_utxos) > 0:
        for i, utxo in enumerate(issuer_utxos[:3]):  # Show first 3
            print(f"    UTxO {i+1}: {utxo.output.amount.coin / 1_000_000:.6f} ADA")
except Exception as e:
    print(f"  Error: {e}")

# Check user
print(f"\nUser: {user_addr}")
try:
    user_utxos = context.utxos(user_addr)
    user_balance = sum([u.output.amount.coin for u in user_utxos])
    print(f"  Balance: {user_balance / 1_000_000:.6f} ADA")
    print(f"  UTxOs: {len(user_utxos)}")
    if len(user_utxos) > 0:
        for i, utxo in enumerate(user_utxos[:3]):  # Show first 3
            print(f"    UTxO {i+1}: {utxo.output.amount.coin / 1_000_000:.6f} ADA")
except Exception as e:
    print(f"  Error: {e}")

print("\n" + "=" * 70)
