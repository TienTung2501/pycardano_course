#!/usr/bin/env python3
"""
CIP-68 NFT Manager - All-in-One Tool

This is the main entry point for all CIP-68 NFT operations.

Usage:
    python nft_manager.py mint [--debug] [--no-submit]
    python nft_manager.py update <policy_id> <asset_name> [--debug] [--no-submit]
    python nft_manager.py burn <policy_id> <asset_name> [--debug] [--no-submit]
    python nft_manager.py query <policy_id> <asset_name>
    python nft_manager.py list
"""
import argparse
import sys
from pathlib import Path

# Import all operation modules
import mint_nft
import update_nft
import burn_nft
import query_nft


def list_nfts():
    """List all NFTs minted by this wallet."""
    print("=" * 70)
    print("Listing NFTs")
    print("=" * 70)
    print("\nℹ️  Feature coming soon!")
    print("For now, use query_nft.py with specific policy ID and asset name.")
    print("\nOr check your wallet address on Cardano explorer:")
    print("https://preprod.cardanoscan.io/")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="CIP-68 NFT Manager - Mint, Update, Burn, and Query NFTs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Mint a new NFT
  python nft_manager.py mint

  # Query NFT info
  python nft_manager.py query 7212c8f7... fa162d...

  # Update NFT metadata
  python nft_manager.py update 7212c8f7... fa162d...

  # Burn NFT
  python nft_manager.py burn 7212c8f7... fa162d...

  # List all NFTs
  python nft_manager.py list
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Mint command
    mint_parser = subparsers.add_parser("mint", help="Mint a new CIP-68 NFT")
    mint_parser.add_argument("--debug", action="store_true", help="Enable debug output")
    mint_parser.add_argument("--no-submit", action="store_true", help="Build but don't submit")
    
    # Update command
    update_parser = subparsers.add_parser("update", help="Update NFT metadata")
    update_parser.add_argument("policy_id", help="Policy ID (hex)")
    update_parser.add_argument("asset_name", help="28-byte asset name suffix (hex)")
    update_parser.add_argument("--debug", action="store_true", help="Enable debug output")
    update_parser.add_argument("--no-submit", action="store_true", help="Build but don't submit")
    
    # Burn command
    burn_parser = subparsers.add_parser("burn", help="Burn NFT (both tokens)")
    burn_parser.add_argument("policy_id", help="Policy ID (hex)")
    burn_parser.add_argument("asset_name", help="28-byte asset name suffix (hex)")
    burn_parser.add_argument("--debug", action="store_true", help="Enable debug output")
    burn_parser.add_argument("--no-submit", action="store_true", help="Build but don't submit")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Query NFT information")
    query_parser.add_argument("policy_id", help="Policy ID (hex)")
    query_parser.add_argument("asset_name", help="28-byte asset name suffix (hex)")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all NFTs")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Route to appropriate handler
    if args.command == "mint":
        sys.argv = ["mint_nft.py"]
        if args.debug:
            sys.argv.append("--debug")
        if args.no_submit:
            sys.argv.append("--no-submit")
        mint_nft.main()
        
    elif args.command == "update":
        sys.argv = ["update_nft.py", args.policy_id, args.asset_name]
        if args.debug:
            sys.argv.append("--debug")
        if args.no_submit:
            sys.argv.append("--no-submit")
        update_nft.main()
        
    elif args.command == "burn":
        sys.argv = ["burn_nft.py", args.policy_id, args.asset_name]
        if args.debug:
            sys.argv.append("--debug")
        if args.no_submit:
            sys.argv.append("--no-submit")
        burn_nft.main()
        
    elif args.command == "query":
        sys.argv = ["query_nft.py", args.policy_id, args.asset_name]
        query_nft.main()
        
    elif args.command == "list":
        list_nfts()


if __name__ == "__main__":
    main()
