#!/usr/bin/env python3
"""
Verify wallet addresses match mnemonic files
"""
from utils.helpers import generate_or_load_wallet
from config import context

print("Loading wallets from mnemonic files...")
print("=" * 70)

# Load issuer
issuer_sk, issuer_vk, issuer_hash, issuer_addr = generate_or_load_wallet('issuer.mnemonic')
print(f"\nIssuer Address: {issuer_addr}")

# Load user  
user_sk, user_vk, user_hash, user_addr = generate_or_load_wallet('user.mnemonic')
print(f"User Address: {user_addr}")

print("\n" + "=" * 70)
print("Checking balances on blockchain...")
print("=" * 70)

# Check issuer balance
try:
    issuer_utxos = context.utxos(issuer_addr)
    issuer_balance = sum([u.output.amount.coin for u in issuer_utxos])
    print(f"\nIssuer: {issuer_balance / 1_000_000:.6f} ADA ({len(issuer_utxos)} UTxOs)")
    
    if len(issuer_utxos) == 0:
        print("  ⚠️  No UTxOs found! Wallet needs to be funded.")
        print(f"  Fund this address: {issuer_addr}")
    else:
        for i, utxo in enumerate(issuer_utxos[:5]):
            print(f"  UTxO {i+1}: {utxo.output.amount.coin / 1_000_000:.6f} ADA")
except Exception as e:
    print(f"\n❌ Error checking issuer: {e}")

# Check user balance
try:
    user_utxos = context.utxos(user_addr)
    user_balance = sum([u.output.amount.coin for u in user_utxos])
    print(f"\nUser: {user_balance / 1_000_000:.6f} ADA ({len(user_utxos)} UTxOs)")
    
    if len(user_utxos) == 0:
        print("  ⚠️  No UTxOs found! Wallet needs to be funded.")
        print(f"  Fund this address: {user_addr}")
    else:
        for i, utxo in enumerate(user_utxos[:5]):
            print(f"  UTxO {i+1}: {utxo.output.amount.coin / 1_000_000:.6f} ADA")
except Exception as e:
    print(f"\n❌ Error checking user: {e}")

print("\n" + "=" * 70)
