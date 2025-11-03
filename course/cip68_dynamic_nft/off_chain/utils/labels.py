def build_token_name(label: int, suffix: bytes) -> bytes:
    """
    Build CIP-68 token name: [label_4bytes_big_endian, suffix_28bytes]
    
    The label is encoded as a 4-byte big-endian integer according to CIP-68:
    - Label 100 (ref): 0x00000064 (4 bytes)
    - Label 222 (user): 0x000000de (4 bytes)
    """
    if not (0 <= label <= 0xFFFFFFFF):
        raise ValueError("Label must fit in 4 bytes (0-4294967295)")
    if len(suffix) != 28:
        raise ValueError("Suffix must be 28 bytes")
    # Encode label as 4-byte big-endian integer
    label_bytes = label.to_bytes(4, byteorder='big')
    return label_bytes + suffix
