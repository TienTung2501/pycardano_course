from pycardano import RawCBOR, PlutusData
from cbor2 import CBORTag
import cbor2
from dataclasses import dataclass
from typing import Any, Mapping, Optional


@dataclass
class StoreDatum(PlutusData):
    """
    CIP-68 store datum shape:
    Constr(0, [ {map}, version, extra ])
    """
    CONSTR_ID = 0
    metadata: dict
    version: int
    extra: Optional[bytes] = None


# IndefiniteList có thể vắng ở một số phiên bản; fallback no-op
try:
    from pycardano.serialization import IndefiniteList  # type: ignore
except Exception:
    class IndefiniteList(list):  # type: ignore
        pass


def _to_cbor_safe(obj: Any) -> Any:
    """
    Chuẩn hóa đệ quy về các kiểu cbor2 hỗ trợ:
    - list/tuple/IndefiniteList -> list
    - dict -> dict với khóa bytes (utf-8) và value đã chuẩn hóa
    - str -> bytes (utf-8)
    - bytes/bytearray/int/bool -> giữ nguyên/ép về bytes
    - loại khác -> str(...).encode('utf-8')
    """
    if isinstance(obj, IndefiniteList):
        return [_to_cbor_safe(x) for x in list(obj)]
    if isinstance(obj, (list, tuple)):
        return [_to_cbor_safe(x) for x in obj]
    if isinstance(obj, Mapping):
        out = {}
        for k, v in obj.items():
            if isinstance(k, (bytes, bytearray)):
                kb = bytes(k)
            else:
                kb = str(k).encode("utf-8")  # CIP-68: khóa là bytes
            out[kb] = _to_cbor_safe(v)
        return out
    if isinstance(obj, str):
        return obj.encode("utf-8")
    if isinstance(obj, (bytes, bytearray)):
        return bytes(obj)
    if isinstance(obj, (int, bool)):
        return obj
    return str(obj).encode("utf-8")


def metadatum_from_json(data: dict, version: int = 1, extra: Optional[bytes] = None) -> RawCBOR:
    """
    Tạo inline datum theo CIP‑68:
      Constr 0 [ metadata_map(bytes-keyed), version(int), extra(bytes) ]
    Trả về RawCBOR để gán vào TransactionOutput(..., datum=...).
    """
    if not isinstance(data, dict):
        raise ValueError("Top-level metadata phải là dict")

    meta_map = _to_cbor_safe(data)
    if not isinstance(meta_map, dict):
        raise ValueError("Metadata map không hợp lệ sau khi chuẩn hóa")

    extra_bytes = b"" if extra is None else bytes(extra)
    tagged = CBORTag(121, [meta_map, int(version), extra_bytes])  # 121 = Plutus Constr(0,...)
    return RawCBOR(cbor2.dumps(tagged, canonical=True))