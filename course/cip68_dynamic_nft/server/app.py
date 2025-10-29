import os
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Make sure we can import off_chain utilities from this repo layout
import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[3]  # .../pycardano_course
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from course.cip68_dynamic_nft.server.services.cip68_service import (
    get_addresses,
    get_store_summary,
    list_cip68_nfts,
    # old direct-submit endpoints (kept for admin/issuer flows)
    mint_dynamic_nft,
    update_dynamic_nft,
    remove_dynamic_nft,
    burn_dynamic_nft,
    # new build/finalize flows for wallet co-sign
    build_mint_tx,
    finalize_with_user_witness,
    build_burn_tx,
)


class MintBody(BaseModel):
    metadata: Dict[str, Any] = Field(default_factory=dict)
    issuer_index: int = 0
    user_index: int = 1
    user_address: Optional[str] = None  # when provided, prefer wallet address over mnemonic-derived


class UpdateBody(BaseModel):
    metadata: Dict[str, Any] = Field(default_factory=dict)
    issuer_index: int = 0


class RemoveBody(BaseModel):
    issuer_index: int = 0
    user_index: int = 1


class BurnBody(BaseModel):
    issuer_index: int = 0
    user_index: int = 1
    user_address: Optional[str] = None


class BuildMintBody(BaseModel):
    user_address: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BuildBurnBody(BaseModel):
    user_address: str


class FinalizeBody(BaseModel):
    tx_cbor: str
    user_witness_cbor: str


app = FastAPI(title="CIP-68 Dynamic NFT API")

# CORS setup
frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin, "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/addresses")
def addresses():
    try:
        issuer, user = get_addresses()
        return {"issuer": issuer, "user": user}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/store")
def store_summary():
    try:
        return get_store_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/nfts")
def list_nfts(address: str = Query(..., description="User bech32 address")):
    try:
        return list_cip68_nfts(address)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mint")
def mint(body: MintBody):
    try:
        # legacy direct-submit (issuer + user from mnemonic) OR wallet-based build/finalize
        if body.user_address:
            tx_cbor, details = build_mint_tx(body.user_address, body.metadata)
            return {"tx_cbor": tx_cbor, "details": details}
        else:
            tx_id, token_names = mint_dynamic_nft(body.metadata, body.issuer_index, body.user_index)
            return {"tx_id": tx_id, "token_names": token_names}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mint/prepare")
def mint_prepare(body: BuildMintBody):
    try:
        tx_cbor, details = build_mint_tx(body.user_address, body.metadata)
        return {"unsigned_tx_cbor": tx_cbor, "details": details}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/update")
def update(body: UpdateBody):
    try:
        tx_id = update_dynamic_nft(body.metadata, body.issuer_index)
        return {"tx_id": tx_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/remove")
def remove(body: RemoveBody):
    try:
        tx_id, consumed = remove_dynamic_nft(body.issuer_index, body.user_index)
        return {"tx_id": tx_id, "consumed": consumed}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/burn")
def burn(body: BurnBody):
    try:
        if body.user_address:
            tx_cbor, details = build_burn_tx(body.user_address)
            return {"tx_cbor": tx_cbor, "details": details}
        else:
            tx_id = burn_dynamic_nft(body.issuer_index, body.user_index)
            return {"tx_id": tx_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/burn/prepare")
def burn_prepare(body: BuildBurnBody):
    try:
        tx_cbor, details = build_burn_tx(body.user_address)
        return {"unsigned_tx_cbor": tx_cbor, "details": details}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tx/finalize")
def finalize_tx(body: FinalizeBody):
    try:
        tx_id = finalize_with_user_witness(body.tx_cbor, body.user_witness_cbor)
        return {"tx_id": tx_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("course.cip68_dynamic_nft.server.app:app", host="0.0.0.0", port=8000, reload=True)
