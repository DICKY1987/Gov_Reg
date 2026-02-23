"""GEU ID generation scheme.

FILE_ID: 0199900004226012489
DOC_ID: DOC-CORE-GEU-GOVERNANCE-ID-SCHEME-0199900004226012489
"""
from __future__ import annotations

import zlib
from typing import Dict

def _anchor_hash8(anchor_file_id: str) -> str:
    # Deterministic numeric hash of the anchor file_id, rendered as 8 digits.
    h = zlib.crc32(anchor_file_id.encode("utf-8")) % 100_000_000
    return f"{h:08d}"

def make_geu_id(*, geu_type: str, anchor_file_id: str, type_codes: Dict[str, str], seq: int) -> str:
    if geu_type not in type_codes:
        raise ValueError(f"Unknown geu_type: {geu_type}")
    if seq < 0 or seq > 9999:
        raise ValueError("seq must be 0..9999")
    prefix = "99"
    type_code = type_codes[geu_type]
    ah = _anchor_hash8(anchor_file_id)
    return f"{prefix}{type_code}{ah}{seq:04d}"
