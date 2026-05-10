"""
Helpers de codificação Base64.

Funções:
- encode_b64(data): bytes -> string Base64.
- decode_b64(data): string Base64 -> bytes.
"""

import base64

def encode_b64(data: bytes) -> str:
    return base64.b64encode(data).decode('utf-8')

def decode_b64(data: str) -> bytes:
    return base64.b64decode(data.encode('utf-8'))
