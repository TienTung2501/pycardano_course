# CIP-68 Dynamic NFT — Backend + Frontend

This module includes a minimal FastAPI backend and a Next.js frontend for interacting with Aiken-based CIP‑68 contracts. It follows a wallet-driven, two-party signing model:

- Frontend: user connects a CIP‑30 wallet (Nami/Eternl/Flint/Gero) and signs transactions client-side.
- Backend (pycardano): builds unsigned transactions with scripts/redeemers, merges the user witness with issuer’s signature, and submits via Blockfrost.

---

## Backend (FastAPI)

Location: `course/cip68_dynamic_nft/server`

- Dependencies: see `requirements.txt` (e.g., `fastapi`, `uvicorn`).
- Uses off-chain utilities in `off_chain/utils/*` and config in `off_chain/common/config.py`.
- Reads `MNEMONIC` and Blockfrost settings from the repo root `.env`.

Endpoints (wallet-driven flow):
- `GET /health` — health check.
- `GET /nfts?address=<bech32>` — list user CIP‑68 items (includes store datum and UTxO refs).
- `POST /mint/prepare` — body: `{ user_address: string, metadata: object }` → returns `{ unsigned_tx_cbor, details }`.
- `POST /burn/prepare` — body: `{ user_address: string }` → returns `{ unsigned_tx_cbor, details }`.
- `POST /tx/finalize` — body: `{ tx_cbor: string, user_witness_cbor: string }` → submits and returns `{ tx_id }`.

Legacy (issuer-direct) endpoints kept for teaching/admin:
- `GET /addresses` — derived issuer (index 0) and demo user (index 1) addresses.
- `GET /store` — store lock address and UTxO count.
- `POST /mint` — `{ metadata, issuer_index?, user_index?, user_address? }` (if `user_address` is missing, does direct-submit from demo mnemonic).
- `POST /update` — `{ metadata, issuer_index? }` (issuer-only; updates inline datum at store).
- `POST /remove` — `{ issuer_index?, user_index? }` (issuer-only; spends store UTxOs back to user).
- `POST /burn` — `{ issuer_index?, user_index?, user_address? }` (if `user_address` present, returns unsigned build; otherwise direct-submit).

Run (from repo root):

```powershell
# 1) Activate your Python environment

# 2) Install backend deps
pip install -r "course/cip68_dynamic_nft/server/requirements.txt"

# 3) Start API server
python -m uvicorn course.cip68_dynamic_nft.server.app:app --host 0.0.0.0 --port 8000 --reload
```

Notes:
- The root `.env` typically has `BLOCKFROST_NETWORK=testnet` which maps to Blockfrost preview in the off-chain config.
- CORS allows `http://localhost:3000` by default. Override with `FRONTEND_ORIGIN` if needed.
- Security (recommended hardening for production): validate that finalize requests match the prepared tx (hash/nonce binding), verify minted/burned assets and outputs, and never sign arbitrary client-constructed CBOR.

---

## Frontend (Next.js)

Location: `course/cip68_dynamic_nft/frontend`

Quick start:

```powershell
cd "course/cip68_dynamic_nft/frontend"
# Copy env example if needed
Copy-Item .env.local.example .env.local
# Set NEXT_PUBLIC_BACKEND_URL if backend is not on default
# (optional) notepad .env.local

# Install deps and start
npm install
npm run dev
```

Open http://localhost:3000. The UI calls the backend at `NEXT_PUBLIC_BACKEND_URL` (default `http://localhost:8000`).

Pages:
- `/` — course summary and legacy demo actions (issuer-direct flows).
- `/mint` — wallet-driven mint: calls `/mint/prepare`, signs with `wallet.signTx(unsigned_tx_cbor, true)`, then `/tx/finalize`.
- `/nfts` — lists user CIP‑68 items; actions:
	- Update (issuer-only, server signs and submits)
	- Remove (issuer-only, server signs and submits)
	- Burn (wallet-driven; `/burn/prepare` → sign → `/tx/finalize`).

Where the browser wallet signs:
- In `pages/mint.tsx` and `pages/nfts.tsx`, the call is `wallet.signTx(unsigned_tx_cbor, true)` — the extension opens a signing popup.

---

## How it works (CIP‑68 specifics)

- Token labels: 100 (reference, at store with inline datum) and 222 (user), with a shared 28‑byte suffix derived from a user UTxO (requires `input.index < 256`).
- Mint (Redeemer 0 on policy): mints both 100/222; user token goes to user address; ref token goes to store with inline datum (metadata JSON‑like).
- Update (Redeemer 0 on store): spends store UTxO and rewrites the inline datum; issuer signs.
- Remove (Redeemer 1 on store): spends store UTxO and moves value out; typically paired with burn.
- Burn (Redeemer 1 on policy): burns both 100/222; transaction also spends the matching store UTxO via Redeemer 1 (Remove) to keep value conservation; requires issuer + user signatures.

---

## Troubleshooting

- Backend imports unresolved (FastAPI/Uvicorn): install deps with the pip command above and restart the Python environment.
- Wallet not detected: ensure a CIP‑30 wallet (Nami/Eternl/Flint/Gero) is installed and enabled on the correct network.
- Not enough tADA / no UTxOs: fund your wallet on the appropriate test network (preview/preprod) matching your `.env`.
- Burn fails with value errors: ensure the store UTxO for the same suffix exists; the backend now includes it automatically.

If you need the UI to choose specific UTxOs, we can add a `GET /utxos?address=...` endpoint and surface selection on the pages.
