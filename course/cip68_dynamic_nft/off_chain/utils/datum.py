# filepath: d:\Code\cip68\cip68_v0\cip68-nfts\off-chain-pycardano\utils\datum.py
from dataclasses import dataclass
from typing import Dict, Any, Optional

from pycardano.plutus import PlutusData, ConstrPlutusData, PlutusV2Script
from pycardano.serialization import RawCBOR
import cbor2

# MetaDatum = Constr 0 [metadata(map bytes->data), version(int), extra(bytes)]
def metadatum_from_json(meta_json: Dict[str, Any], version: int = 1, extra: Optional[bytes] = None) -> RawCBOR:
    # Map JSON -> Plutus data map: khóa/giá trị đều encode như metadatum (đơn giản hóa: dump trực tiếp JSON sang CBOR)
    # Để tương thích on-chain, TS đang đưa JSON vào Data.fromJson rồi wrap Constr(0, [...]).
    # Tương đương ở đây ta encode metadata (đã là data-like) bằng cbor2, sau đó wrap bằng Constr 0.
    if extra is None:
        extra = b""

    # metadata phần này tùy schema; ở đây giả định meta_json là cấu trúc Metadatum hợp lệ khi được CBOR hóa
    metadata_cbor = cbor2.dumps(meta_json)
    datum_cbor = cbor2.dumps(
        cbor2.CBORTag(121, [  # 121 ~ ConstrPlutusData tag base (alternative encoding)
            0,  # constructor index 0
            [metadata_cbor, version, extra]  # fields
        ])
    )
    return RawCBOR(datum_cbor)