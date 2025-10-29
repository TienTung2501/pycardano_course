# filepath: d:\Code\cip68\cip68_v0\cip68-nfts\off-chain-pycardano\README.md
# Off-chain (pycardano)

- Env:
  - export BLOCKFROST_API_KEY=...
- Generate wallets (Python-only):
  - python -m off_chain_pycardano.wallet.generate_credentials
- Mint:
  - python -m off_chain_pycardano.mint_nft
- Update:
  - python -m off_chain_pycardano.update_nft
- Remove:
  - python -m off_chain_pycardano.remove_nft
- Burn:
  - python -m off_chain_pycardano.burn_nft

Lưu ý:
- Các script đọc applied validators từ cip68-nfts/applied-validators, tương tự cách TS sử dụng.
- MetaDatum inline tạo từ nft-metadata.json và wrap theo Constr(0, [...]).